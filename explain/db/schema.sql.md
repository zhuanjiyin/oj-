# db/schema.sql — 数据库建表脚本

## 文件定位
MySQL 数据库的完整初始化脚本，一键创建数据库、所有表结构、视图、存储过程、触发器、默认用户数据。

## 执行方式
`ash
mysql -u root -pzjy200646 < db/schema.sql
`

## 内容结构

| 区块 | 说明 |
|------|------|
| 头部 | CREATE DATABASE IF NOT EXISTS oj_platform 创建数据库，指定 utf8mb4 字符集 |
| 表1 users | 用户表：id/username/password(SHA-256)/role(ENUM)/nickname；预插入 admin/student1/student2 |
| 表2 problems | 题目表：id/title/description/input_format/output_format/sample/时限/内存/created_by(FK) |
| 表3 	est_cases | 测试用例表：problem_id(FK CASCADE)/input_data/expected_output |
| 表4 submissions | 提交记录表：problem_id(FK)/user_id(FK)/code/语言(ENUM)/status(10种ENUM)/score/detail(JSON)/时间/内存/updated_at |
| 视图1 | _student_progress 学生成绩聚合 |
| 视图2 | _problem_analysis 题目难度分析 |
| 视图3 | _recent_activity 最近提交动态 |
| 存储过程1 | sp_student_ranking(IN min_sub INT) 学生排名 |
| 存储过程2 | sp_problem_detail(IN pid INT) 题目详细分析（3结果集） |
| 存储过程3 | sp_contest_ranking(IN cid INT) ACM比赛排名 |
| 触发器1 | 	rg_users_before_insert 自动设置默认昵称 |
| 触发器2 | 	rg_submissions_before_update 状态变更时间追踪 |
| 表5 orum_posts | 论坛帖子表：user_id(FK CASCADE)/content/image_url/video_url/is_pinned |
| 表6 contests | 比赛表：title/description/start_time/end_time/created_by(FK) |
| 表7 contest_problems | 比赛-题目 M:N 关联表，含 UNIQUE(contest_id, problem_id) |
| 表8 contest_registrations | 比赛-学生 M:N 报名表，含 UNIQUE(contest_id, user_id) |

## 设计要点
- 所有外键使用 ON DELETE CASCADE 保证引用完整性
- 字符集统一 utf8mb4_unicode_ci 完整支持中文
- submissions.detail 用 JSON 类型存储各测试点详情
- 10 种评测状态用 ENUM 约束防止脏数据
- 关联表用 UNIQUE 复合主键防止重复

## 上下游关系
`
db/schema.sql
  ├── 执行后生成: oj_platform 数据库 (16个对象)
  └── 被依赖: app.py 中所有 SQL 操作
`
"@, [System.Text.UTF8Encoding]::new(False))

[System.IO.File]::WriteAllText("E:\oj判题\explain\judge\judge.cpp.md", @"
# judge/judge.cpp — C++ 判题核心

## 文件定位
整个平台最关键的性能模块——编译用户代码、在资源限制下运行、对比输出、返回评测结果。

## 编译方式
`ash
g++ -o judge.exe judge.cpp -static -O2 -lpsapi
`
参数说明：-static 静态链接免 DLL 依赖、-O2 优化编译、-lpsapi 链接进程内存监控 API。

## 调用方式
`
judge.exe <submission_id> <code_file> <language> <time_limit_ms> <memory_limit_kb> <input_dir> <answer_dir> <work_dir>
`
输出：JSON 格式评测结果到 stdout

## 函数清单

| 函数 | 功能 |
|------|------|
| compile_code() | 调用 system("g++ ...") 编译代码，错误重定向到 compile.log |
| un_test() | 运行单个测试用例：CreateFile 打开 I/O → CreateProcess(带文件重定向) → WaitForSingleObject 超时监控 → GetProcessMemoryInfo 内存监控 → GetExitCodeProcess 退出码检查 → compare_output 输出对比 |
| compare_output() | 逐行比较输出（忽略行尾空格和回车） |
| kill_process_tree() | 超时时递归终止整个进程树 |
| list_input_files() | 按编号排序扫描 .in 文件 |
| escape_json() | 手动 JSON 转义（避免依赖第三方库） |
| output_result() | JSON 格式化输出到 stdout |

## 评测状态机
`
编译 → [失败] Compile Error
     → [成功] 逐个运行测试用例:
         → 超时 → Time Limit Exceeded
         → 超内存 → Memory Limit Exceeded
         → 退出码≠0 → Runtime Error
         → 输出不匹配 → Wrong Answer
         → 全部通过 → Accepted
`

## 关键技术
- **进程隔离**：CreateProcess + CREATE_NO_WINDOW 禁止GUI
- **时间控制**：WaitForSingleObject(pi.hProcess, time_limit_ms + 1000) 硬超时
- **内存控制**：GetProcessMemoryInfo → PeakWorkingSetSize / 1024
- **进程树清理**：CreateToolhelp32Snapshot → Process32First/Next 递归终止子进程
- **I/O 重定向**：STARTF_USESTDHANDLES + CreateFileA 直接重定向，无 cmd.exe 中间层

## 上下游关系
`
judge/judge.cpp
  ├── 编译产物: judge/judge.exe
  ├── 被调用: app.py → run_judge() → subprocess.run()
  ├── 依赖: MinGW g++ (编译时), 题目测试数据 (运行时)
  └── 输出: JSON → app.py 解析 → 写入 submissions 表
`
"@, [System.Text.UTF8Encoding]::new(False))

[System.IO.File]::WriteAllText("E:\oj判题\explain\judge\judge.exe.md", @"
# judge/judge.exe — 编译后的判题程序

## 文件定位
judge.cpp 经 g++ 编译生成的可执行文件，被 pp.py 通过 subprocess.run() 调用。

## 编译命令
`ash
cd judge
g++ -o judge.exe judge.cpp -static -O2 -lpsapi
`

## 输入参数（9个）
`
judge.exe <submission_id> <code_file> <lang> <tl_ms> <ml_kb> <input_dir> <answer_dir> <work_dir>
`

## 输出格式
标准输出 (stdout) 返回 JSON：
`json
{
  "status": "Accepted",
  "score": 3,
  "test_total": 3,
  "compile_error": null,
  "time_used": 15,
  "memory_used": 2048,
  "detail": [
    {"case_id":1,"status":"Accepted","time_ms":12,"memory_kb":1980,"error_msg":""}
  ]
}
`

## 注意事项
- 如果 judge.exe 不存在，pp.py 的 un_judge() 会直接返回 System Error
- 重新修改 judge.cpp 后需重新编译
- 该程序为 Windows 专用（依赖 Win32 API）