# templates/submission_detail.html — 提交详情页

## 文件定位
显示单条提交的完整信息，GET /submission/<sid>，学生只能看自己的。

## 页面元素
- 基本信息：题目、提交者、状态、通过数、时间、内存、提交时间
- 源代码展示：pre 标签原样显示
- 编译错误（如有）：红色高亮
- 测试点详情表格：case_id / status / time / memory / error

## 数据来源
submissions 表 JOIN problems + users，detail 字段为 JSON 格式。
