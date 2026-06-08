# judge/judge.exe — 编译后的判题程序

## 文件定位
judge.cpp 经 g++ 编译生成的可执行文件，被 app.py 通过 subprocess.run() 调用。

## 编译命令
`
cd judge
g++ -o judge.exe judge.cpp -static -O2 -lpsapi
`

## 输入参数（9个）
`
judge.exe <submission_id> <code_file> <lang> <tl_ms> <ml_kb> <input_dir> <answer_dir> <work_dir>
`

## 输出格式
标准输出 (stdout) 返回 JSON：
`
{
  "status": "Accepted",
  "score": 3, "test_total": 3,
  "compile_error": null,
  "time_used": 15, "memory_used": 2048,
  "detail": [
    {"case_id":1,"status":"Accepted","time_ms":12,"memory_kb":1980,"error_msg":""}
  ]
}
`

## 注意事项
- 如果 judge.exe 不存在，app.py 的 run_judge() 会直接返回 System Error
- 重新修改 judge.cpp 后需重新编译
- 该程序为 Windows 专用（依赖 Win32 API）
