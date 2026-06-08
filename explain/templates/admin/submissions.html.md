# templates/admin/submissions.html — 所有提交记录

## 文件定位
管理员查看全部用户的提交，GET /admin/submissions。

## 页面元素
- 提交表格：ID / 题目 / 用户 / 状态 / 通过数 / 时间 / 内存 / 提交时间
- 最近 50 条，按 ID 降序

## 数据流
`
GET → admin_submissions() → SELECT submissions JOIN problems JOIN users ORDER BY id DESC LIMIT 50
`
