# templates/student/ranking.html — 成绩排名

## 文件定位
全局学生成绩排行榜，GET /ranking。

## 页面元素
- 排名表格：排名 / 用户名 / 昵称 / 通过题数 / 总提交 / 通过率
- 通过率颜色：>=80% 绿色、>=40% 橙色、<40% 红色
- 排序：通过题数 DESC，通过率 DESC

## 数据来源
v_student_progress 视图，查询语句：
`sql
SELECT * FROM v_student_progress ORDER BY problems_passed DESC, pass_rate DESC
`
