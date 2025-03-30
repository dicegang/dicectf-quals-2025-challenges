import sys
import argparse
import re

def format_binary(num, width=8):
    """Format a number as binary string with given width"""
    return f"{num:0{width}b}"

def collect_labels(lines):
    """First pass: collect all labels and their positions"""
    labels = {}
    current_pos = 0
    
    # First pass: collect all label definitions
    for line in lines:
        # Remove comments and strip whitespace
        line = line.split(';')[0].strip()
        if not line:
            continue
            
        # Check if line contains a label
        if line.endswith(':'):
            label = line[:-1].strip()
            labels[label] = current_pos
            continue
            
        # Count words for this instruction
        parts = line.split()
        if not parts:  # Skip empty lines
            continue
            
        mnemonic = parts[0].upper()
        
        # Two-word instructions
        if mnemonic in ['LOADI', 'JMP', 'JZ', 'JNZ', 'ADD', 'SUB', 'MOV', 'LOAD', 'STORE', 'JLT']:
            current_pos += 2
        # Single-word instructions
        elif mnemonic in ['MUL', 'SHR', 'MOD', 'CMP_COMP', 'LOAD_COMP', 'STEP_COMP', 'GOOD', 'BAD']:
            current_pos += 1
        elif '.DATA' in mnemonic:
            pass
        else:
            assert False, f"Unknown instruction: {mnemonic}"
            
    return labels

