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
