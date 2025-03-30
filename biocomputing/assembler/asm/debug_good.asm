; debug_good.asm: Simple program to write "=good" to output
; Result will be written to memory addresses 8-12

; Write characters to memory starting with 'd' and working backwards

LOADI R1, 'd'
STORE 12, R1

LOADI R1, 'o'
STORE 11, R1

LOADI R1, 'o'
STORE 10, R1

LOADI R1, 'g'
STORE 9, R1

LOADI R1, '='
STORE 8, R1

; End of program