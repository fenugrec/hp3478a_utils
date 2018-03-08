/*
 * (c) fenugrec 2018
 * 
 * GPLv3
 *
 * simple tool to work with cal data dumps from hp3478a units.
 * thanks to eevblog forum users (esp. Sailor) for cal and ROM dumps !
 *
 * limited functionality. see usage (run without args)
 *
 * input format :
 * -b : binary, one byte per nibble, as dumped from GPIB, with or without "0x40" prefix.
 *
 */

#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#include <getopt.h>

#include "stypes.h"

#define CALSIZE 256				//256 nibs total.
#define	CAL_ENTRYSIZE	0x0D	//includes 2-nib checksum
#define	CAL_DATASIZE	0x0B	//11 nibs
#define CAL_ENTRIES	0x12		//18 entries of 13 bytes

/** ret 0 if ok. format : 256 raw bytes */
static int read_bin(FILE *i_file, u8 *dest) {
	rewind(i_file);

	/* load whole ROM */
	if (fread(dest,1,CALSIZE,i_file) != CALSIZE) {
		printf("coudln't read 256 bytes\n");
		return -1;
	}

	return 0;
}


/** parse ASCII into a 256-byte array of nibbles
 * ret 0 if ok.
 *
 * Expected format : one ascii char per expected nibble within [0x40-0x4F]
 * Skips all other bytes.
 */
static int read_ascii(FILE *ifile, u8 *dest) {
	u8 src[CALSIZE * 2];	//assumes max 50% of noise (CR/LF, whitespace etc)
	unsigned cnt = 0;	//pos in dest[]
	int tcur = 0;	//pos in src[]
	int flen;

	flen = fread(src,1,sizeof(src),ifile);
	if (flen < CALSIZE) {
		printf("not enough data, won't work\n");
		return -1;
	}

	while (	(cnt < CALSIZE) &&
			(tcur < flen)) {
		u8 inp = src[tcur++];

		if ((inp < 0x40) || (inp > 0x4F)) {
			continue;
		}
		dest[cnt] = (u8) inp & 0x0F;
		cnt += 1;
	}

	if (cnt != CALSIZE) {
		printf("couldn't identify 256 nibbles !\n");
		return -1;
	}

	return 0;
}


/** just checksums for every entry */
static void test_ck(const u8 *caldata) {
	int recindex;

	for (recindex = 0; recindex < CAL_ENTRIES; recindex += 1) {
		//parse every 13-byte entry.
		u8 sum = 0;
		const u8 *entrydata = &caldata[(1 + (CAL_ENTRYSIZE * recindex))];
		int idx;
		for (idx = 0; idx < CAL_DATASIZE; idx += 1) {
			u8 nib = entrydata[idx] & 0x0F;
			sum += nib;
		}
		sum += (entrydata[CAL_DATASIZE] << 4);	//hi nib of cks byte
		sum += entrydata[CAL_DATASIZE + 1] & 0x0F;	//lo nib of cks byte
		
		if (sum != 0xFF) {
			printf("entry 0x%02X: bad cks (0x%02X)\n", recindex, sum);
		} else {
			printf("entry 0x%02X: OK\n", recindex);
		}
	}	//for
}


/** convert dumped data (with extra "0x40" bits) to raw data;
 * still keeps 1 nibble-per-byte format
*/
static void process(u8 *caldata, FILE *o_file) {
	int idx;

	for (idx = 0; idx < CALSIZE; idx += 1) {
		caldata[idx] &= 0x0F;	//clear higher nib
	}

	if (fwrite(caldata, 1, CALSIZE, o_file) != CALSIZE) {
		printf("problem with fwrite\n");
	}
	return;
}

/** print out raw data for every cal entry */
static void dump_entries(const u8 *caldata) {
	int recindex;

	for (recindex = 0; recindex < CAL_ENTRIES; recindex += 1) {
		//parse every 13-byte entry.
		const u8 *entrydata = &caldata[(1 + (CAL_ENTRYSIZE * recindex))];
		int idx;
		
		printf("entry %02X: ", recindex);
		for (idx = 0; idx < CAL_DATASIZE; idx += 1) {
			printf("%01X ", (unsigned) entrydata[idx] & 0x0F);
		}
		printf("\n");
	}
}

static struct option long_options[] = {
//	{ "debug", no_argument, 0, 'd' },
	{ "help", no_argument, 0, 'h' },
	{ NULL, 0, 0, 0 }
};

static void usage(void)
{
	fprintf(stderr, "usage:\n"
		"***** file input : specify one\n"
		"--ascfile\t-a <filename>\tASCII CAL dump\n"
		"--binfile\t-b <filename>\tbinary CAL dump (one byte per nibble)\n"
		"***** action : specify one\n"
		"\t-t  \ttest checksums of every record\n"
		"\t-p <outfile> \tcreate dump with processed bytes (clear 4 higher bits)\n"
		"\t-d  \tdump raw data for every record\n"
		"");
}


int main(int argc, char * argv[]) {
	char c;

	enum {NIL, TEST, PROCESS, DUMP} action = NIL;

	int optidx;
	FILE *file = NULL;
	FILE *ofile = NULL;
	u8	caldata[CALSIZE];

	printf(	"**** %s\n"
		"**** (c) 2018 fenugrec\n", argv[0]);

	while((c = getopt_long(argc, argv, "dta:b:p:h",
			       long_options, &optidx)) != -1) {
		switch(c) {
		case 'h':
			usage();
			return 0;
		case 'd':
			if (action != NIL) {
				printf("extra / bad arg : %s\n", optarg);
				goto bad_exit;
			}
			action = DUMP;
			break;
		case 't':
			if (action != NIL) {
				printf("extra / bad arg : %s\n", optarg);
				goto bad_exit;
			}
			action = TEST;
			break;
		case 'a':
			if (file) {
				fprintf(stderr, "input file given twice");
				goto bad_exit;
			}
			file = fopen(optarg, "rb");
			if (!file) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			if (read_ascii(file, caldata)) {
				goto bad_exit;
			}
			break;
		case 'b':
			if (file) {
				fprintf(stderr, "input file given twice");
				goto bad_exit;
			}
			file = fopen(optarg, "rb");
			if (!file) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			if (read_bin(file, caldata)) {
				goto bad_exit;
			}
			break;
		case 'p':
			if (ofile) {
				fprintf(stderr, "-p given twice");
				goto bad_exit;
			}
			ofile = fopen(optarg, "wb");
			if (!ofile) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			action = PROCESS;
			break;
		default:
			usage();
			goto bad_exit;
		}
	}
	if ((action == NIL) || !file ||
		((action == PROCESS) && !ofile)) {
		printf("some missing args.\n");
		usage();
		goto bad_exit;
	}

	if (optind <= 1) {
		usage();
		goto bad_exit;
	}

	switch (action) {
	case DUMP:
		dump_entries(caldata);
		break;
	case TEST:
		test_ck(caldata);
		break;
	case PROCESS:
		process(caldata, ofile);
	default:
		break;
	}

	fclose(file);
	if (ofile) fclose(ofile);
	return 0;

bad_exit:
	if (file) {
		fclose(file);
	}
	if (ofile) fclose(ofile);
	return 1;
}
