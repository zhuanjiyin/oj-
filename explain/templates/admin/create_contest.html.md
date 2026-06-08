# templates/admin/create_contest.html — 创建比赛

## 文件定位
管理员创建新比赛，GET/POST /contest/create。

## 表单字段
- 比赛名称（必填）
- 比赛描述（选填）
- 开始时间 / 结束时间（必填，datetime-local 选择器）
- 选择题目（多选下拉框，Ctrl+点击多选，可选已有题目）

## 数据流
`
POST → contest_create()
  → INSERT INTO contests
  → 循环 INSERT INTO contest_problems（M:N 关联）
  → redirect /contest
`
