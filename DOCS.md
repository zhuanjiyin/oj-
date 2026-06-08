# OJ 判题平台 — 技术文档

## 1. 项目概述

轻量级在线判题（Online Judge）平台，面向数据库课程设计。支持管理员创建题目与管理测试数据，学生注册后在线提交代码并获取实时评测结果，同时提供论坛交流与 ACM 赛制比赛功能。

**技术栈**: Python Flask（Web 后端）+ C++ Judge Core（判题核心）+ MySQL 8.0（数据持久化）

**角色体系**: 基于 RBAC 的双角色模型——管理员（admin）与学生（student）。

## 2. 系统架构

```
浏览器 --HTTP--> Flask Web Server (app.py)  [27 条路由]
                    |
                    +-- MySQL 8.0 (oj_platform)
                    |     +-- 8 张业务表
                    |     +-- 2 张多对多关联表 (contest_problems, contest_registrations)
                    |     +-- 3 个视图 (v_student_progress, v_problem_analysis, v_recent_activity)
                    |     +-- 3 个存储过程 (sp_student_ranking, sp_problem_detail, sp_contest_ranking)
                    |     +-- 2 个触发器 (trg_users_before_insert, trg_submissions_before_update)
                    |
                    +-- subprocess --> C++ Judge (judge.exe)
                          +-- 编译 (g++/gcc)
                          +-- 运行 + 资源限制 (WaitForSingleObject / GetProcessMemoryInfo)
                          +-- 输出对比 (逐行比较，忽略行尾空格)
```

### 2.1 角色与权限

| 角色 | 权限说明 |
|------|---------|
| 管理员 (admin) | 创建/编辑题目、管理测试数据、查看所有提交记录、创建和管理比赛、管理论坛帖子（删除/置顶） |
| 学生 (student) | 注册账号、浏览题目、提交代码、查看提交记录、查看成绩排名、参与论坛、报名与参加比赛 |

## 3. 数据库设计

### 3.1 E-R 图

```
                    ┌──────────────┐
                    │    users     │
                    │  (用户表)     │
                    └──┬───┬───┬──┘
                       │   │   │
              1        │   │   │       1
          ┌────────────┘   │   └────────────┐
          │                │                │
          N                │                N
 ┌────────┴────────┐       │       ┌────────┴────────┐
 │  submissions    │       │       │  forum_posts    │
 │  (提交记录)      │       │       │  (论坛帖子)      │
 └────────┬────────┘       │       └─────────────────┘
          │                │
          N                │
          │           1    │
 ┌────────┴────────┐       │
 │   problems      │       │
 │   (题目表)       │───────┘
 └──┬──────────┬───┘
    │          │
   1│          │M:N  contest_problems (关联表)
    │          │
    N     ┌────┴──────┐   1
 ┌────────┴────────┐  │  ┌──────────────┐
 │  test_cases     │  └──│   contests   │
 │  (测试用例)      │     │   (比赛表)    │
 └─────────────────┘     └──────┬───────┘
                                │M:N  contest_registrations (关联表)
                                │
                                │1
                          ┌─────┴──────┐
                          │    users   │
                          │  (用户表)   │
                          └────────────┘

实体关系说明：
  users 1──N submissions    (一个用户可以有多次提交)
  users 1──N forum_posts    (一个用户可以发布多个帖子)
  problems 1──N submissions (一道题目可以有多次提交)
  problems 1──N test_cases  (一道题目可以有多个测试用例)
  users 1──N problems       (管理员创建题目)
  contests M──N problems    (通过 contest_problems 关联)
  contests M──N users       (通过 contest_registrations 关联，学生报名)
```

### 3.2 表结构

**users（用户表）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| username | VARCHAR(64) | UNIQUE NOT NULL | 用户名 |
| password | VARCHAR(255) | NOT NULL | SHA-256 哈希密码 |
| role | ENUM('admin','student') | NOT NULL, DEFAULT 'student' | 角色 |
| nickname | VARCHAR(64) | DEFAULT NULL | 显示昵称 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 注册时间 |

**problems（题目表）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| title | VARCHAR(255) | NOT NULL | 题目标题 |
| description | TEXT | NOT NULL | 题目描述 |
| input_format | TEXT | DEFAULT NULL | 输入格式说明 |
| output_format | TEXT | DEFAULT NULL | 输出格式说明 |
| sample_input | TEXT | DEFAULT NULL | 样例输入 |
| sample_output | TEXT | DEFAULT NULL | 样例输出 |
| time_limit | INT | NOT NULL, DEFAULT 1000 | 时间限制(ms) |
| memory_limit | INT | NOT NULL, DEFAULT 65536 | 内存限制(KB) |
| created_by | INT | FK→users(id) | 创建者 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**test_cases（测试用例表）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| problem_id | INT | FK→problems(id) ON DELETE CASCADE | 关联题目 |
| input_data | TEXT | NOT NULL | 输入数据 |
| expected_output | TEXT | NOT NULL | 期望输出 |

