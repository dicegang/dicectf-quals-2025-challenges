; test_mul_shr.asm: Testing MUL and SHR instructions

; Test MUL instruction
LOADI R1, 4        ; ASSERT R1 = 4
LOADI R2, 3        ; ASSERT R2 = 3
MUL R2             ; ASSERT R1 = 12

LOADI R3, 5        ; ASSERT R3 = 5
MUL R3             ; ASSERT R1 = 60

; Test SHR instruction
SHR 2              ; ASSERT R1 = 15
SHR 3              ; ASSERT R1 = 1

; Test edge cases
LOADI R1, 255      ; ASSERT R1 = 255
SHR 1              ; ASSERT R1 = 127

LOADI R1, 128      ; ASSERT R1 = 128
SHR 7              ; ASSERT R1 = 1 