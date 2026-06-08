# judge/judge.cpp — C++ 判题核心

## 文件定位
整个平台最关键的性能模块——编译用户代码、在资源限制下运行、对比输出、返回评测结果。

## 编译方式
`
g++ -o judge.exe judge.cpp -static -O2 -lpsapi
`
参数说明：-static 静态链接免 DLL 依赖、-O2 优化编译、-lpsapi 链接进程内存监控 API。

## 调用方式
`
judge.exe <submission_id> <code_file> <language> <time_limit_ms> <memory_limit_kb> <input_dir> <answer_dir> <work_dir>
`
输出：JSON 格式评测结果到 stdout

## 函数清单

| 函数 | 功能 |
|------|------|
| compile_code() | 调用 system() 编译代码，错误重定向到 compile.log |
| run_test() | 运行单个测试用例：CreateFile 打开 I/O -> CreateProcess(带 STDIN/STDOUT 重定向) -> WaitForSingleObject 超时监控 -> GetProcessMemoryInfo 内存监控 -> GetExitCodeProcess 退出码检查 -> compare_output 输出对比 |
| compare_output() | 逐行比较输出（忽略行尾空格和回车） |
| kill_process_tree() | 超时时递归终止整个进程树 |
| list_input_files() | 按编号排序扫描 .in 文件 |
| escape_json() | 手动 JSON 转义（避免依赖第三方库） |
| output_result() | JSON 格式化输出到 stdout |

## 评测状态机

`
编译 -> [失败] Compile Error
     -> [成功] 逐个运行测试用例:
         -> 超时 -> Time Limit Exceeded
         -> 超内存 -> Memory Limit Exceeded
         -> 退出码!=0 -> Runtime Error
         -> 输出不匹配 -> Wrong Answer
         -> 全部通过 -> Accepted
`

## 关键技术
- 进程隔离：CreateProcess + CREATE_NO_WINDOW 禁止GUI
- 时间控制：WaitForSingleObject(pi.hProcess, time_limit_ms + 1000) 硬超时
- 内存控制：GetProcessMemoryInfo -> PeakWorkingSetSize / 1024
- I/O 重定向：STARTF_USESTDHANDLES + CreateFileA 直接重定向，无 cmd.exe 中间层
- 进程树清理：CreateToolhelp32Snapshot -> Process32First/Next 递归终止子进程

## 上下游关系
`
judge/judge.cpp
  +-- 编译产物: judge/judge.exe
  +-- 被调用: app.py -> run_judge() -> subprocess.run()
  +-- 依赖: MinGW g++ (编译时), 题目测试数据 (运行时)
  +-- 输出: JSON -> app.py 解析 -> 写入 submissions 表
`
