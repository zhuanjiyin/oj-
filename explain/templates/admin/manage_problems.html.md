# templates/admin/manage_problems.html — 题目列表

## 文件定位
管理员查看所有题目，GET /admin/problems。

## 页面元素
- 题目表格：ID / 标题 / 时间限制 / 内存限制 / 创建时间
- 每行操作：编辑、测试数据
- 顶部按钮：+ 创建题目

## 数据流
`
GET → manage_problems() → SELECT * FROM problems ORDER BY id DESC
`