**submissions（提交记录表）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| problem_id | INT | FK→problems(id) | 题目 |
| user_id | INT | FK→users(id) | 提交用户 |
| code | LONGTEXT | NOT NULL | 源代码 |
| language | ENUM('c','cpp','java','python') | NOT NULL, DEFAULT 'cpp' | 编程语言 |
| status | ENUM('Pending','Compiling','Running','Accepted','Wrong Answer','Compile Error','Time Limit Exceeded','Memory Limit Exceeded','Runtime Error','System Error') | NOT NULL, DEFAULT 'Pending' | 评测状态 |
| score | INT | NOT NULL, DEFAULT 0 | 通过测试点数 |
| test_total | INT | NOT NULL, DEFAULT 0 | 总测试点数 |
| compile_error | TEXT | DEFAULT NULL | 编译错误信息 |
| detail | JSON | DEFAULT NULL | 各测试点详情 |
| time_used | INT | DEFAULT NULL | 运行时间(ms) |
| memory_used | INT | DEFAULT NULL | 内存使用(KB) |
| submitted_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 提交时间 |
| updated_at | DATETIME | DEFAULT NULL | 状态变更时间(由触发器维护) |

**forum_posts（论坛帖子表）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| user_id | INT | FK→users(id) ON DELETE CASCADE | 发帖用户 |
| content | TEXT | NOT NULL | 帖子内容 |
| image_url | VARCHAR(512) | DEFAULT NULL | 图片链接 |
| video_url | VARCHAR(512) | DEFAULT NULL | 视频链接 |
| is_pinned | TINYINT(1) | NOT NULL, DEFAULT 0 | 是否置顶 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 发布时间 |

**contests（比赛表）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| title | VARCHAR(255) | NOT NULL | 比赛名称 |
| description | TEXT | DEFAULT NULL | 比赛简介/规则 |
| start_time | DATETIME | NOT NULL | 开始时间 |
| end_time | DATETIME | NOT NULL | 结束时间 |
| created_by | INT | FK→users(id) | 创建者 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**contest_problems（比赛题目关联表，M:N）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| contest_id | INT | FK→contests(id) ON DELETE CASCADE | 比赛 |
| problem_id | INT | FK→problems(id) ON DELETE CASCADE | 题目 |
|  |  | UNIQUE(contest_id, problem_id) | 防止重复关联 |

**contest_registrations（比赛报名表，M:N）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK AUTO_INCREMENT | 自增主键 |
| contest_id | INT | FK→contests(id) ON DELETE CASCADE | 比赛 |
| user_id | INT | FK→users(id) ON DELETE CASCADE | 报名学生 |
| registered_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 报名时间 |
|  |  | UNIQUE(contest_id, user_id) | 防止重复报名 |

### 3.3 视图设计

**v_student_progress（学生成绩统计视图）**

聚合每位学生的提交总数、通过数、通过题数（去重）、通过率、最近提交时间。按通过题数 DESC + 通过率 DESC 排序。

```sql
CREATE VIEW v_student_progress AS
SELECT u.id AS user_id, u.username, u.nickname,
  COUNT(s.id) AS total_submissions,
  SUM(CASE WHEN s.status='Accepted' THEN 1 ELSE 0 END) AS accepted_count,
  COUNT(DISTINCT CASE WHEN s.status='Accepted' THEN s.problem_id END) AS problems_passed,
  CASE WHEN COUNT(s.id)>0 
    THEN ROUND(SUM(CASE WHEN s.status='Accepted' THEN 1 ELSE 0 END)*100.0/COUNT(s.id),1) 
    ELSE 0 END AS pass_rate,
  MAX(s.submitted_at) AS last_submit_time
FROM users u LEFT JOIN submissions s ON u.id=s.user_id
WHERE u.role='student'
GROUP BY u.id, u.username, u.nickname;
```

**v_problem_analysis（题目难度分析视图）**

统计每道题的总提交次数、通过次数、通过率。

```sql
CREATE VIEW v_problem_analysis AS
SELECT p.id AS problem_id, p.title, p.time_limit, p.memory_limit,
  COUNT(s.id) AS total_submissions,
  SUM(CASE WHEN s.status='Accepted' THEN 1 ELSE 0 END) AS accepted_count,
  CASE WHEN COUNT(s.id)>0 
    THEN ROUND(SUM(CASE WHEN s.status='Accepted' THEN 1 ELSE 0 END)*100.0/COUNT(s.id),1) 
    ELSE 0 END AS pass_rate
FROM problems p LEFT JOIN submissions s ON p.id=s.problem_id
GROUP BY p.id, p.title, p.time_limit, p.memory_limit;
```

