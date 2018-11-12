; Control file for d48 disassembler.
;
; intent is to add symbols and labels in here iteratively so the listing can be
; re-generated automatically.
;
; Pros:
; - main: when identifying and renaming a function; instead of needing
; a manual search + replace, this only requires to add an "L" directive, and regenerate.
; - less messy when developing d48 and trying different tweaks.
; - easier to 'diff' when marking areas as data
;
; Cons:
; Commenting disassembly through this file is more tedious; edits to the
; generated output are of course clobbered on the next re-generation.
;
; command : d48 -d -n -b <filename>
; (-n gives 0x.. constants instead of ..h)


;********* command prefixes:
;L label
;C code
;S symbol
;! inline comment
;B data byte (or array)
;M force mb0/mb1 bank

;****** general stuff

# 0
# 0 Do not edit this .d48 file, as changes will be lost when re-running d48 !
# 0

L 0   reset
L 3   intvec
L 7   tcvec
! 7  tcvec and alt_tcvec are identical
! 0c push a
! die
! 021 reload WDTcnt
! 024 pop a
C 0
C 3
C 7

# 1000
# 1000 This 0x1000-0x1FFF area is only accessible when address bit 12 (A12,
# 1000 software-controlled by pin P26) is high.
# 1000

L 1000   alt_reset
L 1003   alt_intvec
L 1007   alt_tcvec
! 1007  tcvec and alt_tcvec are identical
C 1000
C 1003
C 1007

;************* global iRAM vars
; S doesn't work great for iRAM: it replaces "orl" / "anl" instances too
;s 40 mode40

;************* functions/locs with >95% confidence

L 0200 check_calentry
! 0200 i: a=calid. verify checksum of entry
l 0204 check_calentr_a
! 0204 verify checksum at a=addr
! 043b reassemble offset[6] from CALRAM
# 04ad parse cal gain constant
# 0506 this section seems to parse the cal (offset?) constant,
# 0506 if the first digit is 8 or 9, the # is negative ?
l 0506 readcal_r7_sign?
! 0506 (movx = from CALRAM)
! 050d if (a > 8) ?
l 054e readcal_bot_r6
! 067c test calRAM read/write ?
l 0687 CAL_test
l 16e9 bridge_CAL_test
# 069f: 0xc5= UNCALIBRATED
# 06b7: AD TEST FAIL
# 06bb: AD LINK FAIL
# 105d: UC ROM FAIL
# 10a5: UC RAM FAIL
# 0a3b update cal offset[6] + checksum
# 0a68 read cal offset[6] to iRAM[2C], PBCD
# 0aa5 update cal gain[5] + checksum
l 0ab4 print_VALUEERR
l 0ab8 print_CALRAMFAIL
l 08f8 print_ENABLECAL
l 0946 print_CALIBRATING
l 0ac4 print_CALFINISHD
l 0aca print_CALINVZERO
# 0af0 print_ENABLECAL
l 0dd5 print_ACIVALERR
l 1070 init_idata
l 10aa syserr_a
l 10a9 syserr_r2

l 055c isol_synctx
l 0562 isol_synctx2
! 055c sends 2 bytes from iRAM[0x3F?], MSB first, clr F1 if ok
! 0569 set P27, wait for T=1
! 0577 clr P27, wait for T=0
! 059b do_stopbit
l 0600 isol_syncrx
! 0600 writes 4 bytes to iRAM[0x2D]
l 061A rx_4byteloop
l 061D rx_8bitloop
! 0651 read keypad (useless?)
! 0659 get DIPswitch (useless?)
l 06bb seterr_AD_LINK
l 0800 set_A12_ret
! 0800 set A12; call 1807, then ret to orig (block0)
l 0866 kp_call_a12
l 086f keypad_checkloop1
! 086f: see also keypad loop @ 1118 !
l 0872 kp_initloop
l 0876 kp_loop_top
! 0879 r7 = p1_read
l 0887 key_pressed?
! 088c (r7 = p1)
l 08a0 key_up?
l 08a8 key_down?
l 08bd keypad_a12ret
! 08c5 j if no keys pressed
l 08f6 keyparse_cont1
l 0938 key_sgltrig?
l 0acc call_printcal_r2
l 0aee keyparse_cont1b
L 0B06 BCDstuff_0B06
! 0CAC write full entry
# 0cbd 0xCE = &entry0F_gain[5] (entry 0x0F : 3A DC)
# 0d33 0x18 = &entry01_gain[5] (entry 01 : 300mV DC)
l 0d68 CAL_ACI_fail
L 0D6A BCDstuff_0D6a
! 0d6a not sure. i: r0=caladdr, r1=&dest[3], 
L 0d82 readcal_daa
! 0D82 do some BCD adj on read nib. i: r0=addr--; o: ret a
l 0d97 BCD_div?
# 0d97 fixed cal58 /= (cal2C * 10) ???
# 0da2 loop 8 times
# 0da6 loop 0x0A times
# 0d4b read offset from entry 6 @ 0x4F (ACV)
# 0D53 write to entry 0x11 @0xDE (AC I)
! 0D9B 0x44[0..7]=0

