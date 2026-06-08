// ============================================================
// OJ判题平台 - C++ 判题核心
// 编译: g++ -o judge.exe judge.cpp -static -O2 -lpsapi
// 用法: judge.exe <submission_id> <code_file> <lang> <tl> <ml> <input_dir> <answer_dir> <work_dir>
// 输出: JSON 到 stdout
// ============================================================
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <cstdio>

using namespace std;

struct TestResult {
    int case_id;
    string status;
    double time_ms;
    long long memory_kb;
    string error_msg;
};

struct JudgeResult {
    string status;
    int score;
    int test_total;
    vector<TestResult> detail;
    string compile_error;
    int time_used;
    int memory_used;
};

vector<string> list_input_files(const string& dir) {
    vector<string> files;
    string pattern = dir + "\\*.in";
    WIN32_FIND_DATAA fd;
    HANDLE hFind = FindFirstFileA(pattern.c_str(), &fd);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            string name = fd.cFileName;
            size_t pos = name.rfind(".in");
            if (pos != string::npos) {
                files.push_back(name.substr(0, pos));
            }
        } while (FindNextFileA(hFind, &fd));
        FindClose(hFind);
    }
    sort(files.begin(), files.end(), [](const string& a, const string& b) {
        return atoi(a.c_str()) < atoi(b.c_str());
    });
    return files;
}

string escape_json(const string& s) {
    string out;
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:   out += c;
        }
    }
    return out;
}

void output_result(const JudgeResult& r) {
    printf("{\n");
    printf("  \"status\": \"%s\",\n", escape_json(r.status).c_str());
    printf("  \"score\": %d,\n", r.score);
    printf("  \"test_total\": %d,\n", r.test_total);
    if (r.compile_error.empty())
        printf("  \"compile_error\": null,\n");
    else
        printf("  \"compile_error\": \"%s\",\n", escape_json(r.compile_error).c_str());
    printf("  \"time_used\": %d,\n", r.time_used);
    printf("  \"memory_used\": %d,\n", r.memory_used);
    printf("  \"detail\": [\n");
    for (size_t i = 0; i < r.detail.size(); ++i) {
        const auto& d = r.detail[i];
        printf("    {\"case_id\":%d,\"status\":\"%s\",\"time_ms\":%.0f,\"memory_kb\":%lld,\"error_msg\":\"%s\"}",
               d.case_id, escape_json(d.status).c_str(), d.time_ms, d.memory_kb, escape_json(d.error_msg).c_str());
        if (i < r.detail.size() - 1) printf(",");
        printf("\n");
    }
    printf("  ]\n}\n");
    fflush(stdout);
}

bool compile_code(const string& code_file, const string& language,
                  const string& work_dir, string& error) {
    string exe_path = work_dir + "\\program.exe";
    string log_file = work_dir + "\\compile.log";
    string cmd;
    if (language == "c") {
        cmd = "gcc \"" + code_file + "\" -o \"" + exe_path + "\" -O2 -std=c11 -Wall > \"" + log_file + "\" 2>&1";
    } else if (language == "cpp") {
        cmd = "g++ \"" + code_file + "\" -o \"" + exe_path + "\" -O2 -std=c++17 -Wall > \"" + log_file + "\" 2>&1";
    } else {
        return true;
    }
    int ret = system(cmd.c_str());
    if (ret != 0) {
        ifstream f(log_file);
        if (f.is_open()) {
            stringstream ss;
            ss << f.rdbuf();
            error = ss.str();
        } else {
            error = "Compilation failed (exit code " + to_string(ret) + ")";
        }
        return false;
    }
    return true;
}

bool compare_output(const string& out_file, const string& ans_file) {
    ifstream fout(out_file);
    ifstream fans(ans_file);
    if (!fout.is_open() || !fans.is_open()) return false;
    string lo, la;
    while (true) {
        bool ho = (bool)getline(fout, lo);
        bool ha = (bool)getline(fans, la);
        if (!ho && !ha) return true;
        if (!ho || !ha) return false;
        while (!lo.empty() && (lo.back() == ' ' || lo.back() == '\r')) lo.pop_back();
        while (!la.empty() && (la.back() == ' ' || la.back() == '\r')) la.pop_back();
        if (lo != la) return false;
    }
}

