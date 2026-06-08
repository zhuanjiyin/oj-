# templates/student/contest_detail.html — 比赛详情

## 文件定位
比赛详情页，展示比赛信息、简介、题目列表和排名入口，GET /contest/<cid>。

## 页面元素
- 比赛信息卡片：标题 / 时间 / 创建者 / 报名人数 / 状态
- 报名按钮（比赛开始前，学生未报名时显示）
- 比赛简介卡片（有描述时显示）
- 比赛进行中 + 已报名/管理员：
  - 左侧：题目列表（每道题有 做题 按钮）
  - 右侧：报名人数卡片 + 查看实时排名 按钮
- 比赛未开始：题目将在比赛开始后显示

## 数据流
`
GET → contest_detail()
  → SELECT contests JOIN users WHERE c.id=?
  → SELECT contest_problems JOIN problems
  → SELECT contest_registrations 查报名状态和人数
`
