CC = gcc
BASICFLAGS = -std=gnu11 -Wall -Wextra -Wpedantic
OPTFLAGS = -g
CFLAGS = $(BASICFLAGS) $(OPTFLAGS) $(EXFLAGS)

TGTLIST = hp3478util

all: $(TGTLIST)

hp3478util:	hp3478util.c

clean:
	rm -f *.o
	rm -f $(TGTLIST)