def assemble_line(line, labels, current_pos, debug=False):
    # Remove comments and strip whitespace
    line = line.split(';')[0].strip()
    if not line:
        return None
    if line.endswith(':'):  # Skip labels on second pass
        return None
        
    parts = line.split()
    mnemonic = parts[0].upper()

    if debug:
        print(f"\nAssembling: {line}")

    if mnemonic == "JMP":
        # JMP value (alias for LOADI R0, value)
        assert len(parts) == 2, "JMP requires 1 argument: JMP value"
        target_str = parts[1]
        try:
            # First try parsing as a number
            target = int(target_str, 0)
        except ValueError:
            # If that fails, look up the label
            assert target_str in labels, f"Undefined label: {target_str}"
            target = labels[target_str]
        assert 0 <= target <= 255, "Target address must be between 0 and 255"
        
        # First word: opcode(5) | rs=0(3)
        word1 = (0b00001 << 3) | 0
        # Second word: immediate value (8 bits)
        word2 = target & 0xFF

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00001, 5)}, rs: {format_binary(0, 3)})")
            print(f"  Word 2: {format_binary(word2)} (target: 0x{target:02x})")

        return [word1, word2]

    elif mnemonic == "LOADI":
        # LOADI RS, imm8 (load next_word into RS)
        assert len(parts) == 3, "LOADI requires 2 arguments: LOADI RS, imm8"
        rs = parse_register(parts[1].replace(',', ''))
        assert rs != 0, "Cannot use LOADI with R0 directly - use JMP instead"
        
        # Handle immediate value or label
        imm_str = parts[2].replace(',', '')
        try:
            # First check if it's a character literal
            if imm_str.startswith("'") and imm_str.endswith("'"):
                char_val = parse_ascii_char(imm_str)
                assert char_val is not None, f"Invalid character literal: {imm_str}"
                imm = char_val
            else:
                # Try parsing as a number
                imm = int(imm_str, 0)
        except ValueError:
            # If that fails, look up the label
            assert imm_str in labels, f"Undefined label: {imm_str}"
            imm = labels[imm_str]
        assert 0 <= imm <= 255, "Immediate must be between 0 and 255"
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00001 << 3) | (rs & 0x7)
        # Second word: immediate value (8 bits)
        word2 = imm & 0xFF

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00001, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (imm: {format_binary(imm, 8)})")

        return [word1, word2]

    elif mnemonic == "ADD" or mnemonic == "SUB":
        # ADD RD, RS[, imm4]  - RD += RS + imm4
        # SUB RD, RS[, imm4]  - RD -= RS + imm4
        assert 3 <= len(parts) <= 4, f"{mnemonic} requires 2-3 arguments: {mnemonic} RD, RS[, imm4]"
        rd = parse_register(parts[1].replace(',', ''))
        rs = parse_register(parts[2].replace(',', ''))
        
        # Handle optional immediate value
        if len(parts) == 4:
            try:
                imm = int(parts[3].replace(',', ''), 0)
            except Exception:
                assert False, "Invalid immediate value: " + parts[3]
            assert -8 <= imm <= 7, "Immediate must be between -8 and 7 (4-bit signed)"
        else:
            imm = 0
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00100 << 3) | (rs & 0x7)
        # Second word: rd(3) | sign(1) | imm4
        word2 = ((rd & 0x7) << 5) | ((1 if mnemonic == "SUB" else 0) << 4) | (imm & 0xF)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00100, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (rd: {format_binary(rd, 3)}, sign: {1 if mnemonic == 'SUB' else 0}, imm: {format_binary(imm & 0xF, 4)})")

        return [word1, word2]

    elif mnemonic == "JZ" or mnemonic == "JNZ":
        # JZ label, RS (jump to label if RS is zero)
        # JNZ label, RS (jump to label if RS is not zero)
        assert len(parts) == 3, f"{mnemonic} requires 2 arguments: {mnemonic} label, RS"
        target_str = parts[1].replace(',', '')
        rs = parse_register(parts[2])  # RS is the second argument
        
        try:
            # First try parsing as a number
            target = int(target_str, 0)
        except ValueError:
            # If that fails, look up the label
            assert target_str in labels, f"Undefined label: {target_str}"
            target = labels[target_str]
        assert 0 <= target <= 127, "Target address must be between 0 and 127 (7 bits)"
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00011 << 3) | (rs & 0x7)
        # Second word: is_jnz(1) | target address (7 bits)
        word2 = ((1 if mnemonic == "JNZ" else 0) << 7) | (target & 0x7F)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00011, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (is_jnz: {1 if mnemonic == 'JNZ' else 0}, target: 0x{target:02x})")

        return [word1, word2]

    elif mnemonic == "JLT":
        # JLT label, RS (jump to label if R2 < RS, signed comparison)
        assert len(parts) == 3, "JLT requires 2 arguments: JLT label, RS"
        target_str = parts[1].replace(',', '')
        rs = parse_register(parts[2])
        
        try:
            # First try parsing as a number
            target = int(target_str, 0)
        except ValueError:
            # If that fails, look up the label
            assert target_str in labels, f"Undefined label: {target_str}"
            target = labels[target_str]
        assert 0 <= target <= 127, "Target address must be between 0 and 127 (7 bits)"
        
        # First word: opcode(5) | rs(3)
        word1 = (0b01010 << 3) | (rs & 0x7)
        # Second word: target address (7 bits)
        word2 = target & 0x7F

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b01010, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (target: 0x{target:02x})")

        return [word1, word2]

    elif mnemonic == "MOV":
        # MOV RD, RS + imm5 or MOV RD, RS - imm5 or MOV RD, RS
        assert len(parts) >= 3, "MOV requires format: MOV RD, RS or MOV RD, RS + imm5 or MOV RD, RS - imm5"
        rd = parse_register(parts[1].replace(',', ''))
        
        # Check for arithmetic syntax
        full_src = ' '.join(parts[2:])  # Join remaining parts to handle potential spaces
        
        # First try simple register move without operator
        if re.match(r'^[Rr][0-7]$', full_src):
            rs = parse_register(full_src)
            imm = 0
        else:
            # Try arithmetic syntax
            match = re.match(r'^([Rr][0-7])\s*([+-])\s*(\d+)$', full_src)
            assert match, "MOV must use format: MOV RD, RS or MOV RD, RS + imm5 or MOV RD, RS - imm5"
            
            # Parse the components
            rs = parse_register(match.group(1))
            op = match.group(2)
            try:
                imm = int(match.group(3), 0)
                if op == '-':
                    imm = -imm
            except Exception:
                assert False, "Invalid immediate value: " + match.group(3)
            
            assert -16 <= imm <= 15, "Immediate must be between -16 and 15 (5-bit signed)"
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00010 << 3) | (rs & 0x7)
        # Second word: rd(3) | imm5
        word2 = ((rd & 0x7) << 5) | (imm & 0x1F)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00010, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (rd: {format_binary(rd, 3)}, imm: {format_binary(imm & 0x1F, 5)})")

        return [word1, word2]

    elif mnemonic == "MUL":
        # MUL RS (R1 *= RS)
        assert len(parts) == 2, "MUL requires 1 argument: MUL RS"
        rs = parse_register(parts[1])
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00111 << 3) | (rs & 0x7)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00111, 5)}, rs: {format_binary(rs, 3)})")

        return [word1]

    elif mnemonic == "MOD":
        # MOD RS (R1 %= RS)
        assert len(parts) == 2, "MOD requires 1 argument: MOD RS"
        rs = parse_register(parts[1])
        
        # First word: opcode(5) | rs(3)
        word1 = (0b01001 << 3) | (rs & 0x7)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b01001, 5)}, rs: {format_binary(rs, 3)})")

        return [word1]

    elif mnemonic == "SHR":
        # SHR imm3 (R1 >>= imm3)
        assert len(parts) == 2, "SHR requires 1 argument: SHR imm3"
        try:
            imm = int(parts[1], 0)
        except Exception:
            assert False, "Invalid immediate value: " + parts[1]
        assert 0 <= imm <= 7, "Shift amount must be between 0 and 7 (3 bits)"
        
        # First word: opcode(5) | imm3(3)
        word1 = (0b01000 << 3) | (imm & 0x7)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b01000, 5)}, imm: {format_binary(imm, 3)})")

        return [word1]

    elif mnemonic == "LOAD":
        # LOAD RD, imm5(RS) or LOAD RD, (RS) (alias for LOAD RD, 0(RS))
        # Special case: LOAD RD, addr (absolute addressing using R7)
        assert len(parts) == 3, "LOAD requires 2 arguments: LOAD RD, imm5(RS) or LOAD RD, (RS) or LOAD RD, addr"
        rd = parse_register(parts[1].replace(',', ''))
        
        # First try absolute addressing format
        try:
            addr = int(parts[2], 0)
            assert 0 <= addr <= 31, "Absolute address must be between 0 and 31"
            # Use R7 for absolute addressing
            rs = 7
            offset = addr
        except ValueError:
            # Parse imm5(RS) format or (RS) format
            addr_part = parts[2]
            match = re.match(r'^(-?\d+)\(([Rr][0-7])\)$', addr_part)
            if not match:
                # Try (RS) format
                match = re.match(r'^\(([Rr][0-7])\)$', addr_part)
                assert match, "Invalid memory address format. Must be imm5(RS) or (RS) or absolute address, e.g. 0(R1) or (R1) or 8"
                rs = parse_register(match.group(1))
                offset = 0
            else:
                try:
                    offset = int(match.group(1), 0)
                except Exception:
                    assert False, "Invalid offset value: " + match.group(1)
                assert -16 <= offset <= 15, "Offset must be between -16 and 15 (5-bit signed)"
                rs = parse_register(match.group(2))
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00101 << 3) | (rs & 0x7)
        # Second word: rd(3) | imm5
        word2 = ((rd & 0x7) << 5) | (offset & 0x1F)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00101, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (rd: {format_binary(rd, 3)}, offset: {format_binary(offset & 0x1F, 5)})")

        return [word1, word2]

    elif mnemonic == "STORE":
        # STORE imm5(RD), RS or STORE (RD), RS (alias for STORE 0(RD), RS)
        # Special case: STORE addr, RS (absolute addressing using R7)
        assert len(parts) == 3, "STORE requires 2 arguments: STORE imm5(RD), RS or STORE (RD), RS or STORE addr, RS"
        
        # First try absolute addressing format
        try:
            addr = int(parts[1].replace(',', ''), 0)
            assert 0 <= addr <= 31, "Absolute address must be between 0 and 31"
            # Use R7 for absolute addressing
            rd = 7
            offset = addr
        except ValueError:
            # Parse imm5(RD) format or (RD) format
            addr_part = parts[1].replace(',', '')
            match = re.match(r'^(-?\d+)\(([Rr][0-7])\)$', addr_part)
            if not match:
                # Try (RD) format
                match = re.match(r'^\(([Rr][0-7])\)$', addr_part)
                assert match, "Invalid memory address format. Must be imm5(RD) or (RD) or absolute address, e.g. 0(R1) or (R1) or 8"
                rd = parse_register(match.group(1))
                offset = 0
            else:
                try:
                    offset = int(match.group(1), 0)
                except Exception:
                    assert False, "Invalid offset value: " + match.group(1)
                assert -16 <= offset <= 15, "Offset must be between -16 and 15 (5-bit signed)"
                rd = parse_register(match.group(2))
        rs = parse_register(parts[2])
        
        # First word: opcode(5) | rs(3)
        word1 = (0b00110 << 3) | (rs & 0x7)
        # Second word: rd(3) | imm5
        word2 = ((rd & 0x7) << 5) | (offset & 0x1F)

        if debug:
            print(f"  Word 1: {format_binary(word1)} (opcode: {format_binary(0b00110, 5)}, rs: {format_binary(rs, 3)})")
            print(f"  Word 2: {format_binary(word2)} (rd: {format_binary(rd, 3)}, offset: {format_binary(offset & 0x1F, 5)})")

        return [word1, word2]
    
    elif mnemonic == "CMP_COMP":
        # CMP_COMP (R1)
        return [0b11101 << 3]
        
    elif mnemonic == "LOAD_COMP":
        # LOAD_COMP (R1)
        return [0b11110 << 3]
        
    elif mnemonic == "STEP_COMP":
        # STEP_COMP (R1)
        return [0b11111 << 3]
    
    elif mnemonic == "GOOD":
        return [0b11010 << 3]
    
    elif mnemonic == "BAD":
        return [0b11011 << 3]

    else:
        assert False, "Unknown instruction: " + mnemonic


