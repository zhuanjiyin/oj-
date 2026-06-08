# config.py — 应用配置文件

## 文件定位
集中管理数据库连接参数、Flask 密钥、判题程序路径。

## 配置项

| 变量 | 值 | 用途 |
|------|-----|------|
| DB_HOST | localhost | MySQL 服务器地址 |
| DB_PORT | 3306 | MySQL 端口 |
| DB_USER | root | 数据库用户名 |
| DB_PASSWORD | zjy200646 | 数据库密码 |
| DB_NAME | oj_platform | 数据库名 |
| SECRET_KEY | oj_platform_secret_key_2026 | Flask Session 签名密钥 |
| JUDGE_BIN | judge/judge.exe | C++ 判题程序路径 |

## 注意事项
- 当前 app.py 内部也定义了 DB_CONFIG 字典，实际运行时以 app.py 中的值为准
- 密码硬编码仅适用于本地开发，生产环境应使用环境变量
