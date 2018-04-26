CC = gcc
BASICFLAGS = -std=gnu11 -Wall -Wextra -Wpedantic
OPTFLAGS = -g
CFLAGS = $(BASICFLAGS) $(OPTFLAGS) $(EXFLAGS)

TGTLIST = rebuild_rom

all: $(TGTLIST)

rebuild_rom:	rebuild_rom.c

clean:
	rm -f *.o
	rm -f $(TGTLIST)
