# ============================================================
# OJ判题平台 - Flask Web 应用主程序
# ============================================================
import os
import json
import subprocess
import hashlib
import tempfile
import shutil
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
import pymysql
import pymysql.cursors

app = Flask(__name__)
app.secret_key = 'oj_platform_secret_key_2026'

# ============================================================
from datetime import datetime as dt_now
app.jinja_env.globals['now'] = dt_now.now

# 添加自定义的 fromjson 过滤器，用于在前端解析判题结果
@app.template_filter('fromjson')
def fromjson_filter(s):
    try:
        return json.loads(s) if s else []
    except:
        return []
        
# ----------------------------
# 数据库配置
# ----------------------------
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'zjy200646',
    'database': 'oj_platform',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

# C++ judge 程序路径
JUDGE_BIN = os.path.join(os.path.dirname(__file__), 'judge', 'judge.exe')
WORK_DIR  = os.path.join(os.path.dirname(__file__), 'judge', 'work')

# ============================================================
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'mp4', 'webm', 'avi', 'mov'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    return pymysql.connect(**DB_CONFIG)


# ----------------------------
# 登录验证装饰器
# ----------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('需要管理员权限', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ----------------------------
# 密码哈希
# ----------------------------
def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


# ============================================================
# 路由：登录 / 登出
# ============================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('login.html')

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    'SELECT id, username, role, nickname FROM users '
                    'WHERE username=%s AND password=SHA2(%s,256)',
                    (username, password)
                )
                user = cur.fetchone()
        finally:
            db.close()

        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            session['nickname'] = user['nickname'] or user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================================