void kill_process_tree(DWORD pid) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return;
    PROCESSENTRY32 pe; pe.dwSize = sizeof(pe);
    if (Process32First(snap, &pe)) {
        do {
            if (pe.th32ParentProcessID == pid) {
                HANDLE h = OpenProcess(PROCESS_TERMINATE, FALSE, pe.th32ProcessID);
                if (h) { TerminateProcess(h, 1); CloseHandle(h); }
            }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    HANDLE h = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
    if (h) { TerminateProcess(h, 1); CloseHandle(h); }
}

TestResult run_test(const string& exe_path, const string& input_file,
                     const string& output_file, const string& answer_file,
                     int time_limit_ms, long long memory_limit_kb,
                     const string& language, const string& code_file,
                     const string& work_dir) {
    TestResult res;
    res.case_id = 0;
    res.status = "Accepted";
    res.time_ms = 0;
    res.memory_kb = 0;

    LARGE_INTEGER freq, start_t, end_t;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start_t);

    STARTUPINFOA si; PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si)); ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES;
    si.wShowWindow = SW_HIDE;

    HANDLE hInput = CreateFileA(input_file.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    HANDLE hOutput = CreateFileA(output_file.c_str(), GENERIC_WRITE, FILE_SHARE_READ, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    
    if (hInput == INVALID_HANDLE_VALUE || hOutput == INVALID_HANDLE_VALUE) {
        if (hInput != INVALID_HANDLE_VALUE) CloseHandle(hInput);
        if (hOutput != INVALID_HANDLE_VALUE) CloseHandle(hOutput);
        res.status = "Runtime Error";
        res.error_msg = "Failed to open I/O files";
        return res;
    }
    si.hStdInput = hInput;
    si.hStdOutput = hOutput;
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);

    string cmd_line;
    if (language == "python") {
        cmd_line = "python \"" + code_file + "\"";
    } else if (language == "java") {
        cmd_line = "java -cp \"" + work_dir + "\" Main";
    } else {
        cmd_line = "\"" + exe_path + "\"";
    }
    vector<char> buf(cmd_line.begin(), cmd_line.end());
    buf.push_back('\0');

    if (!CreateProcessA(NULL, buf.data(), NULL, NULL, TRUE,
                        CREATE_NO_WINDOW, NULL, work_dir.c_str(), &si, &pi)) {
        CloseHandle(hInput); CloseHandle(hOutput);
        res.status = "Runtime Error";
        res.error_msg = "Failed to create process";
        return res;
    }
    CloseHandle(hInput); CloseHandle(hOutput);

    DWORD wait = WaitForSingleObject(pi.hProcess, time_limit_ms + 1000);
    QueryPerformanceCounter(&end_t);
    res.time_ms = (double)(end_t.QuadPart - start_t.QuadPart) * 1000.0 / freq.QuadPart;

    if (wait == WAIT_TIMEOUT) {
        kill_process_tree(pi.dwProcessId);
        res.status = "Time Limit Exceeded";
        res.error_msg = "TLE: " + to_string(time_limit_ms) + "ms";
        CloseHandle(pi.hProcess); CloseHandle(pi.hThread);
        return res;
    }

    PROCESS_MEMORY_COUNTERS pmc;
    if (GetProcessMemoryInfo(pi.hProcess, &pmc, sizeof(pmc)))
        res.memory_kb = pmc.PeakWorkingSetSize / 1024;

    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);
    if (exit_code != 0) {
        res.status = "Runtime Error";
        res.error_msg = "Exit code " + to_string(exit_code);
        CloseHandle(pi.hProcess); CloseHandle(pi.hThread);
        return res;
    }
    CloseHandle(pi.hProcess); CloseHandle(pi.hThread);

    if (res.time_ms > time_limit_ms) {
        res.status = "Time Limit Exceeded";
        return res;
    }
    if (res.memory_kb > memory_limit_kb) {
        res.status = "Memory Limit Exceeded";
        return res;
    }
    if (!compare_output(output_file, answer_file)) {
        res.status = "Wrong Answer";
        res.error_msg = "Output mismatch";
        return res;
    }
    res.status = "Accepted";
    return res;
}

int main(int argc, char* argv[]) {
    if (argc < 9) {
        JudgeResult err;
        err.status = "System Error";
        err.compile_error = "Usage: judge.exe <sid> <code_file> <lang> <tl> <ml> <input_dir> <answer_dir> <work_dir>";
        output_result(err);
        return 1;
    }

    int sid              = atoi(argv[1]);
    string code_file      = argv[2];
    string language       = argv[3];
    int tl_ms             = atoi(argv[4]);
    long long ml_kb       = atoll(argv[5]);
    string input_dir      = argv[6];
    string answer_dir     = argv[7];
    string work_dir       = argv[8];

    JudgeResult result;
    result.status = "Accepted"; result.score = 0; result.test_total = 0;
    result.time_used = 0; result.memory_used = 0;

    if (language == "c" || language == "cpp") {
        string ce;
        if (!compile_code(code_file, language, work_dir, ce)) {
            result.status = "Compile Error";
            result.compile_error = ce;
            result.test_total = 0;
            output_result(result);
            return 0;
        }
    }

    vector<string> ids = list_input_files(input_dir);
    result.test_total = (int)ids.size();
    if (ids.empty()) {
        result.status = "System Error";
        result.compile_error = "No test cases";
        output_result(result);
        return 0;
    }

    int max_time = 0, max_mem = 0, passed = 0;
    for (const auto& cid : ids) {
        TestResult tr;
        tr.case_id = atoi(cid.c_str());
        string in  = input_dir  + "\\" + cid + ".in";
        string ans = answer_dir + "\\" + cid + ".out";
        string out = work_dir   + "\\" + cid + ".out";
        string exe = work_dir   + "\\program.exe";

        tr = run_test(exe, in, out, ans, tl_ms, ml_kb, language, code_file, work_dir);

        if (tr.status == "Accepted") passed++;
        max_time = max(max_time, (int)tr.time_ms);
        max_mem  = max(max_mem, (int)tr.memory_kb);

        if (result.status == "Accepted" && tr.status != "Accepted")
            result.status = tr.status;

        result.detail.push_back(tr);
    }

    result.time_used = max_time;
    result.memory_used = max_mem;
    result.score = passed;
    if (passed == (int)ids.size()) result.status = "Accepted";

    output_result(result);
    return 0;
}
