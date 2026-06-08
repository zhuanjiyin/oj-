# templates/student/dashboard.html — 学生仪表盘

## 文件定位
学生登录后的首页，GET /dashboard（role=student 时渲染）。

## 页面元素
- 题目列表表格：ID / 标题 / 时间限制 / 内存限制 / 操作（进入按钮）
- 最近提交表格：ID / 题目 / 状态（彩色徽章）/ 通过数 / 提交时间
- 最近 20 条提交，按 ID 降序

## 数据流
`
GET /dashboard → dashboard() 检测 role=student
  → SELECT problems ORDER BY id DESC
  → SELECT submissions JOIN problems WHERE user_id=? ORDER BY id DESC LIMIT 20
`
