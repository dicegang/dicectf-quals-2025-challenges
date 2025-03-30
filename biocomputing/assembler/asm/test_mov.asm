; test_mov.asm: Testing MOV instruction with signed immediate values

; Test basic MOV functionality (no immediate)
LOADI R1, 42       ; ASSERT R1 = 42
MOV R2, R1         ; ASSERT R2 = 42
MOV R3, R2         ; ASSERT R3 = 42

; Test MOV with positive immediate values
MOV R4, R1 + 5     ; ASSERT R4 = 47
MOV R5, R4 + 10    ; ASSERT R5 = 57
MOV R6, R5 + 15    ; ASSERT R6 = 72

; Test MOV with negative immediate values
MOV R1, R6 - 10    ; ASSERT R1 = 62
MOV R2, R1 - 5     ; ASSERT R2 = 57
MOV R3, R2 - 15    ; ASSERT R3 = 42

; Test edge cases of immediate range
LOADI R7, 100      ; ASSERT R7 = 100
MOV R1, R7 + 15    ; ASSERT R1 = 115
MOV R2, R7 - 16    ; ASSERT R2 = 84

; Test chaining MOVs with immediates
LOADI R1, 50       ; ASSERT R1 = 50
MOV R2, R1 + 5     ; ASSERT R2 = 55
MOV R3, R2 - 3     ; ASSERT R3 = 52
MOV R4, R3 + 7     ; ASSERT R4 = 59
MOV R5, R4 - 9     ; ASSERT R5 = 50 