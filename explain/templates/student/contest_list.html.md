# templates/student/contest_list.html — 比赛列表

## 文件定位
展示所有比赛的列表，GET /contest。

## 页面元素
- 管理员可见：+ 创建比赛 按钮
- 比赛卡片（颜色左边框表示状态）：
  - 蓝色 = 即将开始
  - 绿色 = 进行中
  - 灰色 = 已结束
- 每张卡片：标题 / 开始时间 / 结束时间 / 创建者 / 报名人数 / 状态标签 / 进入比赛按钮

## 数据流
`
GET → contest_list()
  → SELECT contests JOIN users ORDER BY start_time DESC
  → 逐条查 reg_count 和 is_registered
`
