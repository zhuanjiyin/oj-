# templates/student/contest_problem.html — 比赛题目

## 文件定位
比赛中查看题目并提交代码，GET/POST /contest/<cid>/problem/<pid>。

## 页面元素
- 面包屑导航：← 比赛名 | 排名
- 题目信息：标题 / 时间限制 / 内存限制
- 题目描述 / 输入格式 / 输出格式 / 样例输入 / 样例输出
- 代码提交区：语言选择 + 代码编辑 + 提交按钮

## 权限校验
- 比赛不存在 → 错误
- 比赛未开始 → 错误
- 比赛已结束 → 错误
- 学生未报名 → 错误
- 题目不属于此比赛 → 错误

## 数据流
`
POST → INSERT INTO submissions → run_judge() → UPDATE
  → flash 判题结果 → redirect /contest/<cid>/ranking
`
