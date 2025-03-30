LOADI R3, 208         ; 128 + 80

; LOADI R1, 0
; LOADI R6, 0
LOADI R7, 4

LOADI R2, 14
LOADI R4, 'A'

GEN_CHECK_LOOP:
    MUL R2
    ADD R1, R7

    LOADI R5, 23
    MOD R5

    LOAD R5, (R3)
    STORE (R2), R5
    SUB R5, R1
    SUB R5, R4

    MOV R2, R2 + 1
    MOV R3, R3 + 1

    JZ CHECK_VALID, R5

    ADD R6, R7
    JMP CHECK_END

CHECK_VALID:
    ADD R6, R5
    JMP CHECK_END

CHECK_END:
    LOADI R5, 23 ; 14 + 8 + 1
    JLT GEN_CHECK_LOOP, R5
    JZ GEN_CHECK_LOOP, R6

LOADI R1, 204 ; 128 + 72 + 4
MOV R2, R7
JLT END, R6

LOADI R1, 200 ; 128 + 80

END:

LOADI R5, '|'
STORE 13, R5
STORE 22, R5

; reuse r2=r7 which is 4
; r2 = 4
LOADI R3, 9
COPY_LOOP:
    LOAD R4, (R1)
    STORE (R3), R4

    MOV R2, R2 - 1
    MOV R1, R1 + 1
    MOV R3, R3 + 1

    JNZ COPY_LOOP, R2

STORE 8, R5

.data(72) 'd' 'i' 'c' 'e' '.' 'b' 'a' 'd'

; Space for user input
;.data(80) 'C' 'M' 'Q' 'N' 'V' 'P' 'I' 'T' 'F' 'E' 'W' 'U' 'K' 'G' 'J' 'B'
; CMQNVPITFEWUKGJBHO
