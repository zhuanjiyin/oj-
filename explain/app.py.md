# app.py — Flask Web 主程序

## 文件定位
整个 OJ 判题平台的 Web 后端核心，负责接收 HTTP 请求、处理业务逻辑、调用判题引擎、渲染页面。是项目的中枢神经。

## 模块划分

| 行号范围 | 模块 | 功能 |
|----------|------|------|
| 1-30 | 导入与配置 | Flask 初始化、数据库连接参数、静态文件路径 |
| 38-60 | 工具函数 | get_db() 数据库连接、romjson 模板过滤器 |
| 66-82 | 权限装饰器 | login_required（登录校验）、dmin_required（管理员校验） |
| 95-176 | 认证模块 | 登录 (/)、退出 (/logout)、注册 (/register) |
| 182-218 | 仪表盘 | /dashboard 按角色分流：管理员看统计卡片，学生看题目列表 |
| 223-314 | 题目管理 | 创建、编辑、列表（管理员专属） |
| 338-470 | 测试数据 | 手动添加、批量导入 .in/.out、删除（管理员专属） |
| 476-495 | 提交管理 | 管理员查看所有提交记录 |
| 501-567 | 学生判题 | 题目详情 + 代码提交 + 调用 un_judge() |
| 573-623 | 提交记录 | 我的提交列表、单条提交详情（含源码） |
| 629-707 | **判题引擎** | un_judge() 函数：准备临时目录 → 写代码 → 查测试用例 → 调用 judge.exe → 解析 JSON → 更新 DB |
| 717-749 | 数据分析 | 题目难度分析、成绩排名 |
| 755-906 | 论坛系统 | 发帖、列表、搜索、删帖、置顶、个人主页 |
| 912-1214 | 比赛系统 | 创建比赛、报名、详情、ACM 排名、比赛内提交 |

## 关键技术点

- **数据库连接**：每次请求新建连接，inally 块保证关闭，使用 pymysql.cursors.DictCursor 返回字典格式
- **安全**：密码 SHA-256 哈希存储、Session 会话管理、参数化查询防 SQL 注入
- **判题调用**：subprocess.run() 同步调用 judge.exe，超时 20 秒
- **文件清理**：shutil.rmtree() 清理判题临时目录
- **文件上传**：论坛图片/视频存入 static/uploads/，UUID 防重名

## 上下游关系
`
app.py
  ├── 引用: config.py (DB_CONFIG), judge/judge.exe
  ├── 渲染: templates/ (22个HTML模板)
  ├── 写入: static/uploads/ (论坛上传)
  └── 依赖: MySQL → db/schema.sql
`
"@, [System.Text.UTF8Encoding]::new(False))

[System.IO.File]::WriteAllText("E:\oj判题\explain\config.py.md", @"
# config.py — 应用配置文件

## 文件定位
集中管理数据库连接参数、Flask 密钥、判题程序路径。与 pp.py 中直接定义的配置保持同步。

## 配置项

| 变量 | 值 | 用途 |
|------|-----|------|
| DB_HOST | localhost | MySQL 服务器地址 |
| DB_PORT | 3306 | MySQL 端口 |
| DB_USER | oot | 数据库用户名 |
| DB_PASSWORD | zjy200646 | 数据库密码 |
| DB_NAME | oj_platform | 数据库名 |
| SECRET_KEY | oj_platform_secret_key_2026 | Flask Session 签名密钥 |
| JUDGE_BIN | judge/judge.exe | C++ 判题程序路径 |

## 注意事项
- 当前 pp.py 内部也定义了 DB_CONFIG 字典和 JUDGE_BIN，实际运行时以 pp.py 中的值为准
- config.py 作为独立配置模块便于环境切换（开发/生产）
- 密码硬编码仅适用于本地开发，生产环境应使用环境变量

## 上下游关系
`
config.py
  └── 被引用: app.py
`
"@, [System.Text.UTF8Encoding]::new(False))

[System.IO.File]::WriteAllText("E:\oj判题\explain\requirements.txt.md", @"
# requirements.txt — Python 依赖清单

## 文件定位
pip install -r requirements.txt 一键安装项目所需的所有 Python 包。

## 依赖列表

| 包名 | 版本 | 用途 |
|------|------|------|
| Flask | 3.0.0 | Web 框架，路由、模板渲染、Session |
| PyMySQL | 1.1.0 | MySQL 数据库驱动，纯 Python 实现 |

## 说明
- 项目只依赖 2 个第三方包，非常轻量
- Flask 自带 Jinja2 模板引擎和 Werkzeug WSGI 工具包
- PyMySQL 用 DictCursor 返回字典格式查询结果
- 判题引擎 judge.exe 是 C++ 编译产物，不占用 Python 依赖