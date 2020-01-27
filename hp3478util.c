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

#include <assert.h>
#include <errno.h>
#include <math.h>
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
// structure of cal data :
#define CAL_OFFSETSIZE	0x06	//6 first nibs : BCD offset value


struct gain_test {
	double gain;
	u8 gstr[5];
};

static const struct gain_test gtests[] = {
								{1.049000, {5,0xF,0,0,0}},
								{1.000006, {0,0,0,0x1,0xC}},	//this one "works" but should be encoded as 00006, not 0001C
								{0.911112, {8,8,8,8,8}},
								{1.077777, {7,7,7,7,7}},
								{1.012906, {1,3,0xF,1,0xC}},	//same. how does the firmware come up with this
								{0.988906, {0xf,0xf,0xf,1,0xc}}
							};
#define NUM_GTESTS (sizeof(gtests)/sizeof(struct gain_test))

static const int rec_unused[] = {0x05, 0x10, 0x12, -1};	//these entries are always (?) unused and *may* have a bad checksum ?

static const char *calentry_names[] = {
	"30 mV DC",	//entry 0
	"300 mV DC",
	"3 V DC",
	"30 V DC",
	"300 V DC",
	"(Not used)",	//entry 5
	"ACV",
	"30 Ohm 2W/4W",
	"300 Ohm 2W/4W",	//entry 8
	"3 KOhm 2W/4W",
	"30 KOhm 2W/4W",
	"300 KOhm 2W/4W",
	"3 MOhm 2W/4W",
	"30 MOhm 2W/4W",
	"300 mA DC",	//entry 0x0E
	"3A DC",
	"(Not used)",	//entry 0x10
	"300 mA/3A AC",
	"(Not used)",
};



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
			printf("entry 0x%02X (%s): bad cks (0x%02X)",
					recindex, calentry_names[recindex], sum);
			if (!is_validentry(recindex)) {
				printf(" (unused entry)\n");
			} else {
				printf("\n");
			}
		} else {
			printf("entry 0x%02X: OK (%s)\n", recindex, calentry_names[recindex]);
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

/** calculate gain correction factor
 *
 * based on 5-char gain string
*/
static double getgain(const u8 *gstr) {
	double gain = 1.0;
	double mult = 0.01;
	unsigned cur;
	u8 dig;

	for (cur = 0; cur <= 4; cur += 1) {
		dig = gstr[cur] & 0x0F;
		if (dig & 0x08) {
			// digit is negative, i.e. 0x0C is -4
			gain += (dig-16) * mult;
		} else {
			gain += dig * mult;
		}
		mult = mult / 10;
	}
	return gain;
}



/** incr/decrement the digit #_pos, correcting all digits towards the left
 * if add : incr
 * if !add : decr
 * caller must have range-checked the input
 */
static void adjusticate(int *digits, bool add, unsigned pos) {
	assert((pos >= 1) && (pos <= 5));

	unsigned cur;
	int adj;
	if (add) {
		adj = 1;
	} else {
		adj = -1;
	}

	for (cur = pos; cur >= 1; cur -= 1) {
		int dig = digits[cur - 1];
		dig += adj;

		if (dig < -8) {
			//borrow : continue looping but with "-1" as next operation
			assert(cur != 1);	//can't happen !
			adj = -1;
			dig = (10 - dig);
		} else if (dig > 7) {
			//carry: continue loop with "+1" for next op
			assert(cur != 1);	//can't happen !
			adj = 1;
			dig = dig - 10;
		} else {
			//digit within bounds : add 0 on next
			adj = 0;
		}
		digits[cur - 1] = dig;
	}
}

#define MAX_GAIN ((double) 1.077777)
#define MIN_GAIN ((double) 0.911112)
/** gain must be given as the ratio of cal_reading / raw_reading
 * gain constant written to gstr[] as binary values 0-F (not ASCII)
 *
 *
 */

static void encode_gain(u8 *gstr, double gain) {
	memset(gstr, 0, 5);
	int k[5] = {0};	//digit K_values

	long kf_int = (1.0E6 * gain) - 1E6; // otherwise, problems with the last digit because of precision
	long divider = 1E4L;


	if ((gain > MAX_GAIN) || (gain < MIN_GAIN)) {
		printf("gain out of range, setting to 1.0\n");
		return;
	}

	unsigned cur;	//current digit

	for (cur = 1; cur <= 5; cur += 1) {
		int tmp = kf_int / divider;	//get digit

		//printf("kf_int : %ld,", kf_int);
		//printf("digit %u: %d\n", cur, tmp);

		//can't just toss the digit in the string : need to adjust.
		
		if (tmp >= 8) {
			//crap, need to adjusticate.
			assert(cur != 1);	//can't adjust on this digit !
			k[cur - 1] = tmp - 10;
			adjusticate(k, 1, cur - 1);
		} else if (tmp <= -9) {
			assert(cur != 1);	//can't adjust on this digit !
			k[cur - 1] = 10 + tmp;
			adjusticate(k, 0, cur - 1);
		} else {
			//valid digit as-is
			k[cur - 1] = tmp;
		}
		
		//ok, for next loop : drop current digit and left shift.
		kf_int -= (tmp * divider);
		divider /= 10;
	}

	// all done, now convert k_values to proper digits 0x0 - 0xF
	for (cur = 1; cur <= 5; cur += 1) {
		int k_value = k[cur - 1];
		if (k_value < 0) {
			gstr[cur - 1] = 0x10 + k_value;
		} else {
			gstr[cur - 1] = k_value;
		}
	}
	return;
}

/* ret 1 if ok */
static bool selftest(void) {
	u8 gstr[5];

	unsigned idx;

	for (idx = 0; idx < NUM_GTESTS; idx += 1) {
		double realgain, tmpgain;
		realgain = gtests[idx].gain;
		long intgain = round(1.0E6 * realgain);
		
		//test roundtrip conversion
		encode_gain(gstr, realgain);
		tmpgain = getgain(gstr);
		long itmpgain = round(1.0E6 * tmpgain);
		//if (memcmp(gstr, gtests[idx].gstr,5)) {
		//memcmp() is too strict (see comments in test cases)
		if (intgain != itmpgain) {
			printf("test %u failed: calcgain=%f (%ld), g=%f (%ld)\n",
					idx, tmpgain, itmpgain, realgain, intgain);
			unsigned cur;
			for (cur=0; cur <= 4; cur++) {
				printf("%X:%X\n", gstr[cur], gtests[idx].gstr[cur]);
			}
			return 0;
		}
	}
	return 1;
}

/** print out raw data for every cal entry */
static void dump_entries(const u8 *caldata) {
	int recindex;

	//header columns
	printf("entry #\toffset\t(rawgain)\tgain\trange\n");
	for (recindex = 0; recindex < CAL_ENTRIES; recindex += 1) {
		//parse every 13-byte entry.
		const u8 *entrydata = &caldata[(1 + (CAL_ENTRYSIZE * recindex))];
		int idx;

		printf("%02X\t", recindex);
		for (idx = 0; idx < CAL_OFFSETSIZE; idx += 1) {
			printf("%01X", (unsigned) entrydata[idx] & 0x0F);
		}
		printf("\t");
		for (; idx < CAL_DATASIZE; idx += 1) {
			//print raw gain string
			printf("%01X", (unsigned) entrydata[idx] & 0x0F);
		}
		printf("\t%1.6f", getgain(&entrydata[CAL_OFFSETSIZE]));
		printf("\t%s\n", calentry_names[recindex]);
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

	printf(	"************ hp3478util, "
		"(c) 2018-2020 fenugrec ************\n");

	if (!selftest()) {
		return -1;
	}

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
