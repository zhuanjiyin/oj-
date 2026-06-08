# templates/admin/testdata.html — 测试数据管理

## 文件定位
管理员管理某道题目的测试用例，GET/POST /admin/problems/<id>/testdata。

## 页面元素
- 题目信息（标题）
- 手动添加表单：输入数据 + 期望输出
- 批量导入表单：磁盘目录路径（扫描 .in/.out 配对文件）
- 已有测试用例列表：每行可删除

## 数据流
`
手动添加 → INSERT INTO test_cases
批量导入 → 扫描目录 → 逐对 INSERT
删除 → DELETE FROM test_cases WHERE id=?
`