**v_recent_activity（最近动态视图）**

展示最近的提交记录，关联题目名和用户名。

```sql
CREATE VIEW v_recent_activity AS
SELECT s.id AS submission_id, p.title AS problem_title,
  u.username AS student_name, s.status, s.score, s.test_total,
  s.time_used, s.memory_used, s.submitted_at
FROM submissions s 
JOIN problems p ON s.problem_id=p.id 
JOIN users u ON s.user_id=u.id
ORDER BY s.submitted_at DESC;
```

### 3.4 存储过程设计

**sp_student_ranking(IN min_sub INT)** — 学生成绩排名

接收最少提交次数参数，返回每位学生的提交数、通过数、通过率、平均运行时间。

**sp_problem_detail(IN pid INT)** — 题目详细分析

返回题目基本信息 + 各状态统计（AC/WA/CE/TLE/RTE）+ 最近 10 条提交记录。一次调用返回 3 个结果集。

**sp_contest_ranking(IN cid INT)** — ACM 比赛排名

计算比赛的 ACM 排名：对每位报名学生，统计通过题数（Accepted 去重）和罚时（首次 AC 时间 − 比赛开始时间 + 错误次数 × 1200 秒），按通过题数 DESC + 罚时 ASC 排序。

### 3.5 触发器设计

**trg_users_before_insert** — 自动设置默认昵称

在 INSERT 用户时，若 nickname 为空或 NULL，自动设为 username 的值。

```sql
CREATE TRIGGER trg_users_before_insert
BEFORE INSERT ON users FOR EACH ROW
BEGIN
  IF NEW.nickname IS NULL OR NEW.nickname='' THEN
    SET NEW.nickname = NEW.username;
  END IF;
END;
```

**trg_submissions_before_update** — 状态变更时间追踪

在 UPDATE 提交记录时，若 status 字段发生变化，自动更新 updated_at 字段为当前时间。

```sql
CREATE TRIGGER trg_submissions_before_update
BEFORE UPDATE ON submissions FOR EACH ROW
BEGIN
  IF NEW.status != OLD.status OR OLD.status IS NULL THEN
    SET NEW.updated_at = NOW();
  END IF;
END;
```

## 4. 判题流程

```
1. 学生提交代码 (HTTP POST)
2. Flask 写入 submissions 表 (status='Pending')
3. Flask 通过 subprocess.run() 调用 judge.exe
4. judge.exe 执行:
   a. 编译代码 (g++/gcc)
      失败 → status='Compile Error'，捕获 stderr
   b. 逐个运行测试用例
      - CreateProcess + WaitForSingleObject(超时)
      - GetProcessMemoryInfo(内存限制)
      - GetExitCodeProcess(检查 Runtime Error)
      - 逐行对比输出 (忽略行尾空格)
   c. 输出 JSON 结果到 stdout
5. Flask 解析 JSON → 更新 submissions 表
6. shutil.rmtree() 清理临时工作目录
7. Flash 消息通知用户判题结果
```

### 4.1 判题核心参数

```
judge.exe <submission_id> <code_file> <language> <time_limit_ms> <memory_limit_kb> <input_dir> <answer_dir> <work_dir>
```

### 4.2 输出 JSON 格式

```json
{
  "status": "Accepted",
  "score": 3, "test_total": 3,
  "compile_error": null,
  "time_used": 15, "memory_used": 2048,
  "detail": [
    {"case_id":1, "status":"Accepted", "time_ms":12, "memory_kb":1980, "error_msg":""}
  ]
}
```

