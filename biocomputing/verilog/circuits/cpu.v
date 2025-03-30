module cpu(
    input wire clk,
    input wire rst,
    input wire [8*128 - 1:0] rom,
    output wire [8*24-1:0] memory_out
);

reg [7:0] memory [0:31];    // 32 bytes of memory (0-7 are registers, 8-32 are general memory)

// Connect internal memory to output
genvar i;
generate
    for (i = 8; i < 32; i = i + 1) begin: memory_output
        assign memory_out[8*i - 64 +: 8] = memory[i];
    end
endgenerate

// Define PC as memory[0]
wire [7:0] pc = memory[0];

// Memory read from ROM - extract 8-bit words using bit slicing
wire [7:0] mem_out = rom[8*(pc[6:0]) +: 8];  // Current word
wire [7:0] next_word = rom[8*(pc[6:0] + 1) +: 8];  // Next word

// Instruction decode
wire [4:0] opcode = mem_out[7:3];
wire [2:0] rs = mem_out[2:0];  // Source register (RS), always last argument
wire [2:0] rd = next_word[7:5];  // Destination register (RD)
wire [3:0] imm4 = next_word[3:0];  // 4-bit immediate value for ADD/SUB
wire [4:0] imm5 = next_word[4:0];  // 5-bit immediate value for LOAD/STORE 
wire [7:0] rs_value = memory[rs];  // Register values are in memory[0:7]
wire [7:0] rd_value = memory[rd];

wire is_signed = next_word[4];  // Sign bit determines if rs_value + imm4 should be positive or negative

// Memory access logic
wire [7:0] signed_imm5 = {{3{imm5[4]}}, imm5};  // Sign extend imm5 from 5 to 8 bits
wire [7:0] load_effective_addr = rs_value + signed_imm5;  // Base address (in RS) + signed offset (imm5) for LOAD
wire [7:0] store_effective_addr = rd_value + signed_imm5;  // Base address (in RD) + signed offset (imm5) for STORE
wire [4:0] load_mem_index = load_effective_addr[4:0];  // Use bottom 5 bits for 32 memory locations
wire [4:0] store_mem_index = store_effective_addr[4:0];  // Use bottom 5 bits for 32 memory locations
                
wire is_jnz = next_word[7];
wire should_jump = is_jnz ? (rs_value != 0) : (rs_value == 0);
wire is_less_than = memory[2] < rs_value;  // Signed comparison for JLT (R2 < RS)

// Main CPU logic
always @(posedge clk) begin
    if (rst) begin
        // Reset all memory (including registers)
        for (integer i = 0; i < 32; i = i + 1)
            memory[i] <= 0;

        protein_count <= 0;
        for (integer i = 0; i < 64; i = i + 1)
            protein_array[i] <= 0;
    end else begin
        // Fetch/execute stage
        case (opcode)
            5'b00001: begin // LOADI RS, imm8 (load next_word into RS)
                memory[0] <= pc + 2;  // Skip over immediate
                memory[rs] <= next_word;
            end

            5'b00010: begin // MOV RD, RS[, signed_imm5] (RD = RS + signed_imm5)
                memory[0] <= pc + 2;
                memory[rd] <= rs_value + signed_imm5;  // Add RS and sign-extended imm5
            end

            5'b00011: begin // JZ/JNZ target, RS 
                            // Jump to target & 0x7F if:
                            //   - target[7] = 0: RS is zero (JZ)
                            //   - target[7] = 1: RS is not zero (JNZ)
                if (should_jump) begin
                    memory[0] <= {1'b0, next_word[6:0]};  // Clear high bit for actual target
                end else begin
                    memory[0] <= pc + 2;
                end
            end

            5'b01010: begin // JLT target, RS (jump to target if R2 < RS, signed comparison)
                if (is_less_than) begin
                    memory[0] <= {1'b0, next_word[6:0]};  // Clear high bit for actual target
                end else begin
                    memory[0] <= pc + 2;
                end
            end

            5'b00100: begin // ADD RD, RS[, imm4]  - RD += RS + imm4
                            // SUB RD, RS[, imm4]  - RD -= RS + imm4
                memory[0] <= pc + 2;
                memory[rd] <= memory[rd] + (is_signed ? -(rs_value + imm4) : (rs_value + imm4));
            end

            5'b00101: begin // LOAD RD, imm5(RS) (load from memory[RS + imm5] into RD)
                            // If RS is R7, treat imm5 as absolute src register (LOAD RD, imm5)
                            // If high bit of effective address is set, load from ROM instead of memory
                memory[0] <= pc + 2;
                if (rs == 3'b111) begin
                    memory[rd] <= memory[imm5];  // Load directly from register specified by imm5
                end else if (load_effective_addr[7]) begin
                    memory[rd] <= rom[8*(load_effective_addr[6:0]) +: 8];  // Load from ROM
                end else begin
                    memory[rd] <= memory[load_mem_index];  // Normal memory load
                end
            end

            5'b00110: begin // STORE imm5(RD), RS (store RS into memory[RD + imm5])
                            // If RS is R7, treat imm5 as absolute dst register (STORE imm5, RS)
                memory[0] <= pc + 2;
                if (rd == 3'b111) begin
                    memory[imm5] <= rs_value;  // Store directly to register/memory specified by imm5
                end else begin
                    memory[store_mem_index] <= rs_value;  // Normal memory store
                end
            end

            5'b00111: begin // MUL RS (R1 *= RS)
                memory[1] <= memory[1] * rs_value;
                memory[0] <= pc + 1;  // One byte instruction
            end

            5'b01000: begin // SHR imm3 (R1 >>= imm3)
                memory[1] <= memory[1] >> rs;  // Use RS as shift amount
                memory[0] <= pc + 1;  // One byte instruction
            end

            5'b01001: begin // MOD RS (R1 %= RS)
                memory[1] <= memory[1] % rs_value;
                memory[0] <= pc + 1;  // One byte instruction
            end

            default: begin
                // Invalid opcode - do nothing
                memory[0] <= pc + 1;
            end
        endcase
    end
end

endmodule