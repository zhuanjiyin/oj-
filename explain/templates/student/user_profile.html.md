# templates/student/user_profile.html — 用户主页

## 文件定位
查看某用户的主页及其所有发帖，GET /forum/user/<uid>。

## 页面元素
- 用户信息卡片：昵称 / 用户ID / @用户名 / 注册日期
- 帖子列表：用户的全部帖子（文本 + 媒体），显示发布时间和置顶标志
- 返回论坛链接

## 数据流
`
GET → forum_user()
  → SELECT users WHERE id=?
  → SELECT forum_posts WHERE user_id=? ORDER BY created_at DESC
`
