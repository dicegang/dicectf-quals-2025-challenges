; test_jz_jnz.asm: Testing JZ and JNZ instructions
; Memory map:
; addr 8: JZ with zero (should be 1)
; addr 9: JZ with non-zero (should be 1)
; addr 10: JNZ with non-zero (should be 1)
; addr 11: JNZ with zero (should be 1)

; Initialize test values
LOADI R1, 0        ; Zero value for testing
LOADI R2, 5        ; Non-zero value for testing
LOADI R3, 1        ; Success marker

; Test JZ with zero value (should jump)
JZ NEXT1, R1
LOADI R3, 0        ; Wrong path
NEXT1:
STORE 8, R3        ; Should be 1

; Test JZ with non-zero value (should not jump)
LOADI R3, 0        ; Reset marker
JZ NEXT2, R2       ; Should not jump
LOADI R3, 1        ; Correct path
NEXT2:
STORE 9, R3        ; Should be 1

; Test JNZ with non-zero value (should jump)
JNZ NEXT3, R2
LOADI R3, 0        ; Wrong path
NEXT3:
STORE 10, R3       ; Should be 1

; Test JNZ with zero value (should not jump)
LOADI R3, 0        ; Reset marker
JNZ NEXT4, R1      ; Should not jump
LOADI R3, 1        ; Correct path
NEXT4:
STORE 11, R3       ; Should be 1

; Expected memory state after execution:
; memory[8] = 1    (JZ jumped on zero)
; memory[9] = 1    (JZ didn't jump on non-zero)
; memory[10] = 1   (JNZ jumped on non-zero)
; memory[11] = 1   (JNZ didn't jump on zero) 