L 0E00 getaddr
! 0e00 getaddr(idcal) with tableread
l 0e0d ret_getaddr
L 0f09 memset0_r2
! 0f09 clear (r2) bytes @ r0
L 0f0f cal_cpy5_to_r1
# 0f0f i:( r0 = src, r1 = dest) . Copy 5 bytes
L 0f18 cal58_add2C
# 0f18 BCD add : cal58[] += cal2C[]

l 0f4a write_CALcks
! 0f4a i: (a= id)
l 0f4c write_CALcks_noget
! 0f4c (a=caladdr)
l 0f65 write_calRAM
! 0f65 a = val, r1 = addr; o: flags


l 1118 kp_check2_init
l 111c kp_loop2_top
l 112e kp_keypressed2
! 112e (r7 = p1)
l 114b key_LCL_or_SRQ
! 114d : here, iterate through tbl_keys @ 1320 !
l 1157 key_found
! 1157 when found, r0 = 0x20 + key_id


l 15a8 func_change
# 15a8 i: a = new mode (1 = DCV, 2=ACV, 2W,etc..)

;************* GPIB stuff
L 00BA GPIB_trig
l 0400 GPIB_SPstuff
L 1026 GPIB_DevClr
l 10cb GPIB_SPstat_r7
l 1200 GPIB_intparsage
! 1265 range check on received data : alphanum, digits, and \r\n
l 1287 GPIB_RXbad
! 1287 alphab out of range / other stuf?
l 128f GPIB_reparse_ISR1
l 1294 GPIB_RXother
! 1294 rx E [0x0E, 0x2F]
l 12aa GPIB_RXhidig
! 12aa hi digit (0x38-0x3F), a = byte - 0x38
l 12b0 GPIB_RXplus
l 12b7 GPIB_RXneg
l 12c0 GPIB_RXdigit
! 12c0 a = rxbyte - 0x30.
l 12c8 GPIB_RXalpha
! 12c8 a = rxb - 0x41
l 1251 GPIB_ISR1_BI
l 12f0 GPIB_ISR1_BO
l 1339 GPIB_sendreading?
L 19AF GPIB_getSPSTAT?
! 00BC GPIB_CS
! 00C2 AUXMODE=4 trig
! 00C4 GPIB_release
! 0402 GPIB_CS
! 040F SPSTATUS
! 0411 SPMODE
! 065C GPIB_CS (for init)
! 0662 AUXMODE = 02 creset
! 0664 AUXMODE=0 pon
! 0669 ADDRMODE = 80 tonly
! 066F DOUT = 0
! 0672 SPMODE = 0
! 0673 a=SPSTAT
! 0676 GPIB_release
! 10DA SPSTATUS
! 10DC SPMODE = a
! 10e3 SPSTAT
! 10f4 SPMODE
! 118C GPIB_CS for RTLstuff
! 1192 AUXMODE = 0D setRTL
! 1195 AUXMODE = 05 clrRTL
! 11a0 calld with mb0
! 1205 get ADR0 ?
! 1206 check INT bit
! 120A if (ADR0.INT == 1)
! 120C get ISR2
! 1210 ISR2.ADSC
! 1212 ISR2.REMC
! 1214 ISR2.SPC
! 1218 get ISR1
! 121D ISR1.BI
! 121F ISR1.BO
! 1221 ISR1.DEC
! 1223 ISR1.GET
! 1225 clr BI, DEC, APT
! 122F read ADDR0 ?
! 1230 check INT bit
! 124a SPSTATUS
! 1251 ISR1.BI
! 1253 get DIN
! 1254 r7 = DIN
! 1258 check ISR2s.REM ?
! 125C GPIB data_in while remote
! 1261 a = DIN
! 1267 - 'z' +1
! 126B 'a'
! 126D discard lowercase ?
! 126F 'Z'+1
! 1273  'A'
! 1277  '9' -1
! 127B  '0'
! 127F  0x0E
! 1283  0x09
! 128F (get ISR1)
! 1295 '-'
! 129A ','
! 129F '+'
! 12A4 ' '
! 12AA check if 0x3B ';'
! 12B0 a = iRAM[0x2A] ?
! 12c6 (jmpindex = iRAM[r0])
! 12C9 iRAM[2A]
! 12DF a = GPIB_alphatbl[a] (tbl @ 1306)
l 12e9 do_GPIBjmp
! 12E9 (a = iRAM[2A],r7 = DIN)
l 12f2 GPIB_ISR1_DEC
l 12f4 GPIB_ISR1_GET
l 132F GPIB_BOh
! 134F GPIB_CS
! 135E ascii_digitstuff
! 1362  '.'
! 13A1 AUXMODE=06 sendEOI
! 13AB DOUT = data
# 13bf sketch : we got here from "jz	X13bf",
# 13bf so the jz below is unconditional !
l 1400 GPIB_jmp1
! 1400 i : r0=&val (iRAM[24] always?)
l 1454 jmp_rxbad
! 1491 SPSTATUS
! 14c7 read CAL!
! 14E1 GPIB_release
! 14E3 GPIB_CS
l 155c GPIB_init
! 1565 check "power-on SRQ" dipswitch
! 156d GPIB_CS
! 1572 AUXMODE = creset
! 1577 ISR1enable = GET, DEC, BO, BI
! 157b ISR2en = SPC, LLOC, REMC, ADSC
! 157e SPMODE = 0
! 1583 AUXMODE : set clock
! 1586 AUXRA = 0
! 1589 AUXRB = RFD holdoff GET+DEC
! 158e GPIB_CS
! 1592 AUXMODE : pon
! 159d ISR2
! 15a3 AUXMODE : release RFDhold
! 15ed AUXMODE : release RFDhold
# 1607 print HPIB ADRS TO
! 1617 GPIB_CS for setaddr
! 161D if addr > 0x1f?
! 1621 ADRMODE = 1 (prim-prim)
! 1626 ADR1 = 0, DT + DL
! 1628 ADR0 = DIPaddr
! 1645 DIP addr > 0x1f
! 1647 ADRMODE = tonly
! 1650 read 50/60Hz switch. GPIB_release
! 1652 DIPadd_sel
! 1654 get DIP addr again
! 1656 keep 50/60Hz bit
! 17e9 get iRAM[2A], if < 0x3F then ret a |= 0x40 => check MTA/MLA ?
! 19B1 SPSTAT
! 19B3 Carry = SRQS
! 19b9 get ADRS
! 1E13 still mb0
! 1E20 GPIB_CS
! 1E26 AUXMODE = TRIG
! 1E2A a = ADDRSTAT?
# 1e38 sketch again : orl forces NZ, so this is unconditional !
! 1F05 ret to 16a5 !
! 1F8E r7 = rxbyte


! 155f get DIP
L 1600 dip_parse
! 160F DIP_sel
! 1611 get DIP setting
! 1650 read 50/60Hz switch
l 16c0 clr_ram27_bit7
l 18ad render_reading
l 18dc pad display with spaces
l 1d06 append_optsign_r6
l 1d11 append_space
l 1d15 append_sign_r1
l 1d17 append_pos
l 1d1b append_neg
l 1d1f append_hsdigit
l 1d23 append_lsdigit
l 1d25 append_digit
l 1d29 append_tail

;**** disp stuff
L 0Dc5 print_calstr_r2
! 0dc5 i: r2=&src in page 0x300
l 1602 print_GPIBaddr
l 1708 disp_print1_r2
! 1708 print predefined strings from table, to disp buf
l 1724 disp_print_r2
l 17c5 disp_putc
! 17c5 write to dispbuf : i: a=val, r1=&dest,
l 1906 disp_setpwo
! 1906 if (!f1) : clr pwo then set pwo, sync=0
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


;************* locs with low confidence
l 0106 isol_dly
! 0106 approx 10-15ms ? rough calc
! 0413 do math on raw ADC val ?

l 0643 reset_debug
! 0643 init code for reset with A12=0
L 0f28 cal58_sub2C
! 0f28 cal58 -= cal2C ? not sure
l 1185 keyjmp_85_modechange
l 118a keyjmp_8a_LCL
l 1197 keyjmp_97_AUTO
l 11a1 keyjmp_a1_UP
l 11a5 keyjmp_a5_DOWN
l 11af keyjmp_af_SGL
! 11af called with mb0
l 11bf keyjmp_bf_SHIFT
l 11c4 keyjmp_c4_shift345
l 11c9 keyjmp_c9_ADRS
l 11cd keyjmp_cd_CAL
l 11d6 keyjmp_d6_INT
l 11e3 keyjmp_e3_SRQ
l 11e7 keyjmp_e7_AUTOZ
l 11ef keyjmp_ef_TESTRST

l 1419 jmpt1407_19
l 1447 jmpt1407_47
l 144b jmpt1407_4b
l 14b4 jmpt1407_b4
l 146f GPIBjmp_6f_Ffunc
l 147f jmpt1407_7f
l 14a6 jmpt1407_a6
l 14b2 jmpt1407_b2
l 14b6 jmpt1407_b6
l 14b8 jmpt1407_b8
l 14bb GPIBjmp_bb_Wread
l 14cf jmpt1407_cf
l 14d7 GPIBjmp_d7_Xwrite
# 14d7 write to CALRAM !!
l 14e7 jmpt1407_e7
l 1484 jmpt1407_84
l 147b jmpt1407_7b
l 146d jmpt1407_6d
l 147d jmpt1407_7d

l 15bb sub_15bb
! 17d8 j if not changed; else clr f0
l 17da cal_toggle0
! 17da (toggle calram[0] and ret a)
l 17e9 sub_17E9
l 1800 clr_A12_ret
l 1a4c _cal_toggle0
! 1a4c toggle calram[0] and ret a
! 1a4e SRAM_CS
# 1a67 61=AD LINK FAIL


;************* general comments
;vaguely sorted

! 068d calRAM_CE
! 081e calRAM_CE
! 0e02 calRAM_CE
! 14c3 calRAM_CE


! 0106 clr P27 : isol_out
! 0201 idcal = stored @ RAM0[3F]
! 0451 cal2C[] += cal36[] ?
! 063C set P27 (isol_dout)
! 0644 clr P27 (isol_dout)
! 0678 calRAM_CE
! 0823 invert nib @ 00 . lols
! 0A3C val: hinib
! 0A3D r1=addr
! 0A42 val: lonib
! 0AA6 entry[6 + i]
! 0B0C loop (r2) times
! 0C9B 0x45[2i + 0] = r0[i + 0]
! 0CA0 0x45[2i + 1], r0[i + 1] >> 4
! 103B clear iRAM
! 1040 write 0xFF to iRAM
! 1049 test iRAM[idx]==0xFF

! 14D9 calRAM_CE


;************* data / ignore sections
l 0174 tbl_0174
b 0174-01a6

l 0306 calstr_06
# 0306 CAL ABORTED
l 0313 calstr_13
# 0313 CAL FINISHED
l 0320 calstr_20
# 0320 ENABLE CAL
l 032D calstr_2D
# 032D CALIBRATING
l 033a calstr_3a
# 033a VALUE ERROR
l 0347 calstr_47
# 0347 AC I VAL ERR
l 0354 calstr_54
# 0354 CAL RAM FAIL
l 0361 calstr_61
# 0361 AD LINK FAIL
l 036e calstr_6e
# 036e AD SLOPE ERR
l 037B calstr_7B
# 037B INVALID ZERO
B 0306-0387

l 04db tbl_spstatus?
b 04db-04e3

b 0e0f-0e40
i 0f70-0fff

l 1098 tbl_datainit
# 1098 does iRAM[datainit[0 + 2i]] = datainit[1 + 2i]
b 1098-109c

l 10c1 tbl_flagerrors
# 10c1 offs => flag,str
# 10c1 c1: 02,47 UC RAM FAIL
# 10c1 c3: 04,54 UC ROM FAIL
# 10c1 c5: 01,6e UNCALIBRATED
# 10c1 c7: 20,7b AD LINK FAIL
# 10c1 c9: 10,88 AD TEST FAIL
b 10c1-10ca

# 1169 keycode jmp tables !
# 1169 DCV,ACV,2W,4W,   DCA,ACA,SHIFT,AUTO
# 1169 UP,DOWN,INT,SGL,  SRQ,LCL

l 1169 keyjmp_unshifted
b 1169-1177
l 1177 keyjmp_shifted
b 1176-1184

# 1306 GPIB RXalpha table; tbl[0] = 'A'
# 1306 if 0 : invalid. Other values are copied to iRAM[2A];
# 1306 bit 6 (0x40) causes to clear iRAM[27].bit7 and do GPIB_jmp1
# 1306 value & 0x1F gives offset into GPIBjmp_1407[] !
#
# 1306 first digits: () = illegal
# 1306 (A) B C D	E F (G) H
# 1306 (IJ) K (L)	M N (OP)
# 1306 (Q) R S T	(UV) W X
# 1306 (Y) Z
l 1306 GPIB_alphatbl
b 1306-131f

l 1320 tbl_keys
# 1320 keycode lookup !
# 1320 DCV,ACV,2W,4W, DCA,ACA,SHIFT,AUTO
# 1320 UP,DOWN,INT,SGL,SRQ,LCL

b 1320-132e

l 13e6 tbl_13e6
! 13e6 see movp with 0xe6
b 13e6-13f1

l 13f2 ascii_99999
! 13f2 see movp with 0xf2
b 13f2-13fa

# 1407 GPIB RX actions.
# 1407 entries 0-9 are for digits ?
# 1407 other entries obtained from GPIB_alphatbl
l 1407 GPIBjmp_1407
! 1407 looks like GPIB actions
b 1407-1418

# 173A string tables !
# 173A bit flags : 0x80 = ?, 0x40 : decimal point !
# 1731 1 to 0x1A maps to 'A'-'Z' ! (ASCII - 0x40)
# 0x40-0x5A ('A'-'Z') permitted too ? => show with decimal point !
# 0x20 : space ( + 0)

l 173a str173A_3a
# 173a SELF TEST
l 1747 str173A_47
# 1747 UC RAM FAIL
l 1754 str173A_54
# 1754 UC ROM FAIL
l 1761 str173A_61
# 1761 (all segs?)
l 176e str173A_6e
# 176e UNCALIBRATED
l 177b str173A_7b
# 177b AD LINK FAIL
l 1788 str173A_88
# 1788 AD TEST FAIL
l 1795 str173A_95
# 1795 HPIB ADRS TO
l 17a2 str173A_a2
# 17a2 OVLD
l 17ab str173A_ab
# 17ab (blank)
l 17b8 str173A_b8
# 17b8 SELF TEST OK
b 173a-17c4

l 1b33 tbl_1b33
# 1b33 fits with func selection (1=DCV, 2=ACV, etc.)
b 1b33-1b39

i 1e3e

l 1f61 tbl_prefixes
# 1f61 M/K/G etc. Some weirdness
# 1f61 " \0MFMG E"
# 1f61 " F GKEKF"
# 1f61 "KGMEM"
b 1f61-1f75


l 1f76 tbl_units
# 1f76 unit suffixes
# 1f76 FXFV DCVA
# 1f76 COHM OHMA
# 1f76 DCAA COHM
b 1f76-1f8d

l 1ff3 tbl_1ff3
b 1ff3-1ffa

! 1fff probable dummy byte to bring checksum == 0 (see romck_prepare)
b 1fff
;************* forced bank selection
;i.e. force sel mb0 / mb1
m 0 1001
m 1 135e
m 1 1365
m 1 136c
m 1 1373
m 1 1375
m 1 1377
m 1 137f
m 1 1382
m 0 13c4	;sketch
m 1 1541
m 0 18e3
m 0 19bd
m 0 19c2
m 0 19c9
m 0 19cc
m 0 19d5
m 0 19dd
m 0 19e4
m 0 19eb
m 0 19f0
m 0 19f3
m 0 19fa
m 0 1a6b
m 0 1e13
m 1 1f13
