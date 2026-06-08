# templates/student/analysis.html — 题目难度分析

## 文件定位
查看某道题目的提交统计与难度评估，GET /problem/<pid>/analysis。

## 页面元素
- 题目名称
- 统计概览：总提交数 / 通过数 / 通过率（通过率越低难度越大）
- 状态分布表格：Accepted / Wrong Answer / Compile Error / TLE / RTE 各占多少

## 数据来源
- v_problem_analysis 视图：聚合统计
- submissions 表 GROUP BY status：状态分布

## 上下游关系
`
入口: problem.html 中的 题目难度分析 按钮
  → GET /problem/<pid>/analysis
  → 查询 v_problem_analysis + GROUP BY
`
