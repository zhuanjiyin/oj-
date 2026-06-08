# OJ Judge Makefile
CXX = g++
CXXFLAGS = -O2 -std=c++17 -static -Wall
LDFLAGS = -lpsapi

judge.exe: judge.cpp
	$(CXX) $(CXXFLAGS) -o judge.exe judge.cpp $(LDFLAGS)

clean:
	del /f judge.exe 2>nul || rm -f judge.exe

