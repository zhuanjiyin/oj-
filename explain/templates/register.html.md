# templates/register.html — 注册页面

## 文件定位
新用户注册入口，GET /register 和 POST /register 共用，不继承 base.html。

## 页面元素
- 表单：用户名 + 密码 + 昵称（选填）
- 校验：用户名 3-20 位仅字母数字、密码至少 6 位
- 触发器 trg_users_before_insert 在写入时自动处理昵称默认值

## 数据流
`
填写表单 → POST /register → register() 校验
  → 成功: INSERT users (role=student) → redirect /login
  → 失败: flash → 重新渲染
`
