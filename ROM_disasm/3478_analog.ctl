; Control file for d48 disassembler.
;
; intent is to add symbols and labels in here iteratively so the listing can be
; re-generated automatically.
;
; command : d48 -d -n -b <filename>
; (-n gives 0x.. constants instead of ..h)
;
; Note : the disasm in ghidra is now (2022/12) better commented and analyzed, except for the movp tables


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

l 003f init_continue
l 0700 selftest
l 0706 clr_RAM_1
l 070e set_RAM_FF
l 0720 clr_RAM_2
b 072c
l 072c ????
l 072d romck_prepare
l 0732 romck
l 075d romck_bad


;********** movp tables

! 00e2 see 00de
b 00e2-00f1

! 01ba see 011f
b 01ba-01c9

! 01ca see 010e
b 01ca-01e6

! 03e6 see 03dd
b 03e6-03f5

l 0401 bcdtbl_0401
! 0401 not sure, BCD shit @ 0416?
b 0401-0409

l 0561 tbl_0561
! 0561 see 052e
b 0561-05a0

l 05a1 tbl_05a1
! 05a1 see 0536
b 05a1-05a8

l 05a9 tbl_05a9
! 05a9 probably 2-byte entries, see 053f
b 05a9-05b8

l 05b9 tbl_05b9
! 05b9 see 054c
b 05b9-05bc