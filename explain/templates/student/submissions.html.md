# templates/student/submissions.html — 我的提交记录

## 文件定位
学生查看自己的提交历史，GET /my/submissions。

## 页面元素
- 提交表格：ID / 题目 / 状态 / 通过数 / 语言 / 时间 / 内存 / 提交时间
- 最近 50 条，按 ID 降序
- 每行可点击进入提交详情 (/submission/<sid>)

## 数据流
`
GET → my_submissions() → SELECT submissions JOIN problems WHERE user_id=? ORDER BY id DESC LIMIT 50
`
