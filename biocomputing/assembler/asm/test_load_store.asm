; test_load_store.asm: Testing LOAD and STORE instructions with both addressing modes

; Test register + offset addressing
LOADI R2, 8        ; ASSERT R2 = 8
                   ; Base address for first array
LOADI R1, 42       ; ASSERT R1 = 42
STORE (R2), R1     ; Store 42 at memory[8]
STORE 1(R2), R1    ; Store 42 at memory[9]

; Test absolute addressing
LOADI R1, 100      ; ASSERT R1 = 100
STORE 16, R1       ; Store 100 at memory[16] using absolute addressing
STORE 17, R1       ; Store 100 at memory[17] using absolute addressing

; Test loading with register + offset
LOAD R3, (R2)      ; ASSERT R3 = 42
                   ; Load from memory[8]
LOAD R4, 1(R2)     ; ASSERT R4 = 42
                   ; Load from memory[9]

; Test loading with absolute addressing
LOAD R5, 16        ; ASSERT R5 = 100
                   ; Load from memory[16]
LOAD R6, 17        ; ASSERT R6 = 100
                   ; Load from memory[17]

; Test mixing both addressing modes
STORE 20, R3       ; Store R3 (42) to memory[20]
LOAD R1, 2(R2)     ; Load from memory[10] into R1 (should be 0)
STORE 3(R2), R5    ; Store R5 (100) to memory[11]
LOAD R7, 20        ; ASSERT R7 = 42
                   ; Load from memory[20]

; Expected memory layout after execution:
; memory[8]  = 42   (stored via register+offset)
; memory[9]  = 42   (stored via register+offset)
; memory[10] = 0    (untouched)
; memory[11] = 100  (stored via register+offset)
; memory[16] = 100  (stored via absolute addressing)
; memory[17] = 100  (stored via absolute addressing)
; memory[20] = 42   (stored via absolute addressing) 