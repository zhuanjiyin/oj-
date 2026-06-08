# judge/Makefile — C++ 编译脚本

## 文件定位
提供便捷的 make 命令编译判题程序，等价于手动执行：
`ash
g++ -o judge.exe judge.cpp -static -O2 -lpsapi
`

## 内容
`makefile
all:
	g++ -o judge.exe judge.cpp -static -O2 -lpsapi

clean:
	del judge.exe
`

## 使用
`ash
cd judge
make          # 编译
make clean    # 删除编译产物
`

> Windows 环境下需安装 MinGW 的 mingw32-make 或 GNU Make。