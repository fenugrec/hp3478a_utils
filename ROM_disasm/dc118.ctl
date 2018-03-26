; test control file for d48.
; intent is to add symbols and labels in here iteratively so the listing can be
; re-generated automatically.
; The advantage of this is mainly when identifying and renaming a function; instead of needing
; a manual search + replace, this only requires to add a "L" directive .
; The downside is that adding disassembly comments is slightly more tedious; edits to the
; output of course are clobbered on the next re-generation.
;
; command : d48 -d -n -b <filename>
; (-n gives 0x.. constants instead of ..h)



;L label
;C code
;S symbol
;! inline comment
;

L 0   reset
L 3   intvec
L 7   tcvec
C 0
C 3
C 7

L 1000   alt_reset
L 1003   alt_intvec
L 1007   alt_tcvec
C 1000
C 1003
C 1007

;*************
;functions/locs with >95% confidence
L 00BA GPIB_trig
L 0200 check_calentry
! 0200 i: a=calid. verify checksum of entry
l 0204 check_calentr_a
! 0204 verify checksum at a=addr
! 043b reassemble 6 nibs from CALRAM
! 0506 (movx = from CALRAM)
l 055c isol_synctx?
l 0600 isol_syncrx?
l 0800 set_A12_ret
l 086f keypad_checkloop?
L 0B06 BCDstuff_0B06
L 0D6A BCDstuff_0D6a
! 0d6a not sure. i: r0=caladdr, r1=&dest[3], 
L 0d82 readcal_daa
! 0D82 do some BCD adj on read nib. i: r0=addr--; o: ret a

L 0E00 getaddr
! 0e00 getaddr(idcal) with tableread
l 0e0d ret_movp
L 0f09 clr_0f09
! 0f09 clear (r2) bytes @ r0
L 0f0f cal_cpy5
! 0f0f i:( r0 = src, r1 = dest) . Copy 5 bytes
L 0f18 cal2C_add
! 0f18 BCD add : cal58[] += cal2C[]

l 0f4a write_CALcks
! 0f4a i: (a= id)
l 0f4c write_CALcks_noget
! 0f4c (a=caladdr)
l 0f65 write_calRAM
! 0f65 a = val, r1 = addr; o: flags

l 10cb GPIB_SPstatus
! 10cb missing xrefs due to mb0 not assumed
l 1200 GPIB_intparsage
! 1200 missing xrefs due to mb0
! 1265 range check on received data : alphanum, digits, and \r\n
l 1287 GPIB_RXbad
! 1287 alphab out of range / other stuf?
l 128f GPIB_reparse_ISR1
! 1294 rx E [0x0E, 0x2F]
l 12aa GPIB_RXhidig
! 12aa hi digit (0x38-0x3F), a = byte - 0x38
l 12b0 GPIB_RXplus
l 12b7 GPIB_RXneg
l 12c0 GPIB_RXdigit
! 12c0 a = rxbyte - 0x30.
l 12c8 GPIB_RXalpha
! 12c8 a = rxb - 0x41
l 12f0 GPIB_ISR1_BO
L 1600 dip_parse
! 1650 read 50/60Hz switch
l 16c0 clr_ram26_b6_0
l 1d15 ascii_getsign
! 1d15 (a=val, r1=&dest++)

;**** disp stuff
l 1906 disp_setpwo
! 1906 if (!f1) : tog sync and set pwo
l 1917 disp_init?
l 1937 disp_writeannuns?
l 194a disp_write12h
! 194a write 12 MSnibs from from iRAM[4F] backwards : iRAM[44..4F])
l 195e disp_write12l
! 195e write 12 LSnibs from from iRAM[4F] backwards : iRAM[44..4F])
l 1971 disp_clrpwo
l 197a disp_sendib
! 197a i: a=instr byte
l 1993 disp_send8d
! 1993 send 8 data bits. a=data
l 1997 disp_send4d
! 1997 send 4 data bits (i: a & 0x0F)
l 1a00 pulse_dispck44
! 1a00 pulse clk1,clk2 0x44 cycles
l 1a02 pulse_dispck_r2
l 1a0d pulse_dispck2
l 1a0f pulse_dispck

;**** rom checksum stuff
l 169e romck_prepare
l 16e4 romck_flip0
l 06e6 romck_flipped0
l 00fc romck_00fc
l 02fc romck_02fc
l 04fc romck_04fc
l 06fd romck_06fd
l 08fc romck_08fc
l 0afc romck_0afc
l 0cfc romck_0cfc
l 0efc romck_0efc
l 10fc romck_10fc
l 12fc romck_12fc
l 14fc romck_14fc
l 16fd romck_16fd
l 18fc romck_18fc
l 1afc romck_1afc
l 1cfc romck_1cfc
l 1efc romck_1efc
! 1f05 ret to 16a5
! 1fff probable dummy byte to bring checksum == 0 (see romck_prepare)

;****** short return xrefs
; just clarifies disasm so a distant "jcc <x>" is obviously a jump-to-exit
L 00fb retr_00fb
L 0158 ret_0158
L 021e retr_021e
L 05b7 retr_05b7
L 0b36 retr_0b36
L 0dc4 retr_0dc4
L 0dd4 retr_0dd4
L 0f64 retr_0f64
L 0f6f retr_0f6f
L 10c0 retr_10c0
L 10f5 retr_10f5
L 112d retr_112d
L 1196 retr_1196
L 1232 retr_1232
L 16bb retr_16bb
L 16e7 ret_16e7
L 1739 retr_1739
L 17fb retr_17fb
L 1889 retr_1889
L 1949 retr_1949


;*************
;locs with low confidence
l 0106 isol_dly
! 0106 approx 10-15ms ? rough calc
L 0313 cmd_0313?	; goes with sub 0DC5
L 032D cmd_032D?	;
L 037B cmd_037B?

L 0Dc5 sub_0dc5
! 0dc5 i: r2=&src in 0x300 (PC & 0xFF). copy to RAM[0x44+idx] until src[idx]==0 ?

L 0f28 cal58_sub2C
! 0f28 cal58 -= cal2C ? not sure
l 11af sub_11af
! 11af called with mb0
l 11cd sub_11cd
l 11d6 sub_11d6
l 1339 GPIB_sendreading?

l 15bb sub_15bb
l 17e9 sub_17E9
! 17e9 get iRAM[2A], if < 0x3F then ret a |= 0x40 => check MTA/MLA ?
L 19AF GPIB_getSPSTAT?
! 1f8e r7=rxbyte


;*************
;data / ignore sections
l 0306 tbl_0306
B 0306-0387
b 0e0f-0e40
i 0f70-0fff

b 10c1-10ca
l 1306 tbl_1306
b 1306-132e