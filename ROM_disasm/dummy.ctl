; test for ghidra script Control file for d48 disassembler.

# 16d0 a few far call "bridges" here
l 16d0 farcall_0026
! 16d0 inline return via 16d8

; and a few malformed lines

! 16d1: malformed address
l 16d2 whitespace in label

L 0f2e uppercase_label
