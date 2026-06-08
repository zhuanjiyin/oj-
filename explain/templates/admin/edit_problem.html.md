# templates/admin/edit_problem.html — 编辑题目

## 文件定位
管理员修改已有题目，GET/POST /admin/problems/<id>/edit。

## 页面元素
- 表单预填当前题目所有字段值
- 与创建题目表单相同结构
- 提交后 UPDATE problems SET ... WHERE id=?

## 数据流
`
GET → 查询 problems 表 → 预填表单
POST → UPDATE problems → flash 成功 → redirect /admin/problems
`
