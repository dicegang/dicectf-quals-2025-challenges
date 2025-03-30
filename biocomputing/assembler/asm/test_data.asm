; test_data.asm: Testing ROM access and data section
; First load some values from ROM into registers
LOADI R1, 42       ; ASSERT R1 = 42
LOADI R2, 8        ; Base address for memory writes

; Store some values in regular memory
STORE (R2), R1     ; Store 42 at memory[8]
STORE 1(R2), R1    ; Store 42 at memory[9]

; Set up base address for ROM access (128 + 32 = 160)
LOADI R6, 160      ; Base address for ROM reads

; Load values from ROM using base address
LOAD R3, (R6)      ; Load first ROM byte into R3
LOAD R4, 1(R6)     ; Load second ROM byte into R4
LOAD R5, 2(R6)     ; Load third ROM byte into R5

; Store ROM values to verify them
STORE 16, R3       ; Store first ROM byte
STORE 17, R4       ; Store second ROM byte
STORE 18, R5       ; Store third ROM byte

; Data section starts at 32 with test pattern
.data(32) FF 42 A5 00 55 AA 