# OJ 判题平台 — 全局架构总览

## 一、项目定位

轻量级在线判题（Online Judge）系统，面向数据库课程设计。支持管理员创建题目、学生在线提交代码并获得实时评测结果，同时提供论坛交流与 ACM 赛制比赛功能。

---

## 二、技术栈层次

`
+---------------------------------------------+
|              浏览器 (HTML/CSS)               |  <- 21个Jinja2模板
+---------------------------------------------+
|          Flask Web Server (Python)           |  <- app.py 27条路由
|          Session / RBAC / Flash消息           |
+--------------------+------------------------+
|   PyMySQL 驱动      |   subprocess 子进程      |
|   (DictCursor)     |   (同步调用)             |
+--------------------+------------------------+
|   MySQL 8.0        |   C++ Judge Core       |
|   8表+3视图+3SP+2触发器 |   (judge.exe)        |
|                    |   Win32 API 资源控制     |
+--------------------+------------------------+
`

| 层次 | 技术 | 文件 |
|------|------|------|
| 前端 | HTML5 + CSS3 + Jinja2 | templates/ (22个文件) |
| Web 后端 | Python Flask 3.0 | app.py (27条路由) |
| 数据库驱动 | PyMySQL 1.1 | app.py 中 get_db() |
| 数据库 | MySQL 8.0 InnoDB | db/schema.sql (16个对象) |
| 判题引擎 | C++ (Win32 API) | judge/judge.cpp -> judge.exe |
| 配置 | Python dict | config.py |

---

## 三、数据流全景

### 3.1 核心业务流程

`
学生登录 -> 浏览题目列表 -> 点击题目进入详情
  -> 读题、写代码 -> 选择语言 -> 点击提交
  -> Flask 写入 submissions 表 (status=Pending)
  -> Flask 调用 judge.exe (subprocess, 同步等待)
    -> judge.exe 编译代码 (g++)
    -> judge.exe 逐个运行测试用例 (CreateProcess + 资源限制)
    -> judge.exe 输出对比 -> JSON 结果
  -> Flask 解析 JSON -> 更新 submissions 表
  -> Flash 消息通知结果 -> 页面刷新
`

### 3.2 比赛流程

`
管理员创建比赛(选时间+选题) -> 学生报名(比赛开始前)
  -> 比赛开始 -> 学生可查看题目+提交
  -> 提交后跳转实时排名页
  -> ACM排名: 过题数 DESC, 罚时 ASC
  -> 比赛结束 -> 排名定格
`

### 3.3 论坛流程

`
学生发布新帖(文本+可选图片/视频) -> 上传到 static/uploads/
  -> INSERT forum_posts -> 出现在论坛列表
管理员: 删除帖子 / 置顶切换
用户: 搜索(按用户ID) / 查看个人主页(所有发帖)
`

---

## 四、数据库对象全景

`
oj_platform 数据库
+-- 8 张业务表
|   +-- users           (用户)
|   +-- problems        (题目)
|   +-- test_cases      (测试用例)
|   +-- submissions     (提交记录, 含JSON)
|   +-- forum_posts     (论坛帖子)
|   +-- contests        (比赛)
|   +-- contest_problems    (M:N 关联)
|   +-- contest_registrations (M:N 关联)
+-- 3 个视图
|   +-- v_student_progress  (学生成绩聚合)
|   +-- v_problem_analysis  (题目难度分析)
|   +-- v_recent_activity   (最近动态)
+-- 3 个存储过程
|   +-- sp_student_ranking(min_sub)  (学生排名)
|   +-- sp_problem_detail(pid)       (题目分析, 多结果集)
|   +-- sp_contest_ranking(cid)      (ACM比赛排名)
+-- 2 个触发器
    +-- trg_users_before_insert      (自动设置昵称)
    +-- trg_submissions_before_update (状态变更时间追踪)
`

---

## 五、文件组织架构

`
mysolution/
+-- app.py                    *** Flask 主程序 (核心)
+-- config.py                 *** 数据库配置
+-- requirements.txt          包管理 Python 依赖
+-- DOCS.md                  *** 技术文档
+-- 部署指南.md                *** 部署教程
+-- db/
|   +-- schema.sql            *** 数据库建表脚本
+-- judge/
|   +-- judge.cpp             *** C++ 判题源码
|   +-- judge.exe             *** 编译后的判题程序
|   +-- Makefile              *** 编译脚本
+-- templates/
|   +-- base.html             *** 全局骨架 (被21个模板继承)
|   +-- login.html            *** 登录页
|   +-- register.html         *** 注册页
|   +-- submission_detail.html *** 提交详情
|   +-- admin/                *** 管理员页面 (7个)
|   +-- student/              *** 学生页面 (14个)
+-- static/
    +-- uploads/              *** 论坛上传文件
`

---

## 六、路由架构 (27条)

| 模块 | 路由数 | 核心功能 |
|------|--------|---------|
| 认证 | 3 | 登录 / 注册 / 退出 |
| 仪表盘 | 1 | 按角色分流 |
| 题目管理 | 3 | 创建 / 编辑 / 列表 (管理员) |
| 测试数据 | 4 | 添加 / 批量导入 / 删除 (管理员) |
| 提交记录 | 2 | 管理员看全部 / 学生看自己 |
| 判题 | 1 | 题目详情 + 代码提交 |
| 数据分析 | 2 | 题目难度分析 / 成绩排名 |
| 论坛 | 6 | 列表 / 发帖 / 详情 / 删除 / 置顶 / 个人主页 |
| 比赛 | 6 | 列表 / 创建 / 详情 / 报名 / 排名 / 比赛内提交 |
| **合计** | **27** | |

---

## 七、安全机制

| 机制 | 实现 |
|------|------|
| 身份认证 | Session 会话，密码 SHA-256 哈希存储 |
| 权限控制 | @login_required + @admin_required 装饰器 |
| SQL 注入防护 | 全部使用参数化查询 (%s 占位符) |
| 文件上传 | UUID 重命名，扩展名白名单校验 |
| 进程隔离 | judge.exe 作为独立子进程运行 |

---

## 八、阅读导航

| 想要了解... | 去看... |
|------------|--------|
| 整体怎么工作的 | 本页 OVERVIEW.md |
| 主程序所有路由 | app.py.md |
| 数据库怎么建的 | db/schema.sql.md |
| 判题怎么实现的 | judge/judge.cpp.md |
| 页面长什么样 | templates/ 目录下各文件 |
| 怎么部署运行 | 部署指南.md |
| 所有文件索引 | 00-文件索引.md |
