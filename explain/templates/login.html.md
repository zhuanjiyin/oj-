# templates/login.html — 登录页面

## 文件定位
用户访问网站的第一个页面，GET / 和 POST / 共用此模板，不继承 base.html。

## 页面元素
- 标题：OJ 判题平台
- 表单：用户名 + 密码输入框 + 登录按钮
- 链接：没有账号？立即注册 → /register

## 数据流
`
用户输入 → POST / → login() 验证 SHA-256
  → 成功: session 写入 → redirect /dashboard
  → 失败: flash 错误 → 重新渲染
`
