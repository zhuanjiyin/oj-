# templates/admin/dashboard.html — 管理员仪表盘

## 文件定位
管理员登录后的首页，GET /dashboard（role=admin 时渲染）。

## 页面元素
- 统计卡片：题目总数、提交总数、学生总数
- 快捷入口：题目管理、创建题目

## 数据流
`
GET /dashboard → dashboard() 检测 role=admin
  → 查询 SELECT COUNT(*) FROM problems/submissions/users
  → 渲染三张统计卡片
`
