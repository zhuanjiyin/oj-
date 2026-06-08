# templates/student/forum_new.html — 发布新帖

## 文件定位
学生发布论坛帖子，GET/POST /forum/new。

## 页面元素
- 表单：帖子内容 textarea（必填）
- 图片上传：file input（可选，支持 png/jpg/gif/bmp）
- 视频上传：file input（可选，支持 mp4/webm/avi/mov）
- 提交按钮 + 取消链接

## 数据流
`
POST /forum/new
  → 处理文件上传：uuid 防重名 → 存入 static/uploads/
  → INSERT INTO forum_posts (user_id, content, image_url, video_url)
  → redirect /forum
`
