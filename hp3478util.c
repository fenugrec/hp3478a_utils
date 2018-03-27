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
 * input formats :
 * -a : ASCII, as dumped from GPIB but will skip newlines and whitespace
 * -b : one byte per nibble, as dumped from GPIB, with or without "0x40" prefix.
 *
 */

#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#ifdef __MSDOS__
	typedef unsigned char bool;
#else
	#include <stdbool.h>
#endif

#include <getopt.h>

#include "stypes.h"

#ifndef WITH_GPIB
#define WITH_GPIB	1	//optional; set to 0 to compile without NI driver
#endif

#define CALSIZE 256				//256 nibs total.
#define	CAL_ENTRYSIZE	0x0D	//includes 2-nib checksum
#define	CAL_DATASIZE	0x0B	//11 nibs
#define CAL_ENTRIES	0x13		//19 entries of 13 bytes.

static const int rec_unused[] = {0x05, 0x10, 0x12, -1};	//these entries are always (?) unused and *may* have a bad checksum ?


#if (WITH_GPIB == 1)

#ifdef __MSDOS__
	#include "DECL.H"
#else
	#error GPIB DOS-only for now
#endif


#define DEFAULT_GPIBADDR 23
/* some code here from tekfwtool */
int  Dev;
const char *ErrorMnemonic[] = {"EDVR", "ECIC", "ENOL", "EADR", "EARG",
			       "ESAC", "EABO", "ENEB", "EDMA", "",
			       "EOIP", "ECAP", "EFSO", "", "EBUS",
			       "ESTB", "ESRQ", "", "", "", "ETAB"};
static void GPIBCleanup(int Dev, char* ErrorMsg) {
	printf("Error : %s\nibsta = 0x%x iberr = %d (%s)\n",
	       ErrorMsg, ibsta, iberr, ErrorMnemonic[iberr]);
	if (Dev != -1) {
		printf("Cleanup: Taking device offline\n");
		ibonl (Dev, 0);
	}
	return;
}

#endif




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


/** return true if given index is valid (not unused) */
static bool is_validentry(int recindex) {
	int idx;
	for (idx = 0; rec_unused[idx] != -1; idx++) {
		if (rec_unused[idx] == recindex) return 0;
	}
	return 1;
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
			printf("entry 0x%02X: bad cks (0x%02X)", recindex, sum);
			if (!is_validentry(recindex)) {
				printf(" (unused entry)\n");
			} else {
				printf("\n");
			}
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

/** connect over GPIB and dump CAL SRAM contents */
static void get_caldata(FILE *ofile) {
#if (WITH_GPIB != 1)
	(void) ofile;
	return;
#else
	unsigned idx;
	uint8_t buf[CALSIZE];
	uint8_t cmd[3];

	Dev = ibdev(0, DEFAULT_GPIBADDR, 0, T100s, 1, 0);
	if (ibsta & ERR) {
		printf("Unable to open device\nibsta = 0x%x iberr = %d\n",
		       ibsta, iberr);
		return;
	}

	ibclr(Dev);
	if (ibsta & ERR) {
		GPIBCleanup(Dev, "Unable to clear device");
		return;
	}

	cmd[0]='W';	//yes, W means Read. X is write !
	cmd[2]='\n';
	for (idx=0; idx < CALSIZE; idx++) {
		cmd[1] = (uint8_t) idx;
		ibwrt(Dev, cmd, 3);
		if (ibsta & ERR) {
			printf("wrt problem @ 0x%X\n", idx);
			goto badexit;
		}

		ibrd(Dev, &buf[idx], 1);
		if ((ibcntl != 1) || (ibsta & ERR)) {
			printf("rd problem @ 0x%X\n", idx);
			goto badexit;
		}
		//TODO maybe : validate that rx'd byte is [0x40..0x4F] ?
	}
	if (fwrite(buf, 1, CALSIZE, ofile) != CALSIZE) {
		printf("problem with fwrite\n");
	}
	ibonl(Dev, 0);
	return;

badexit:
	GPIBCleanup(Dev, "");
	ibonl(Dev, 0);
	return;
#endif
}



static struct option long_options[] = {
//	{ "debug", no_argument, 0, 'd' },
	{ "help", no_argument, 0, 'h' },
	{ NULL, 0, 0, 0 }
};

static void usage(void) {
	fprintf(stderr, "usage:\n"
		"***** file input, if applicable\n"
		"--ascfile\t-a <filename>\tASCII CAL dump\n"
		"--binfile\t-b <filename>\tbinary CAL dump (one byte per nibble)\n"
		"***** action : specify one\n"
		"\t-t  \ttest checksums of every record\n"
		"\t-p <outfile> \tcreate dump with processed bytes (clear 4 higher bits)\n"
		"\t-d  \tdump raw data for every record\n"
#if (WITH_GPIB == 1)
		"\t-g <outfile> \tget CAL data from unit over GPIB\n"
#endif
		"");
}


int main(int argc, char * argv[]) {
	char c;

	enum {NIL, TEST, PROCESS, DUMP, GGET} action = NIL;

	bool need_ifile = 0;	//input file needed for some actions only
	bool need_ofile = 0;

	int optidx;
	FILE *file = NULL;
	FILE *ofile = NULL;
	u8	caldata[CALSIZE];

	printf(	"**** %s\n"
		"**** (c) 2018 fenugrec\n", argv[0]);

	while((c = getopt_long(argc, argv, "dta:b:p:g:h",
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
			need_ifile = 1;
			action = DUMP;
			break;
		case 't':
			if (action != NIL) {
				printf("extra / bad arg : %s\n", optarg);
				goto bad_exit;
			}
			need_ifile = 1;
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
			need_ifile = 1;
			need_ofile = 1;
			action = PROCESS;
			break;
		case 'g':
			if (ofile) {
				fprintf(stderr, "-g given twice");
				goto bad_exit;
			}
			ofile = fopen(optarg, "wb");
			if (!ofile) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			need_ofile = 1;
			action = GGET;
			break;
		default:
			usage();
			goto bad_exit;
		}
	}
	if ((action == NIL) ||
		(need_ifile && !file) ||
		(need_ofile && !ofile)) {
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
		break;
	case GGET:
		get_caldata(ofile);
		break;
	default:
		break;
	}

	if (file) fclose(file);
	if (ofile) fclose(ofile);
	return 0;

bad_exit:
	if (file) fclose(file);
	if (ofile) fclose(ofile);
	return 1;
}
