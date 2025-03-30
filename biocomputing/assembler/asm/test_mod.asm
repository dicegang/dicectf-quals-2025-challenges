; test_mod.asm: Testing MOD instruction

; Test case 1: 7 % 3 = 1
LOADI R1, 7        ; ASSERT R1 = 7
LOADI R2, 3        ; ASSERT R2 = 3
MOD R2             ; ASSERT R1 = 1

; Test case 2: 12 % 5 = 2
LOADI R1, 12       ; ASSERT R1 = 12
LOADI R2, 5        ; ASSERT R2 = 5
MOD R2             ; ASSERT R1 = 2

; Test case 3: 20 % 6 = 2
LOADI R1, 20       ; ASSERT R1 = 20
LOADI R2, 6        ; ASSERT R2 = 6
MOD R2             ; ASSERT R1 = 2