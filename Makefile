CC=gcc

CFLAGS=-g

EXE=8080

$(EXE): emulator.o
	$(CC) -o $@ $(CFLAGS) $^


emulator.o: emulator.c
	$(CC) $(CFLAGS) $(CPPFLAGS) -o $@ -c $^

clean:
	-rm *.o
	-rm $(EXE)