def parse_register(reg):
    reg = reg.upper()
    assert reg.startswith("R"), "Invalid register format: " + reg
    try:
        num = int(reg[1:])
    except Exception:
        assert False, "Invalid register number in: " + reg
    assert 0 <= num <= 7, "Register number must be between 0 and 7"
    return num


def parse_ascii_char(char_str):
    """Parse a single-quoted ASCII character into its byte value"""
    if not (char_str.startswith("'") and char_str.endswith("'")):
        return None
    char = char_str[1:-1]
    if len(char) != 1:
        return None
    return ord(char)

def parse_directive(line):
    """Parse assembly directives like .data(ADDR) HEX..."""
    line = line.strip()
    if not line.startswith('.'):
        return None
        
    # Match .data(number) directive with optional hex data or ASCII chars
    match = re.match(r'\.data\((\d+)\)((?:\s+(?:[0-9A-Fa-f]{2}|\'[^\']\'))*)', line)
    if match:
        try:
            addr = int(match.group(1))
            # Parse hex data or ASCII chars if present
            data = []
            if match.group(2):
                tokens = match.group(2).strip().split()
                for token in tokens:
                    if token.startswith("'"):
                        ascii_val = parse_ascii_char(token)
                        if ascii_val is None:
                            assert False, f"Invalid ASCII character in data: {token}"
                        data.append(ascii_val)
                    else:
                        data.append(int(token, 16))
            return ('data', addr, data)
        except ValueError:
            assert False, f"Invalid address or data in .data directive: {line}"
            
    assert False, f"Unknown directive: {line}"

