; test_loop.asm: Computing Fibonacci sequence using loops and storing in memory[8:16]
; F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)
; Will compute F(0) through F(8) and store them in memory[8] through memory[16]

; Initialize first two values
LOADI R2, 8      ; Memory pointer starts at 8
LOADI R1, 0      ; F(0) = 0
STORE (R2), R1   ; Store F(0)
LOADI R1, 1      ; F(1) = 1
STORE 1(R2), R1  ; Store F(1)

loop:
    LOAD R1, (R2)    ; Load F(n-2) from current position
    LOAD R4, 1(R2)   ; Load F(n-1) from next position
    ADD R1, R4       ; R1 = F(n-1) + F(n-2)
    STORE 2(R2), R1  ; Store F(n) at next position
    
    MOV R2, R2 + 1   ; Increment pointer
    
    LOADI R1, 14     ; Compare pointer with 14 (last position to write is at 16)
    SUB R1, R2       ; R1 = 14 - pointer
    JZ end, R1       ; If pointer == 14, exit loop
    JMP loop         ; Otherwise continue loop
end:
