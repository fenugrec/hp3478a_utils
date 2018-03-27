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
C 1000
C 1003
C 1007

;************* functions/locs with >95% confidence
L 00BA GPIB_trig
L 0200 check_calentry
! 0200 i: a=calid. verify checksum of entry
l 0204 check_calentr_a
! 0204 verify checksum at a=addr
l 0400 GPIB_SPstuff
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
l 0e0d ret_getaddr
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
l 1708 disp_print1
! 1708 print predefined strings from table, to disp buf
l 1724 disp_print2
l 17c5 disp_putc
! 17c5 write to dispbuf : i: a=val, r1=&dest,
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

L 0Dc5 sub_0dc5
! 0dc5 i: r2=&src in 0x300 (PC & 0xFF). copy to RAM[0x44+idx] until src[idx]==0 ?

L 0f28 cal58_sub2C
! 0f28 cal58 -= cal2C ? not sure
l 1185 jmpt1169_85
l 118a jmpt1169_8a
l 1197 jmpt1169_97
l 11a1 jmpt1169_a1
l 11a5 jmpt1169_a5
l 11af jmpt1169_af
! 11af called with mb0
l 11bf jmpt1169_bf
l 11c4 jmpt1169_c4
l 11c9 jmpt1169_c9
l 11cd jmpt1169_cd
l 11d6 jmpt1169_d6
l 11e3 jmpt1169_e3
l 11e7 jmpt1169_e7
l 11ef jmpt1169_ef
l 1339 GPIB_sendreading?


l 1419 jmpt1407_19
l 1447 jmpt1407_47
l 144b jmpt1407_4b
l 14b4 jmpt1407_b4
l 146f jmpt1407_6f
l 147f jmpt1407_7f
l 14a6 jmpt1407_a6
l 14b2 jmpt1407_b2
l 14b6 jmpt1407_b6
l 14b8 jmpt1407_b8
l 14bb jmpt1407_bb
l 14cf jmpt1407_cf
l 14d7 jmpt1407_d7
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
! 17e9 get iRAM[2A], if < 0x3F then ret a |= 0x40 => check MTA/MLA ?
L 19AF GPIB_getSPSTAT?
l 1a4c _cal_toggle0
! 1a4c toggle calram[0] and ret a
! 1a4e SRAM_CS
! 1f8e r7=rxbyte


;************* general comments

! 00BC GPIB_CS
! 00C2 AUXMODE=4 trig
! 00C4 GPIB_release
! 0106 clr P27 : isol_out
! 0201 idcal = stored @ RAM0[3F]
! 0402 GPIB_CS
! 040F SPSTATUS
! 0411 SPMODE
! 0451 cal2C[] += cal36[] ?
! 063C set P27 (isol_dout)
! 0644 clr P27 (isol_dout)
! 065C GPIB_CS (for init)
! 0662 AUXMODE = 02 creset
! 0664 AUXMODE=0 pon
! 0669 ADDRMODE = 80 tonly
! 066F DOUT = 0
! 0672 SPMODE = 0
! 0673 a=SPSTAT
! 0676 GPIB_release
! 0678 calRAM_CE
! 0823 invert nib @ 00 . lols
! 0A3C val: hinib
! 0A3D r1=addr
! 0A42 val: lonib
! 0AA6 entry[6 + i]
! 0B0C loop (r2) times
! 0C9B 0x45[2i + 0] = r0[i + 0]
! 0CA0 0x45[2i + 1], r0[i + 1] >> 4
! 0CAC write full entry
! 0D53 entry 0x11
! 0D58 write full entry
! 0D9B 0x44[0..7]=0
! 0DCC @(0x0300 | a)
! 103B clear iRAM
! 1040 write 0xFF to iRAM
! 1049 test iRAM[idx]==0xFF
! 10DA SPSTATUS
! 10DC SPMODE = a
! 114e tbl read @ 1300[]
! 1168 INFO: indirect jump
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
! 12C9 iRAM[2A]
! 12DF a = [0x1300 | a]
! 12E9 (a = iRAM[2A],r7 = DIN)
! 134F GPIB_CS
! 135E ascii_digitstuff
! 1362  '.'
! 13A1 AUXMODE=06 sendEOI
! 13AB DOUT = data
! 13E8 INFO: indirect jump
! 1400 i : r0=&val.
! 1406 INFO: indirect jump
! 14D9 calRAM_CE
! 14E1 GPIB_release
! 14E3 GPIB_CS
! 14E5 wtf
! 1600 parse DIP switch stuff
! 160F GPIB_DIPsel
! 1611 get DIP setting
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
! 1800 clr A12
! 1933 GPIB_CS

! 199B GPIB_CS
! 199F GPIB_release
! 19B1 SPSTAT
! 19B3 Carry = SRQS
! 1E13 still mb0
! 1E20 GPIB_CS
! 1E26 AUXMODE = TRIG
! 1E2A a = ADDRSTAT?
! 1F05 ret to 16a5 !
! 1F8E r7 = rxbyte


;************* data / ignore sections
l 0174 tbl_0174
b 0174-01a6
l 0306 cmd_0306[0
L 0313 cmd_0313[1	; goes with sub 0DC5
l 0320 cmd_0320[2
L 032D cmd_032D[3
l 033a cmd_033a[4
l 0347 cmd_0347[5
l 0354 cmd_0354[6
l 0361 cmd_0361[7
l 036e cmd_036e[8
L 037B cmd_037B[9

B 0306-0387

l 04db tbl_spstatus?
b 04db-04e3

b 0e0f-0e40
i 0f70-0fff

l 1098 tbl_datainit?
! 1098 looks like datainit[0 + 2i] = ramaddr, datainit[1 + 2i] = initial value
b 1098-109c

l 10c1 tbl_flaginit?
b 10c1-10ca

l 1169 jmptable_1169
b 1169-1184

l 1306 tbl_1306
b 1306-132e

l 13e6 tbl_13e6
! 13e6 see movp with 0xe6
b 13e6-13f1

l 13f2 ascii_99999
! 13f2 see movp with 0xf2
b 13f2-13fa

l 1407 jmptable_1407
! 1407 looks like GPIB actions
b 1407-1418

l 173a tbl_173a[0]
! 173a sizeof elems=0x0D and sometimes 8; 0-terminated, see 1725
l 1747 tbl_173a[1]
l 1754 tbl_173a[2]
l 1761 tbl_173a[3]
l 176e tbl_173a[4]
l 177b tbl_173a[5]
l 1788 tbl_173a[6
l 1795 tbl_173a[7
l 17a2 tbl_173a[8
l 17ab tbl_173a[9
l 17b8 tbl_173a[0a
b 173a-17c4

l 1b33 tbl_1b33
b 1b33-1b3a

l 1f61 tbl_1f61
b 1f61-1f75
l 1f76 tbl_1f76
b 1f76-1f8d

l 1ff3 tbl_1ff3
b 1ff3-1ffa

! 1fff probable dummy byte to bring checksum == 0 (see romck_prepare)
b 1fff
;************* forced bank selection
;i.e. force sel mb0 / mb1
m 1 135e
m 1 1365
m 1 136c
m 1 1373
m 1 1375
m 1 1377
m 1 137f
m 1 1382
m 1 1541
m 0 1e13
m 1 1f13