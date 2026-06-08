# templates/student/forum_post.html — 帖子详情

## 文件定位
查看单条帖子详情，GET /forum/post/<pid>。

## 页面元素
- 帖子完整内容（文本 + 图片 + 视频）
- 发布者信息（昵称 / @用户名）
- 发布时间
- 返回论坛链接

## 数据流
`
GET → forum_post() → SELECT forum_posts JOIN users WHERE f.id=?
`