## 5. API 路由一览

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET/POST | `/` | 公开 | 登录页 |
| GET | `/logout` | 登录 | 退出登录 |
| GET/POST | `/register` | 公开 | 学生注册 |
| GET | `/dashboard` | 登录 | 按角色跳转仪表盘 |
| GET/POST | `/admin/problems/create` | 管理员 | 创建题目 |
| GET/POST | `/admin/problems/<id>/edit` | 管理员 | 编辑题目 |
| GET | `/admin/problems` | 管理员 | 题目列表 |
| GET/POST | `/admin/problems/<id>/testdata` | 管理员 | 管理测试数据 |
| POST | `/admin/problems/<id>/testdata/batch` | 管理员 | 批量导入测试用例 |
| POST | `/admin/testdata/<id>/delete` | 管理员 | 删除单个测试用例 |
| GET | `/admin/submissions` | 管理员 | 查看所有提交 |
| GET/POST | `/problem/<id>` | 登录 | 题目详情与提交 |
| GET | `/my/submissions` | 登录 | 我的提交记录 |
| GET | `/submission/<id>` | 登录 | 提交详情（含代码） |
| GET | `/problem/<id>/analysis` | 登录 | 题目难度分析 |
| GET | `/ranking` | 登录 | 学生成绩排名 |
| GET | `/forum` | 登录 | 论坛首页（支持用户ID搜索） |
| GET/POST | `/forum/new` | 登录 | 发布新帖 |
| GET | `/forum/post/<id>` | 登录 | 查看帖子详情 |
| POST | `/forum/post/<id>/delete` | 管理员 | 删除帖子 |
| POST | `/forum/post/<id>/pin` | 管理员 | 置顶/取消置顶 |
| GET | `/forum/user/<id>` | 登录 | 查看用户主页及帖子 |
| GET | `/contest` | 登录 | 比赛列表 |
| GET/POST | `/contest/create` | 管理员 | 创建比赛 |
| GET | `/contest/<id>` | 登录 | 比赛详情 |
| POST | `/contest/<id>/register` | 学生 | 报名比赛 |
| GET | `/contest/<id>/ranking` | 登录 | 比赛实时排名 |
| GET/POST | `/contest/<id>/problem/<id>` | 登录 | 比赛题目与提交 |

## 6. 文件结构

```
mysolution/
  app.py                          # Flask 主程序 (27条路由)
  config.py                       # 配置文件
  requirements.txt                # Python 依赖
  DOCS.md                         # 本文档
  db/
    schema.sql                    # 数据库建表脚本 (含视图/存储过程/触发器)
  judge/
    judge.cpp                     # C++ 判题核心
    judge.exe                     # 编译后的判题程序
    work/                         # 临时工作目录
  templates/
    base.html                     # 基础模板 (导航栏+flash消息)
    login.html                    # 登录页
    register.html                 # 注册页
    submission_detail.html        # 提交详情页
    admin/
      dashboard.html              # 管理仪表盘 (统计卡片)
      create_problem.html         # 创建题目
      manage_problems.html        # 题目列表
      edit_problem.html           # 编辑题目
      testdata.html              # 测试数据管理
      submissions.html           # 所有提交记录
      create_contest.html        # 创建比赛
    student/
      dashboard.html              # 学生仪表盘 (题目列表+最近提交)
      problem.html               # 题目详情与提交 (含难度分析链接)
      submissions.html           # 我的提交
      analysis.html              # 题目难度分析
      ranking.html               # 学生成绩排名
      forum.html                 # 论坛首页
      forum_new.html             # 发布新帖
      forum_post.html            # 帖子详情
      user_profile.html          # 用户主页
      contest_list.html          # 比赛列表
      contest_detail.html        # 比赛详情
      contest_ranking.html       # 比赛排名
      contest_problem.html       # 比赛题目与提交
  static/
    uploads/                      # 论坛上传文件 (图片/视频)
```

## 7. 部署指南

### 7.1 环境要求

| 组件 | 版本 |
|------|------|
| Python | 3.8+ |
| MySQL | 8.0+ |
| MinGW-w64 (g++) | 8.0+ |
| pip 依赖 | Flask 3.0+, PyMySQL 1.1+ |

### 7.2 安装步骤

```bash
# Step 1: 创建数据库并导入表结构
mysql -u root -pzjy200646 < db/schema.sql

# Step 2: 安装 Python 依赖
pip install -r requirements.txt

# Step 3: 编译判题程序
cd judge
g++ -o judge.exe judge.cpp -static -O2 -lpsapi

# Step 4: 启动服务
python app.py
# 访问 http://127.0.0.1:5000
```

### 7.3 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 学生 | student1 | 123456 |
| 学生 | student2 | 123456 |

## 8. 关键 Bug 修复记录

### 8.1 cmd.exe 引号解析导致 Runtime Error

**现象**: C/C++ 代码提交后始终返回 Runtime Error (Exit code 1)

**根因**: `judge.cpp` 中 `cmd.exe /c "path\to\program.exe" < "in" > "out"` — Windows cmd.exe 看到命令以双引号开头时会剥离首尾引号，导致可执行文件路径被破坏。

**修复**: 移除 `exe_path` 外不必要的双引号：
```cpp
// 修复前: cmd = "\"" + exe_path + "\" < \"" + input_file + "\" > \"" + output_file + "\"";
// 修复后: cmd = exe_path + " < \"" + input_file + "\" > \"" + output_file + "\"";
```

### 8.2 中文 Flash 消息编码污染

**现象**: 比赛提交后弹出乱码（如 `u5224u9898u5b8cu6210: Accepted`）

**根因**: PowerShell 管道写入导致 `\\uXXXX` Unicode 转义的反斜杠丢失。

**修复**: 全部 28 处 flash 消息改用直接中文字符串。