# 路由：学生注册
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        nickname = request.form.get('nickname', '').strip()

        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('register.html')
        if len(username) < 3 or len(username) > 20:
            flash('用户名长度需在3-20位之间', 'danger')
            return render_template('register.html')
        if not username.isalnum():
            flash('用户名只能包含字母和数字', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('密码长度至少6位', 'danger')
            return render_template('register.html')

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    flash('用户名已存在，请换一个', 'danger')
                    return render_template('register.html')
                cur.execute(
                    'INSERT INTO users (username, password, role, nickname) VALUES (%s, SHA2(%s,256), %s, %s)',
                    (username, password, 'student', nickname or None)
                )
            db.commit()
        finally:
            db.close()

        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ============================================================
# 路由：仪表盘（根据角色跳转）
# ============================================================
@app.route('/dashboard')
@login_required
def dashboard():
    if session['role'] == 'admin':
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute('SELECT COUNT(*) AS cnt FROM problems')
                p_cnt = cur.fetchone()['cnt']
                cur.execute('SELECT COUNT(*) AS cnt FROM submissions')
                s_cnt = cur.fetchone()['cnt']
                cur.execute('SELECT COUNT(*) AS cnt FROM users WHERE role=%s', ('student',))
                u_cnt = cur.fetchone()['cnt']
        finally:
            db.close()
        return render_template('admin/dashboard.html',
                               problem_count=p_cnt,
                               submission_count=s_cnt,
                               student_count=u_cnt)
    else:
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute('SELECT id, title, time_limit, memory_limit, created_at FROM problems ORDER BY id DESC')
                problems = cur.fetchall()
                cur.execute(
                    'SELECT s.id, p.title, s.status, s.score, s.test_total, s.submitted_at '
                    'FROM submissions s JOIN problems p ON s.problem_id=p.id '
                    'WHERE s.user_id=%s ORDER BY s.id DESC LIMIT 20',
                    (session['user_id'],)
                )
                submissions = cur.fetchall()
        finally:
            db.close()
        return render_template("student/dashboard.html",
                               problems=problems,
                               submissions=submissions)

# ============================================================
# 管理员：创建题目
# ============================================================
@app.route('/admin/problems/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_problem():
    if request.method == 'POST':
        title         = request.form.get('title', '').strip()
        description   = request.form.get('description', '').strip()
        input_format  = request.form.get('input_format', '').strip()
        output_format = request.form.get('output_format', '').strip()
        sample_input  = request.form.get('sample_input', '').strip()
        sample_output = request.form.get('sample_output', '').strip()
        time_limit    = int(request.form.get('time_limit', 1000))
        memory_limit  = int(request.form.get('memory_limit', 65536))

        if not title or not description:
            flash('标题和题目描述不能为空', 'danger')
            return render_template('admin/create_problem.html')

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    '''INSERT INTO problems
                       (title, description, input_format, output_format,
                        sample_input, sample_output, time_limit, memory_limit, created_by)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (title, description, input_format, output_format,
                     sample_input, sample_output, time_limit, memory_limit,
                     session['user_id'])
                )
                problem_id = cur.lastrowid
            db.commit()
        finally:
            db.close()

        flash(f'题目 \"{title}\" 创建成功！题目 ID: {problem_id}', 'success')
        return redirect(url_for('manage_problems'))

    return render_template('admin/create_problem.html')



# ============================================================
# 管理员：编辑题目
# ============================================================
@app.route('/admin/problems/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_problem(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM problems WHERE id=%s', (pid,))
            problem = cur.fetchone()
    finally:
        db.close()

    if not problem:
        flash('题目不存在', 'danger')
        return redirect(url_for('manage_problems'))

    if request.method == 'POST':
        title         = request.form.get('title', '').strip()
        description   = request.form.get('description', '').strip()
        input_format  = request.form.get('input_format', '').strip()
        output_format = request.form.get('output_format', '').strip()
        sample_input  = request.form.get('sample_input', '').strip()
        sample_output = request.form.get('sample_output', '').strip()
        time_limit    = int(request.form.get('time_limit', 1000))
        memory_limit  = int(request.form.get('memory_limit', 65536))

        if not title or not description:
            flash('标题和题目描述不能为空', 'danger')
            return render_template('admin/edit_problem.html', problem=problem)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    '''UPDATE problems SET
                       title=%s, description=%s, input_format=%s, output_format=%s,
                       sample_input=%s, sample_output=%s, time_limit=%s, memory_limit=%s
                       WHERE id=%s''',
                    (title, description, input_format, output_format,
                     sample_input, sample_output, time_limit, memory_limit, pid)
                )
            db.commit()
        finally:
            db.close()

        flash(f'题目 "{title}" 已更新', 'success')
        return redirect(url_for('manage_problems'))

    return render_template('admin/edit_problem.html', problem=problem)

# ============================================================
# 管理员：题目列表
# ============================================================
@app.route('/admin/problems')
@login_required
@admin_required
def manage_problems():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, title, time_limit, memory_limit, created_at FROM problems ORDER BY id DESC')
            problems = cur.fetchall()
    finally:
        db.close()
    return render_template('admin/manage_problems.html', problems=problems)


# ============================================================
# 管理员：管理测试数据
# ============================================================
@app.route('/admin/problems/<int:pid>/testdata', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_testdata(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, title FROM problems WHERE id=%s', (pid,))
            problem = cur.fetchone()
    finally:
        db.close()

    if not problem:
        flash('题目不存在', 'danger')
        return redirect(url_for('manage_problems'))

    if request.method == 'POST':
        input_data      = request.form.get('input_data', '')
        expected_output = request.form.get('expected_output', '')

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO test_cases (problem_id, input_data, expected_output) VALUES (%s,%s,%s)',
                    (pid, input_data, expected_output)
                )
            db.commit()
        finally:
            db.close()

        flash('测试用例添加成功', 'success')
        return redirect(url_for('manage_testdata', pid=pid))

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, input_data, expected_output FROM test_cases WHERE problem_id=%s', (pid,))
            test_cases = cur.fetchall()
    finally:
        db.close()

    return render_template('admin/testdata.html', problem=problem, test_cases=test_cases)



# ============================================================
# 管理员：批量导入测试数据（从本地目录读取 .in/.out 文件）
# ============================================================
@app.route('/admin/problems/<int:pid>/testdata/batch', methods=['POST'])
@login_required
@admin_required
def batch_import_testdata(pid):
    dir_path = request.form.get('dir_path', '').strip()

    if not dir_path or not os.path.isdir(dir_path):
        flash('目录不存在，请输入有效路径', 'danger')
        return redirect(url_for('manage_testdata', pid=pid))

    # 扫描目录中所有 .in 文件，匹配同名 .out 文件
    imported = 0
    errors = []
    db = get_db()
    try:
        for fname in sorted(os.listdir(dir_path)):
            if not fname.endswith('.in'):
                continue
            base = fname[:-3]  # 去掉 .in
            in_path  = os.path.join(dir_path, fname)
            out_path = os.path.join(dir_path, base + '.out')

            if not os.path.isfile(out_path):
                errors.append(f'{fname}: 缺少对应的 .out 文件')
                continue

            try:
                with open(in_path, 'r', encoding='utf-8') as f:
                    input_data = f.read()
                with open(out_path, 'r', encoding='utf-8') as f:
                    expected_output = f.read()
            except UnicodeDecodeError:
                try:
                    with open(in_path, 'r', encoding='gbk') as f:
                        input_data = f.read()
                    with open(out_path, 'r', encoding='gbk') as f:
                        expected_output = f.read()
                except Exception as e:
                    errors.append(f'{fname}: 读取失败 - {e}')
                    continue
            except Exception as e:
                errors.append(f'{fname}: 读取失败 - {e}')
                continue

            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO test_cases (problem_id, input_data, expected_output) VALUES (%s,%s,%s)',
                    (pid, input_data, expected_output)
                )
            imported += 1

        db.commit()
    finally:
        db.close()

    if imported > 0:
        flash(f'成功导入 {imported} 个测试用例', 'success')
    if errors:
        for e in errors[:5]:
            flash(f'跳过: {e}', 'warning')

    return redirect(url_for('manage_testdata', pid=pid))

@app.route('/admin/testdata/<int:tid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_testcase(tid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT problem_id FROM test_cases WHERE id=%s', (tid,))
            row = cur.fetchone()
            if row:
                pid = row['problem_id']
                cur.execute('DELETE FROM test_cases WHERE id=%s', (tid,))
            else:
                pid = None
        db.commit()
    finally:
        db.close()
    if pid:
        flash('测试用例已删除', 'success')
        return redirect(url_for('manage_testdata', pid=pid))
    return redirect(url_for('manage_problems'))


# ============================================================
# 管理员：查看所有提交
# ============================================================
@app.route('/admin/submissions')
@login_required
@admin_required
def admin_submissions():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT s.id, p.title, u.username, s.status,
                          s.score, s.test_total, s.time_used, s.memory_used,
                          s.submitted_at
                   FROM submissions s
                   JOIN problems p ON s.problem_id=p.id
                   JOIN users u ON s.user_id=u.id
                   ORDER BY s.id DESC LIMIT 50'''
            )
            submissions = cur.fetchall()
    finally:
        db.close()
    return render_template('admin/submissions.html', submissions=submissions)


# ============================================================
# 学生：题目详情 & 提交
# ============================================================
@app.route('/problem/<int:pid>', methods=['GET', 'POST'])
@login_required
def problem_detail(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                'SELECT id, title, description, input_format, output_format, '
                'sample_input, sample_output, time_limit, memory_limit '
                'FROM problems WHERE id=%s', (pid,)
            )
            problem = cur.fetchone()
    finally:
        db.close()

    if not problem:
        flash('题目不存在', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        code     = request.form.get('code', '')
        language = request.form.get('language', 'cpp')

        if not code.strip():
            flash('代码不能为空', 'danger')
            return render_template('student/problem.html', problem=problem, code=code, language=language)

        # 写入提交记录
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    '''INSERT INTO submissions (problem_id, user_id, code, language, status)
                       VALUES (%s,%s,%s,%s,'Pending')''',
                    (pid, session['user_id'], code, language)
                )
                submission_id = cur.lastrowid
            db.commit()
        finally:
            db.close()

        # 调用 C++ 判题程序
        result = run_judge(submission_id, pid, code, language)

        # 更新提交结果
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    '''UPDATE submissions SET
                       status=%s, score=%s, test_total=%s, detail=%s,
                       compile_error=%s, time_used=%s, memory_used=%s
                       WHERE id=%s''',
                    (result['status'],     result['score'],
                     result['test_total'], json.dumps(result['detail']),
                     result.get('compile_error'),
                     result.get('time_used'), result.get('memory_used'),
                     submission_id)
                )
            db.commit()
        finally:
            db.close()

        flash(f'判题完成: {result["status"]}', 'success' if result['status'] == 'Accepted' else 'warning')
        return redirect(url_for('my_submissions'))

    return render_template('student/problem.html', problem=problem, code='', language='cpp')


