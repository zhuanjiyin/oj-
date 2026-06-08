# templates/student/problem.html — 题目详情与提交

## 文件定位
学生查看题目描述并在线提交代码，GET/POST /problem/<pid>。

## 页面元素
- 题目信息卡片：标题 / 时间限制 / 内存限制
- 题目描述 / 输入格式 / 输出格式 / 样例输入 / 样例输出
- 题目难度分析按钮 → /problem/<pid>/analysis
- 代码提交区：语言下拉框（C/C++/Python）+ 代码编辑 textarea + 提交按钮

## 数据流
`
GET → problem_detail() → SELECT problems WHERE id=?
POST → INSERT INTO submissions → run_judge() → UPDATE submissions
  → flash 判题结果 → redirect /my/submissions
`