def assemble_file(infile, debug=False):
    # Read all lines from file
    with open(infile, 'r') as f:
        lines = f.readlines()
    
    # First pass: collect all labels
    labels = collect_labels(lines)
    if debug:
        print("Labels collected:", labels)
    
    # Second pass: assemble instructions
    result = []
    current_pos = 0
    data_sections = []  # List of (addr, data) tuples for all .data sections
    
    # First collect all instructions to check total code size
    instructions = []
    for line_no, line in enumerate(lines, start=1):
        try:
            # First check if line is a directive
            line = line.split(';')[0].strip()  # Remove comments
            if not line:
                continue
                
            if line.startswith('.'):
                directive = parse_directive(line)
                if directive[0] == 'data':
                    data_addr = directive[1]
                    data_bytes = directive[2]
                    data_sections.append((data_addr, data_bytes))
                continue
            
            # Skip label definitions (they're already processed)
            if line.endswith(':'):
                continue
                
            words = assemble_line(line, labels, current_pos, debug)
            if words is not None:
                instructions.extend(words)
                current_pos += len(words)
                
        except AssertionError as e:
            assert False, f"Error on line {line_no}: {line.strip()} -> {e}"

    # Sort data sections by address
    data_sections.sort(key=lambda x: x[0])
    
    # Check for overlaps between data sections
    for i in range(1, len(data_sections)):
        prev_addr, prev_data = data_sections[i-1]
        curr_addr, _ = data_sections[i]
        if prev_addr + len(prev_data) > curr_addr:
            assert False, f"Error: Data section at address {prev_addr} overlaps with data section at address {curr_addr}"
    
    # Check if code would overlap with first data section
    code_size = len(instructions)
    if data_sections and code_size > data_sections[0][0]:
        assert False, f"Error: Code section (size {code_size}) would overlap with .data section at address {data_sections[0][0]}"
    
    # Now assemble for real
    result.extend(instructions)
    
    # Process all data sections
    for addr, data in data_sections:
        # Pad with zeros up to this data section
        assert len(result) <= addr, f"Error: Previous sections (size {len(result)}) would overlap with .data section at address {addr}"
        while len(result) < addr:
            result.append(0)
        # Append data section
        result.extend(data)
    
    if debug:
        data_size = sum(len(data) for _, data in data_sections)
        print(f"Loaded {len(result)} words total ({code_size} code + {data_size} data)")
    
    return result