# ============================================================
# 学生：我的提交
# ============================================================
@app.route('/my/submissions')
@login_required
def my_submissions():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT s.id, p.title, s.status, s.score, s.test_total,
                          s.time_used, s.memory_used, s.language, s.submitted_at
                   FROM submissions s
                   JOIN problems p ON s.problem_id=p.id
                   WHERE s.user_id=%s
                   ORDER BY s.id DESC LIMIT 50''',
                (session['user_id'],)
            )
            submissions = cur.fetchall()
    finally:
        db.close()
    return render_template('student/submissions.html', submissions=submissions)


# ============================================================
# 学生：查看提交详情（含代码）
# ============================================================
@app.route('/submission/<int:sid>')
@login_required
def submission_detail(sid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT s.*, p.title, u.username
                   FROM submissions s
                   JOIN problems p ON s.problem_id=p.id
                   JOIN users u ON s.user_id=u.id
                   WHERE s.id=%s''', (sid,)
            )
            sub = cur.fetchone()
    finally:
        db.close()

    if not sub:
        flash('提交记录不存在', 'danger')
        return redirect(url_for('dashboard'))

    # 学生只能看自己的提交
    if session['role'] != 'admin' and sub['user_id'] != session['user_id']:
        flash('无权查看', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('submission_detail.html', sub=sub)


# ============================================================
# 调用 C++ 判题程序
# ============================================================
def run_judge(submission_id: int, problem_id: int, code: str, language: str) -> dict:
    """调用 judge.exe 进行代码评测"""
    if not os.path.exists(JUDGE_BIN):
        return {
            'status': 'System Error',
            'score': 0,
            'test_total': 0,
            'detail': [{'status': 'System Error', 'message': '判题程序未安装，请编译 judge/judge.cpp'}],
            'compile_error': None,
            'time_used': 0,
            'memory_used': 0,
        }

    # 准备临时工作目录
    work_dir = os.path.join(WORK_DIR, str(submission_id))
    os.makedirs(work_dir, exist_ok=True)

    # 写入代码
    ext_map = {'c': '.c', 'cpp': '.cpp', 'java': '.java', 'python': '.py'}
    code_file = os.path.join(work_dir, 'Main' + ext_map.get(language, '.cpp'))
    with open(code_file, 'w', encoding='utf-8') as f:
        f.write(code)

    # 获取测试用例和题目配置（合并为一次连接）
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, input_data, expected_output FROM test_cases WHERE problem_id=%s', (problem_id,))
            cases = cur.fetchall()
            cur.execute('SELECT time_limit, memory_limit FROM problems WHERE id=%s', (problem_id,))
            problem = cur.fetchone()
    finally:
        db.close()

    time_limit  = problem['time_limit'] if problem else 1000
    memory_limit = problem['memory_limit'] if problem else 65536

    # 写入测试用例
    input_dir = os.path.join(work_dir, 'input')
    answer_dir = os.path.join(work_dir, 'answer')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(answer_dir, exist_ok=True)

    for i, case in enumerate(cases):
        with open(os.path.join(input_dir, f'{i+1}.in'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(case['input_data'].rstrip() + '\n')
        with open(os.path.join(answer_dir, f'{i+1}.out'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(case['expected_output'].rstrip() + '\n')

    # 调用判决程序
    try:
        proc = subprocess.run(
            [JUDGE_BIN, str(submission_id), code_file, language,
             str(time_limit), str(memory_limit),
             input_dir, answer_dir, work_dir],
            capture_output=True, text=True, timeout=20, cwd=WORK_DIR
        )
        result = json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        result = {'status': 'System Error', 'score': 0, 'test_total': len(cases),
                   'detail': [], 'compile_error': 'Judging timeout'}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        result = {'status': 'System Error', 'score': 0, 'test_total': len(cases),
                   'detail': [], 'compile_error': str(e)}

    # 清理临时文件
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass

    return result


# ============================================================
# 启动
# ============================================================

# ============================================================
# ============================================================
# ============================================================
@app.route('/problem/<int:pid>/analysis')
@login_required
def problem_analysis(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, title FROM problems WHERE id=%s', (pid,))
            problem = cur.fetchone()
            if not problem:
                flash('题目不存在', 'danger')
                return redirect(url_for('dashboard'))
            cur.execute('SELECT * FROM v_problem_analysis WHERE problem_id=%s', (pid,))
            stats = cur.fetchone()
            cur.execute('SELECT status, COUNT(*) as cnt FROM submissions WHERE problem_id=%s GROUP BY status ORDER BY cnt DESC', (pid,))
            status_breakdown = cur.fetchall()
    finally:
        db.close()
    return render_template('student/analysis.html', problem=problem, stats=stats, status_breakdown=status_breakdown)

# ============================================================
# ============================================================
# ============================================================
@app.route('/ranking')
@login_required
def ranking():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT username, nickname, accepted_count, total_submissions, problems_passed, pass_rate FROM v_student_progress ORDER BY problems_passed DESC, pass_rate DESC')
            progress = cur.fetchall()
    finally:
        db.close()
    return render_template('student/ranking.html', progress=progress)


# ============================================================
# 论坛
# ============================================================
@app.route('/forum')
@login_required
def forum():
    db = get_db()
    try:
        with db.cursor() as cur:
            search_uid = request.args.get('search', '').strip()
            if search_uid and search_uid.isdigit():
                cur.execute(
                    '''SELECT f.id, f.content, f.image_url, f.video_url, f.is_pinned, f.created_at,
                              u.id AS uid, u.username, u.nickname
                       FROM forum_posts f JOIN users u ON f.user_id = u.id
                       WHERE u.id = %s
                       ORDER BY f.is_pinned DESC, f.created_at DESC''',
                    (int(search_uid),)
                )
            else:
                cur.execute(
                    '''SELECT f.id, f.content, f.image_url, f.video_url, f.is_pinned, f.created_at,
                              u.id AS uid, u.username, u.nickname
                       FROM forum_posts f JOIN users u ON f.user_id = u.id
                       ORDER BY f.is_pinned DESC, f.created_at DESC'''
                )
            posts = cur.fetchall()
    finally:
        db.close()
    return render_template('student/forum.html', posts=posts)


@app.route('/forum/new', methods=['GET', 'POST'])
@login_required
def forum_new():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash('内容不能为空', 'danger')
            return render_template('student/forum_new.html')

        image_url = None
        video_url = None

        # Handle image upload
        img_file = request.files.get('image')
        if img_file and img_file.filename:
            ext = img_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_EXTENSIONS and ext in {'png','jpg','jpeg','gif','bmp'}:
                import uuid
                fname = str(uuid.uuid4())[:12] + '.' + ext
                img_file.save(os.path.join(UPLOAD_FOLDER, fname))
                image_url = '/static/uploads/' + fname

        # Handle video upload
        vid_file = request.files.get('video')
        if vid_file and vid_file.filename:
            ext = vid_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_EXTENSIONS and ext in {'mp4','webm','avi','mov'}:
                import uuid
                fname = str(uuid.uuid4())[:12] + '.' + ext
                vid_file.save(os.path.join(UPLOAD_FOLDER, fname))
                video_url = '/static/uploads/' + fname

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO forum_posts (user_id, content, image_url, video_url) VALUES (%s, %s, %s, %s)',
                    (session['user_id'], content, image_url, video_url)
                )
                db.commit()
        finally:
            db.close()
        flash('帖子发布成功！', 'success')
        return redirect(url_for('forum'))

    return render_template('student/forum_new.html')


@app.route('/forum/post/<int:pid>')
@login_required
def forum_post(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                '''SELECT f.*, u.username, u.nickname
                   FROM forum_posts f JOIN users u ON f.user_id = u.id
                   WHERE f.id = %s''', (pid,)
            )
            post = cur.fetchone()
    finally:
        db.close()
    if not post:
        flash('帖子不存在', 'danger')
        return redirect(url_for('forum'))
    return render_template('student/forum_post.html', post=post)


@app.route('/forum/post/<int:pid>/delete', methods=['POST'])
@login_required
@admin_required
def forum_delete(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('DELETE FROM forum_posts WHERE id = %s', (pid,))
            db.commit()
    finally:
        db.close()
    flash('帖子已删除', 'success')
    return redirect(url_for('forum'))


@app.route('/forum/post/<int:pid>/pin', methods=['POST'])
@login_required
@admin_required
def forum_pin(pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT is_pinned FROM forum_posts WHERE id = %s', (pid,))
            post = cur.fetchone()
            if post:
                new_val = 0 if post['is_pinned'] else 1
                cur.execute('UPDATE forum_posts SET is_pinned = %s WHERE id = %s', (new_val, pid))
                db.commit()
                flash('已置顶' if new_val else '已取消置顶', 'success')
    finally:
        db.close()
    return redirect(url_for('forum'))


@app.route('/forum/user/<int:uid>')
@login_required
def forum_user(uid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, username, nickname, created_at FROM users WHERE id = %s', (uid,))
            user = cur.fetchone()
            if not user:
                flash('用户不存在', 'danger')
                return redirect(url_for('forum'))
            cur.execute(
                '''SELECT f.id, f.content, f.image_url, f.video_url, f.is_pinned, f.created_at
                   FROM forum_posts f
                   WHERE f.user_id = %s
                   ORDER BY f.created_at DESC''', (uid,)
            )
            posts = cur.fetchall()
    finally:
        db.close()
    return render_template('student/user_profile.html', profile_user=user, posts=posts)


# ============================================================
# 比赛系统
# ============================================================
@app.route('/contest')
@login_required
def contest_list():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT c.*, u.username AS creator_name FROM contests c JOIN users u ON c.created_by = u.id ORDER BY c.start_time DESC')
            contests = cur.fetchall()
            # Get registration count + user registration status for each contest
            for ct in contests:
                cur.execute('SELECT COUNT(*) as cnt FROM contest_registrations WHERE contest_id = %s', (ct['id'],))
                ct['reg_count'] = cur.fetchone()['cnt']
                cur.execute('SELECT id FROM contest_registrations WHERE contest_id = %s AND user_id = %s', (ct['id'], session['user_id']))
                ct['is_registered'] = cur.fetchone() is not None
    finally:
        db.close()
    return render_template('student/contest_list.html', contests=contests)


@app.route('/contest/create', methods=['GET', 'POST'])
@login_required
@admin_required
def contest_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        problem_ids = request.form.getlist('problem_ids')

        if not title or not start_time or not end_time:
            flash('请填写比赛名称和时间', 'danger')
            return redirect(url_for('contest_create'))
        if start_time >= end_time:
            flash('开始时间必须早于结束时间', 'danger')
            return redirect(url_for('contest_create'))

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO contests (title, description, start_time, end_time, created_by) VALUES (%s,%s,%s,%s,%s)',
                    (title, description or None, start_time, end_time, session['user_id'])
                )
                contest_id = cur.lastrowid
                for pid in problem_ids:
                    if pid.strip():
                        cur.execute(
                            'INSERT INTO contest_problems (contest_id, problem_id) VALUES (%s,%s)',
                            (contest_id, int(pid))
                        )
                db.commit()
        finally:
            db.close()
        flash('比赛创建成功！', 'success')
        return redirect(url_for('contest_list'))

    # GET: show form with available problems
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id, title FROM problems ORDER BY id')
            problems = cur.fetchall()
    finally:
        db.close()
    return render_template('admin/create_contest.html', problems=problems)


@app.route('/contest/<int:cid>')
@login_required
def contest_detail(cid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT c.*, u.username AS creator_name FROM contests c JOIN users u ON c.created_by = u.id WHERE c.id = %s', (cid,))
            contest = cur.fetchone()
            if not contest:
                flash('比赛不存在', 'danger')
                return redirect(url_for('contest_list'))

            # Contest problems
            cur.execute(
                'SELECT p.id, p.title, p.time_limit, p.memory_limit FROM contest_problems cp JOIN problems p ON cp.problem_id = p.id WHERE cp.contest_id = %s ORDER BY p.id', (cid,)
            )
            problems = cur.fetchall()

            # Registration status
            cur.execute('SELECT id FROM contest_registrations WHERE contest_id = %s AND user_id = %s', (cid, session['user_id']))
            is_registered = cur.fetchone() is not None

            # Get registrant count
            cur.execute('SELECT COUNT(*) as cnt FROM contest_registrations WHERE contest_id = %s', (cid,))
            reg_count = cur.fetchone()['cnt']
    finally:
        db.close()

    from datetime import datetime
    now = datetime.now()
    can_register = (not is_registered and session['role'] == 'student' and
                    now < contest['start_time'])
    # 开始前均可报名


    is_running = contest['start_time'] <= now <= contest['end_time']
    is_ended = now > contest['end_time']

    return render_template('student/contest_detail.html',
                         contest=contest, problems=problems,
                         is_registered=is_registered, can_register=can_register,
                         is_running=is_running, is_ended=is_ended, reg_count=reg_count)


@app.route('/contest/<int:cid>/register', methods=['POST'])
@login_required
def contest_register(cid):
    if session['role'] != 'student':
        flash('只有学生可以报名', 'danger')
        return redirect(url_for('contest_detail', cid=cid))

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT start_time FROM contests WHERE id = %s', (cid,))
            contest = cur.fetchone()
            if not contest:
                flash('比赛不存在', 'danger')
                return redirect(url_for('contest_list'))

            from datetime import datetime
            now = datetime.now()
            if now >= contest['start_time']:
                flash('报名已截止（比赛已开始）', 'danger')
                return redirect(url_for('contest_detail', cid=cid))

            cur.execute('SELECT id FROM contest_registrations WHERE contest_id = %s AND user_id = %s', (cid, session['user_id']))
            if cur.fetchone():
                flash('已报名', 'warning')
            else:
                cur.execute('INSERT INTO contest_registrations (contest_id, user_id) VALUES (%s,%s)', (cid, session['user_id']))
                db.commit()
                flash('报名成功！', 'success')
    finally:
        db.close()
    return redirect(url_for('contest_detail', cid=cid))


@app.route('/contest/<int:cid>/ranking')
@login_required
def contest_ranking(cid):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM contests WHERE id = %s', (cid,))
            contest = cur.fetchone()
            if not contest:
                flash('比赛不存在', 'danger')
                return redirect(url_for('contest_list'))

            # Get all registrations
            cur.execute(
                'SELECT u.id, u.username, u.nickname FROM contest_registrations cr JOIN users u ON cr.user_id = u.id WHERE cr.contest_id = %s', (cid,)
            )
            users_list = cur.fetchall()

            # Get contest problems
            cur.execute('SELECT problem_id FROM contest_problems WHERE contest_id = %s', (cid,))
            cp_ids = [r['problem_id'] for r in cur.fetchall()]

            # Get all submissions within contest window for these problems
            rankings = []
            for user in users_list:
                if not cp_ids:
                    rankings.append({'username': user['username'], 'nickname': user['nickname'], 'solved': 0, 'penalty': 0})
                    continue

                placeholders = ','.join(['%s'] * len(cp_ids))
                cur.execute(
                    f'''SELECT s.problem_id, s.status, s.submitted_at
                       FROM submissions s
                       WHERE s.user_id = %s AND s.problem_id IN ({placeholders})
                         AND s.submitted_at BETWEEN %s AND %s
                       ORDER BY s.submitted_at''',
                    [user['id']] + cp_ids + [contest['start_time'], contest['end_time']]
                )
                subs = cur.fetchall()

                # Calculate ACM ranking
                solved_problems = set()
                penalty_seconds = 0
                wrong_counts = {}  # problem_id -> wrong count before first AC

                for sub in subs:
                    pid = sub['problem_id']
                    if pid in solved_problems:
                        continue
                    if sub['status'] == 'Accepted':
                        solved_problems.add(pid)
                        elapsed = (sub['submitted_at'] - contest['start_time']).total_seconds()
                        wrong_before = wrong_counts.get(pid, 0)
                        penalty_seconds += int(elapsed) + wrong_before * 1200  # 20 min = 1200s
                    else:
                        wrong_counts[pid] = wrong_counts.get(pid, 0) + 1

                rankings.append({
                    'username': user['username'],
                    'nickname': user['nickname'],
                    'solved': len(solved_problems),
                    'penalty': int(penalty_seconds)
                })

            # Sort: solved DESC, penalty ASC
            rankings.sort(key=lambda x: (-x['solved'], x['penalty']))
    finally:
        db.close()

    from datetime import datetime
    now = datetime.now()
    is_running = contest['start_time'] <= now <= contest['end_time']

    return render_template('student/contest_ranking.html',
                         contest=contest, rankings=rankings, is_running=is_running)


@app.route('/contest/<int:cid>/problem/<int:pid>', methods=['GET', 'POST'])
@login_required
def contest_problem(cid, pid):
    db = get_db()
    try:
        with db.cursor() as cur:
            # Verify contest and registration
            cur.execute('SELECT * FROM contests WHERE id = %s', (cid,))
            contest = cur.fetchone()
            if not contest:
                flash('比赛不存在', 'danger')
                return redirect(url_for('contest_list'))

            from datetime import datetime
            now = datetime.now()
            if now < contest['start_time']:
                flash('比赛尚未开始', 'danger')
                return redirect(url_for('contest_detail', cid=cid))
            if now > contest['end_time']:
                flash('比赛已结束', 'danger')
                return redirect(url_for('contest_detail', cid=cid))

            if session['role'] == 'student':
                cur.execute('SELECT id FROM contest_registrations WHERE contest_id = %s AND user_id = %s', (cid, session['user_id']))
                if not cur.fetchone():
                    flash('你未报名此比赛', 'danger')
                    return redirect(url_for('contest_detail', cid=cid))

            # Get problem
            cur.execute('SELECT * FROM problems WHERE id = %s', (pid,))
            problem = cur.fetchone()
            if not problem:
                flash('题目不存在', 'danger')
                return redirect(url_for('contest_detail', cid=cid))

            cur.execute('SELECT id FROM contest_problems WHERE contest_id = %s AND problem_id = %s', (cid, pid))
            if not cur.fetchone():
                flash('该题目不属于此比赛', 'danger')
                return redirect(url_for('contest_detail', cid=cid))
    finally:
        db.close()

    if request.method == 'POST':
        code = request.form.get('code', '')
        language = request.form.get('language', 'cpp')
        if not code.strip():
            flash('代码不能为空', 'danger')
            return render_template('student/contest_problem.html', contest=contest, problem=problem, code=code, language=language)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO submissions (problem_id, user_id, code, language, status) VALUES (%s,%s,%s,%s,%s)',
                    (pid, session['user_id'], code, language, 'Pending')
                )
                submission_id = cur.lastrowid
            db.commit()
        finally:
            db.close()

        result = run_judge(submission_id, pid, code, language)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    '''UPDATE submissions SET status=%s, score=%s, test_total=%s, detail=%s,
                       compile_error=%s, time_used=%s, memory_used=%s WHERE id=%s''',
                    (result['status'], result['score'], result['test_total'], json.dumps(result['detail']),
                     result.get('compile_error'), result.get('time_used'), result.get('memory_used'), submission_id)
                )
            db.commit()
        finally:
            db.close()

        flash(f'判题完成: {result["status"]}', 'success' if result['status'] == 'Accepted' else 'warning')
        return redirect(url_for('contest_ranking', cid=cid))

    return render_template('student/contest_problem.html', contest=contest, problem=problem, code='', language='cpp')
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

