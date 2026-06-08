# templates/admin/create_problem.html — 创建题目

## 文件定位
管理员创建新题目，GET/POST /admin/problems/create。

## 表单字段
- 标题（必填）
- 题目描述（必填）
- 输入格式 / 输出格式（选填）
- 样例输入 / 样例输出（选填）
- 时间限制（默认 1000ms）/ 内存限制（默认 65536KB）

## 数据流
`
填写表单 → POST → create_problem()
  → INSERT INTO problems → flash 成功 → redirect /admin/problems
`
