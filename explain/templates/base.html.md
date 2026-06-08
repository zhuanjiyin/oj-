# templates/base.html — 全局基础模板

## 文件定位
所有页面的 HTML 骨架，通过 Jinja2 的 extends 指令被其他 21 个模板继承。

## 核心内容

### 1. 内联 CSS
- 全局字体、背景色、卡片样式 (.card)
- 导航栏 .navbar 深色背景 + 白色链接
- 表单样式：input/textarea/select/button
- 表格样式：斑马纹、悬停高亮
- 状态徽章：.status-badge 不同颜色的评测状态
- Alert 消息：.alert-success / .alert-danger / .alert-warning

### 2. 导航栏
根据 session.role 显示不同菜单：
- 管理员：管理面板 / 题目管理 / 提交记录 / 比赛 / 论坛
- 学生：题目列表 / 我的提交 / 成绩排名 / 比赛 / 论坛
- 右上角：我的主页 | 昵称(角色) | 退出

### 3. Flash 消息区域
遍历 get_flashed_messages() 显示操作反馈（成功绿色/失败红色/警告黄色）

### 4. 内容占位
block content 供子模板注入页面主体内容

## 上下游关系
`
base.html
  ├── 被继承: 所有 21 个页面模板
  ├── 读取: session.user_id, session.role, session.nickname
  └── 渲染: get_flashed_messages()
`
