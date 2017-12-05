CC=gcc
CXX=g++

CFLAGS=-g

EXE=8080

#CATCH_INCLUDE_DIR=../Catch2/include
OBJS=emulator.o cpu.o machine.o debug.o


$(EXE): $(OBJS)
	$(CC) -o $@ $(CFLAGS) $^ -lreadline

utests: tests.cpp cpu.o machine.o debug.o
	$(CXX) -std=c++11 -o utests $^ -lreadline

emulator.o: emulator.c cpu.h
cpu.o: cpu.c cpu.h
machine.o: machine.c machine.h cpu.h
debug.o: debug.c debug.h cpu.h machine.h

%.o: %.c
	$(CC) -c -o $@ $< $(CPPFLAGS) $(CFLAGS)

clean:
	-rm *.o
	-rm $(EXE)


