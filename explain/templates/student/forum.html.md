# templates/student/forum.html — 论坛首页

## 文件定位
论坛帖子列表，GET /forum，支持按用户ID搜索。

## 页面元素
- 顶部：+ 发布新帖 按钮
- 搜索栏：输入用户ID搜索，可清除
- 帖子卡片列表（置顶帖左边框橙色）：
  - 头部：昵称 / @用户名 / 发布时间
  - 管理员可见：置顶按钮 + 删除按钮
  - 内容：文本
  - 媒体：图片 img / 视频 video（带 onerror 容错）

## 数据流
`
GET /forum?search=<uid>
  → 有搜索: SELECT forum_posts JOIN users WHERE u.id=? ORDER BY is_pinned DESC, created_at DESC
  → 无搜索: SELECT ... ORDER BY is_pinned DESC, created_at DESC
`
