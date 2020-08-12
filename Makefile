CC = gcc
BASICFLAGS = -std=gnu11 -Wall -Wextra -Wpedantic
OPTFLAGS = -g
EXFLAGS = -DWITH_GPIB=0
CFLAGS = $(BASICFLAGS) $(OPTFLAGS) $(EXFLAGS)
LDLIBS = -lm

TGTLIST = hp3478util

all: $(TGTLIST)

hp3478util:	hp3478util.c

clean:
	rm -f *.o
	rm -f $(TGTLIST)