def format_hex(words, debug=False):
    if debug:
        lines = []
        for i, w in enumerate(words):
            hex_str = f"{w:02X}"
            bin_str = format_binary(w)
            lines.append(f"{i:3d}: {hex_str} ({bin_str})")
        return "\n".join(lines)
    else:
        # Format as 8 bytes per line with spaces between bytes
        lines = []
        current_line = []
        for w in words:
            current_line.append(f"{w:02X}")
            if len(current_line) == 8:
                lines.append(" ".join(current_line))
                current_line = []
        # Handle any remaining bytes
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Assemble code for the 8-bit CPU')
    parser.add_argument('input', help='Input assembly file')
    parser.add_argument('output', nargs='?', help='Output hex file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    try:
        words = assemble_file(args.input, args.debug)
    except AssertionError as e:
        print(f"Assembly error: {e}")
        sys.exit(1)

    output_str = format_hex(words, args.debug)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_str)
    else:
        print(output_str)


def disassemble_instruction(mem, pc):
    """Disassemble a single instruction at pc"""
    if pc >= len(mem):
        return None, 0
        
    word1 = mem[pc]
    opcode = (word1 >> 3) & 0x1F
    rs = word1 & 0x7
    
    if opcode == 0b00001:  # LOADI
        if pc + 1 >= len(mem):
            return None, 0
        imm = mem[pc + 1]
        if rs == 0:
            return f"JMP 0x{imm:02x}", 2
        else:
            return f"LOADI R{rs}, 0x{imm:02x}", 2
            
    elif opcode == 0b00010:  # MOV
        if pc + 1 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        rd = (word2 >> 5) & 0x7
        imm = word2 & 0x1F
        if imm & 0x10:  # Sign extend 5-bit value
            imm = imm - 32
        if imm == 0:
            return f"MOV R{rd}, R{rs}", 2
        elif imm > 0:
            return f"MOV R{rd}, R{rs} + {imm}", 2
        else:
            return f"MOV R{rd}, R{rs} - {-imm}", 2
            
    elif opcode == 0b00011:  # JZ/JNZ
        if pc + 1 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        is_jnz = (word2 >> 7) & 1
        target = word2 & 0x7F
        mnemonic = "JNZ" if is_jnz else "JZ"
        return f"{mnemonic} 0x{target:02x}, R{rs}", 2

    elif opcode == 0b01010:  # JLT
        if pc + 1 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        rd = (word2 >> 5) & 0x7
        target = word2 & 0x7F
        return f"JLT 0x{target:02x}, R{rs}, R{rd}", 2

    elif opcode == 0b00100:  # ADD/SUB
        if pc + 1 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        rd = (word2 >> 5) & 0x7
        is_sub = (word2 >> 4) & 0x1  # Sign bit determines ADD vs SUB
        imm = word2 & 0xF  # 4-bit immediate
        if imm == 0:
            return f"{'SUB' if is_sub else 'ADD'} R{rd}, R{rs}", pc + 2
        else:
            return f"{'SUB' if is_sub else 'ADD'} R{rd}, R{rs}, {imm}", pc + 2
            
    elif opcode == 0b00101:  # LOAD
        if pc + 1 >= len(mem) or pc + 2 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        rd = (word2 >> 5) & 0x7
        offset = word2 & 0x1F
        if rs == 7:  # Absolute addressing
            return f"LOAD R{rd}, {offset}", pc + 2
        else:
            # Sign extend 5-bit offset
            if offset & 0x10:  # If sign bit is set
                offset = offset - 32  # Convert to negative
            if offset == 0:
                return f"LOAD R{rd}, (R{rs})", pc + 2
            else:
                return f"LOAD R{rd}, {offset}(R{rs})", pc + 2
            
    elif opcode == 0b00110:  # STORE
        if pc + 1 >= len(mem) or pc + 2 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        rd = (word2 >> 5) & 0x7
        offset = word2 & 0x1F
        if rd == 7:  # Absolute addressing
            return f"STORE {offset}, R{rs}", pc + 2
        else:
            # Sign extend 5-bit offset
            if offset & 0x10:  # If sign bit is set
                offset = offset - 32  # Convert to negative
            if offset == 0:
                return f"STORE (R{rd}), R{rs}", pc + 2
            else:
                return f"STORE {offset}(R{rd}), R{rs}", pc + 2
            
    elif opcode == 0b00111:  # MUL
        return f"MUL R{rs}", pc + 1

    elif opcode == 0b01000:  # SHR
        if pc + 1 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        return f"SHR {word2}", pc + 2

    elif opcode == 0b01001:  # MOD
        if pc + 1 >= len(mem):
            return None, 0
        word2 = mem[pc + 1]
        return f"MOD R{rs}", pc + 2

    else:
        print(f"Unknown opcode: {opcode}")

    return None, pc + 1  # Unknown opcode

def disassemble_memory(mem, start_pc=0, num_instructions=None):
    """Disassemble memory contents starting from start_pc.
    Returns list of (pc, instruction_str) tuples.
    """
    result = []
    pc = start_pc
    count = 0
    
    while pc < len(mem):
        if num_instructions is not None and count >= num_instructions:
            break
            
        instr, next_pc = disassemble_instruction(mem, pc)
        if instr is None:
            break
            
        result.append((pc, instr))
        pc = next_pc
        count += 1
        
    return result


if __name__ == '__main__':
    main() 