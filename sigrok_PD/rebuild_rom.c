/*
 * (c) fenugrec 2018
 *
 * GPLv3
 *
 * temporary tool to reconstruct a ROM dump based on a logic analyzer capture of
 * the CPU's external memory accesses.
 *
 * Takes one input file generated from sigrok-cli with the mcs48 packet decoder.
 *
 *
 */

#include <ctype.h>	//toupper
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#include <getopt.h>

#include "..\stypes.h"


#define DUMP_MAXSIZE	1*1024*1024UL	//arbitrary
#define ROM_MAXSIZE	64*1024UL


struct dumpfile {
	u8 *data;
	u32 siz;
};

// hax, get file length but restore position
static u32 _flen(FILE *hf) {
	long siz;
	long orig;

	if (!hf) return 0;
	orig = ftell(hf);
	if (orig < 0) return 0;

	if (fseek(hf, 0, SEEK_END)) return 0;

	siz = ftell(hf);
	if (siz < 0) siz=0;
		//the rest of the code just won't work if siz = UINT32_MAX
	#if (LONG_MAX >= UINT32_MAX)
		if ((long long) siz == (long long) UINT32_MAX) siz = 0;
	#endif

	if (fseek(hf, orig, SEEK_SET)) return 0;
	return (u32) siz;
}


/** ret new u8 buffer
 *
 * @param dumpfil : binary file produced by sigrok-cli  */
struct dumpfile *load_dump(FILE *dumpfil) {
	u32 file_len;
	u8 *src;
	struct dumpfile *dpf;

	dpf = malloc(sizeof(struct dumpfile));
	if (!dpf) {
		printf("malloc choke\n");
		return NULL;
	}

	rewind(dumpfil);
	file_len = _flen(dumpfil);
	if ((!file_len) || (file_len > DUMP_MAXSIZE)) {
		printf("huge or bad file (length %lu)\n", (unsigned long) file_len);
		free(dpf);
		return NULL;
	}

	src = malloc(file_len);
	if (!src) {
		printf("malloc choke\n");
		free(dpf);
		return NULL;
	}

	if (fread(src,1,file_len,dumpfil) != file_len) {
		printf("trouble reading\n");
		free(dpf);
		free(src);
		return NULL;
	}

	dpf->data = src;
	dpf->siz = file_len;
	return dpf;
}


void close_dump(struct dumpfile *dpf) {
	if (dpf->data) {
		free(dpf->data);
	}
	free(dpf);
	return;
}

#define REC_SIZE 3	//2 bytes for addres, 1 for data
static void extract_romdata(FILE *ifile, FILE *ofile, unsigned size) {
	struct dumpfile *dpf;
	u8 *rom;

	u32 cur;
	unsigned count = 0;	//how many bytes were captured

	dpf = load_dump(ifile);
	if (!dpf) return;

	rom = malloc(size);
	if (!rom) {
		printf("malloc choke\n");
		close_dump(dpf);
		return;
	}
	/* init ROM to "blank" 0xFF */
	memset(rom, 0xFF, size);

	for (cur=0; cur < dpf->siz; cur += REC_SIZE) {
		//get record
		u16 addr;
		u8 data;
		addr = ((dpf->data[cur] << 8) | dpf->data[cur + 1]);
		data = dpf->data[cur + 2];
		if (addr >= size) {
			printf("address 0x%04X out of bounds @ 0x%lX! aborting\n",
					(unsigned) addr, (unsigned long) cur);
			break;
		}
		//check if ROM already is non-empty and different : problem !
		if ((rom[addr] != 0xFF) && (rom[addr] != data)) {
			printf("data collision @ %04X: had %02X,got %02X\n",
					(unsigned) addr, (unsigned) rom[addr], (unsigned) data);
			continue;
		}
		rom[addr] = data;
		count++;
	}

	if (count != size) {
		printf("didn't get whole ROM ? got %X, wanted %X\n", count, (unsigned) size);
	}

	if (fwrite(rom, 1, size, ofile) != size) {
		printf("fwrite problem\n");
	}

	close_dump(dpf);
	free(rom);
	return;
}


/* htoi : copied from freediag but without octal
 * atoi pulls in strtol() which is very generic
 * and also very big
 */
static int htoi(const char *buf) {
	/* Hex text to int */
	int rv = 0;
	int base = 10;
	int sign=0;	//1 = positive; 0 =neg

	if (*buf != '-') {
		//change sign
		sign=1;
	} else {
		buf++;
	}

	if (*buf == '$') {
		base = 16;
		buf++;
	} else if (*buf == '0') {
		buf++;
		if (tolower(*buf) == 'x') {
			base = 16;
			buf++;
		}
	}

	while (*buf) {
		char upp = toupper(*buf);
		int val;

		if ((upp >= '0') && (upp <= '9')) {
			val = ((*buf) - '0');
		} else if ((upp >= 'A') && (upp <= 'F')) {
			val = (upp - 'A' + 10);
		} else {
			return 0;
		}
		if (val >= base) { /* Value too big for this base */
			return 0;
		}
		rv *= base;
		rv += val;

		buf++;
	}
	return sign? rv:-rv ;
}

static struct option long_options[] = {
//	{ "debug", no_argument, 0, 'd' },
	{ "help", no_argument, 0, 'h' },
	{ NULL, 0, 0, 0 }
};

static void usage(void) {
	fprintf(stderr, "usage:\n"
		"\t-i\tfile input, produced by sigrok-cli\n"
		"\t-o\treconstructed ROM dump\n"
		"***** optional\n"
		"\t-s <size>\tsize of expected ROM dump; default 8kB\n"
		"");
}


int main(int argc, char * argv[]) {
	char c;

	int optidx;
	FILE *file = NULL;
	FILE *ofile = NULL;
	unsigned size = 8*1024;

	printf(	"**** %s\n"
		"**** (c) 2018 fenugrec\n", argv[0]);

	while((c = getopt_long(argc, argv, "i:o:s:h",
			       long_options, &optidx)) != -1) {
		switch(c) {
		case 'h':
			usage();
			return 0;
		case 'i':
			if (file) {
				fprintf(stderr, "input file given twice");
				goto bad_exit;
			}
			file = fopen(optarg, "rb");
			if (!file) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			break;
		case 'o':
			if (ofile) {
				fprintf(stderr, "output file given twice");
				goto bad_exit;
			}
			ofile = fopen(optarg, "wb");
			if (!ofile) {
				fprintf(stderr, "fopen() failed: %s\n", strerror(errno));
				goto bad_exit;
			}
			break;
		case 's':
			size = (unsigned) htoi(optarg);
			break;
		default:
			usage();
			goto bad_exit;
		}
	}
	if (!file || !ofile ||
		!size || (size > ROM_MAXSIZE)) {
		printf("missing / bad args.\n");
		usage();
		goto bad_exit;
	}

	extract_romdata(file, ofile, size);

	if (file) fclose(file);
	if (ofile) fclose(ofile);
	return 0;

bad_exit:
	if (file) fclose(file);
	if (ofile) fclose(ofile);
	return 1;
}
