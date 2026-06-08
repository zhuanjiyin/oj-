# templates/student/contest_ranking.html — 比赛排名

## 文件定位
比赛实时 ACM 排名，GET /contest/<cid>/ranking。

## 页面元素
- 标题：比赛名 - 排名
- 说明文字：ACM 赛制规则（过题数 DESC, 罚时 ASC）
- 排名表格：排名 / 用户 / 昵称 / 过题数（绿色）/ 罚时（MM:SS 格式）
- 当前用户行高亮（绿色背景）
- 底部：返回比赛 + 比赛列表按钮

## ACM 罚时计算
`
罚时 = SUM(首次AC时间 - 比赛开始时间 + 错误次数 * 20分钟)
`
排名规则：过题数 DESC（第一关键字），罚时 ASC（第二关键字）

## 数据流
`
GET → contest_ranking()
  → 查所有报名用户
  → 查所有比赛题目
  → 逐用户查比赛窗口内的提交
  → 在 Python 中计算 ACM 排名
  → 排序后渲染
`
