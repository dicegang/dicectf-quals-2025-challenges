; test_add_loadi.asm: Testing ADD and LOADI instructions

; Test basic arithmetic
LOADI R1, 10       ; ASSERT R1 = 10
LOADI R2, 20       ; ASSERT R2 = 20
ADD R1, R2         ; ASSERT R1 = 30

; Test with larger values
LOADI R3, 255      ; ASSERT R3 = 255
LOADI R4, 128      ; ASSERT R4 = 128
ADD R1, R4         ; ASSERT R1 = 158

; Test with zero and small values
LOADI R5, 0        ; ASSERT R5 = 0
LOADI R6, 1        ; ASSERT R6 = 1
ADD R1, R6         ; ASSERT R1 = 159

; Test with immediate values
LOADI R2, 5        ; ASSERT R2 = 5
ADD R1, R2, 3      ; ASSERT R1 = 167
SUB R1, R2, 2      ; ASSERT R1 = 160

; Test different number formats
LOADI R7, 0xFF     ; ASSERT R7 = 255
ADD R1, R7         ; ASSERT R1 = 159
                   ; Note: Result truncated to 8 bits 