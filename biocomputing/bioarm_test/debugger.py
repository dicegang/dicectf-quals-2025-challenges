#!/usr/bin/env python3
import argparse
import json
import sys
import os
import grpc
import time
import logging
import gzip
import base64
from pathlib import Path

# Add the bioarm directory to the Python path to import the generated protobuf files
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bioarm'))
# Add harness to Python path to import circuit compilation code
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'harness'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'assembler'))

import bioarm_pb2
import bioarm_pb2_grpc
from circuit import Circuit, circuit_to_model
from model import XMLWriter
from assembler import disassemble_instruction

def parse_assertion(comment):
    """Parse an assertion from a comment if present"""
    if not comment:
        return None
    comment = comment.strip()
    if comment.upper().startswith('ASSERT'):
        # Extract the assertion part
        assertion = comment[6:].strip()  # Remove 'ASSERT' prefix
        # Parse register and expected value
        try:
            reg, value = assertion.split('=')
            reg = reg.strip()
            value = int(value.strip(), 0)  # Parse as int, supporting hex/binary/decimal
            return (reg, value)
        except:
            return None
    return None

def load_hex_file(hex_path):
    """Load and parse a hex file into a list of binary instructions"""
    with open(hex_path, 'r') as f:
        # Read all lines and join them, then split on whitespace to get all hex bytes
        hex_bytes = f.read().strip().replace('\n', ' ').split()
    
    # Convert hex strings to binary
    rom_data = []
    for hex_byte in hex_bytes:
        binary = bin(int(hex_byte, 16))[2:].zfill(8)  # Convert to 8-bit binary
        rom_data.append(binary)
    
    return rom_data

def load_asm_file(asm_path):
    """Load and parse an assembly file into a list of instructions and their assertions"""
    instructions_with_assertions = []
    with open(asm_path, 'r') as f:
        for line in f:
            # Split into instruction and comment
            parts = line.split(';', 1)
            instruction = parts[0].strip()
            comment = parts[1].strip() if len(parts) > 1 else ""
            
            if instruction:  # Only add non-empty lines
                assertion = parse_assertion(comment)
                instructions_with_assertions.append((instruction, assertion))
    return instructions_with_assertions

def format_memory_values(memory_values, prev_memory_values=None):
    """Format memory values in a clean layout with color highlighting"""
    CYAN = "\033[36m"    # For nonzero values
    GREEN = "\033[32m"   # For values that changed
    RED = "\033[31m"     # For register separator
    RESET = "\033[0m"
    
    values = []
    for addr in range(32):
        value = memory_values.get(f'mem[{addr}]', 0)
        prev_value = prev_memory_values.get(f'mem[{addr}]', 0) if prev_memory_values else 0
        
        # Determine color based on value and whether it changed
        if value != prev_value and prev_memory_values is not None:
            color = GREEN  # Changed values in green
        elif value != 0:
            color = CYAN  # Nonzero values in cyan
        else:
            color = ""   # Zero values in default color
            
        values.append(f"{color}{value:02x}{RESET}" if color else f"{value:02x}")
        
        # Add separator after registers (first 8 values)
        if addr == 7:
            values.append(f"{RED}|{RESET}")
    
    return ["    Memory: " + " ".join(values)]

def format_memory_values_pretty(memory_values, prev_memory_values=None):
    """Format memory values in a prettier layout with registers at top and memory in rows"""
    CYAN = "\033[36m"    # For nonzero values
    GREEN = "\033[32m"   # For values that changed
    RED = "\033[31m"     # For register separator
    RESET = "\033[0m"
    
    output_lines = []
    
    # Format registers (first 8 bytes of memory)
    reg_values = []
    for addr in range(8):
        value = memory_values.get(f'mem[{addr}]', 0)
        prev_value = prev_memory_values.get(f'mem[{addr}]', 0) if prev_memory_values else 0
        
        # Determine color based on value and whether it changed
        if value != prev_value and prev_memory_values is not None:
            color = GREEN  # Changed values in green
        elif value != 0:
            color = CYAN  # Nonzero values in cyan
        else:
            color = ""   # Zero values in default color
            
        reg_values.append(f"R{addr}={color}0x{value:02x}{RESET}" if color else f"R{addr}=0x{value:02x}")
    
    output_lines.append("    Registers: " + " ".join(reg_values))
    
    # Format memory (in rows of 16 bytes)
    for row in range(2):  # 32 bytes total, 16 bytes per row
        row_values = []
        for col in range(16):
            addr = row * 16 + col + 8
            value = memory_values.get(f'mem[{addr}]', 0)
            prev_value = prev_memory_values.get(f'mem[{addr}]', 0) if prev_memory_values else 0
            
            # Determine color based on value and whether it changed
            if value != prev_value and prev_memory_values is not None:
                color = GREEN  # Changed values in green
            elif value != 0:
                color = CYAN  # Nonzero values in cyan
            else:
                color = ""   # Zero values in default color
                
            row_values.append(f"{color}{value:02x}{RESET}" if color else f"{value:02x}")
        
        addr_start = row * 16 + 8
        addr_end = addr_start + 15
        output_lines.append(f"    Memory [{addr_start:02x}-{addr_end:02x}]: " + " ".join(row_values))
    
    return output_lines

# ANSI color codes
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"
BOLD = "\033[1m"

def load_circuit(hex_path):
    # Load assembly file corresponding to hex file
    asm_path = hex_path.replace('/bin/', '/asm/').replace('.hex', '.asm')
    try:
        instructions_with_assertions = load_asm_file(asm_path)
        print(f'Loaded {len(instructions_with_assertions)} instructions from assembly file')
    except Exception as e:
        print(f'Warning: Could not load assembly file {asm_path}: {e}')
        instructions_with_assertions = None

    # Compile circuit to SBML
    print("Compiling circuit to SBML...")

    cpu_path = os.path.join(os.path.dirname(__file__), '..', 'verilog', 'outputs', 'cpu_dff_nor_final.json')
    cpu_meta = os.path.join(os.path.dirname(__file__), '..', 'verilog', 'outputs', 'cpu_dff_nor.json')
    cpu_meta = json.load(open(cpu_meta, 'r'))

    # Load circuit from JSON file
    circuit = Circuit.load_from_json(cpu_path)
    inputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'input'}
    outputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'output'}

    # Get memory bits
    memory = {
        f'mem[{idx}]': cpu_meta['modules']['cpu']['netnames'][f'memory[{idx}]']['bits'][::-1]
        for idx in range(32)
    }

    # Registers are first 8 bytes of memory
    registers = {
        f'R{idx}': memory[f'mem[{idx}]']
        for idx in range(8)
    }

    return circuit, inputs, outputs, memory, registers, instructions_with_assertions

def initialize_system(stub, sbml_model):
    print("\n=== Initializing System ===")
    # Compress SBML with gzip and encode as base64
    compressed_sbml = gzip.compress(sbml_model.encode('utf-8'))
    encoded_sbml = base64.b64encode(compressed_sbml).decode('ascii')

    response = stub.InitializeSystem(bioarm_pb2.InitializeRequest(sbml_string=encoded_sbml))
    if not response.success:
        print(f"Failed to initialize system: {response.error_message}")
        return
    print("System initialized successfully")

def initialize_rom(stub, inputs, rom_data):
    print("\n=== Initializing ROM ===")
    rom_species = []
    rom_scavengers = []
    
    # Assuming ROM input bits are named rom_0, rom_1, etc.
    rom_bits = inputs.get('rom', [])
    if not rom_bits:
        print("Error: Circuit does not have ROM input")
        return
        
    # Set ROM data bits
    for i, bit in enumerate(rom_bits):
        # Calculate which byte and bit position we need
        byte_index = i // 8
        bit_index = 7 - (i % 8)  # MSB first within each byte
        
        # Get the bit value from the appropriate byte
        if byte_index < len(rom_data):
            bit_value = int(rom_data[byte_index][bit_index])
        else:
            bit_value = 0
            
        if bit_value:
            rom_species.append(f"p_{bit}")
        else:
            rom_scavengers.append(f"p_{bit}")
    
    response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
        species=rom_species,
        scavengers=rom_scavengers
    ))
    print("ROM data initialized")


def run_cpu_simulation(hex_path, num_cycles, cycle_ticks=3):
    """
    Run CPU simulation using the bioarm RPC service
    
    Args:
        hex_path: Path to the hex file containing ROM data
        num_cycles: Number of cycles to run
        cycle_ticks: Number of simulation ticks per cycle
    """
    circuit, inputs, outputs, memory, registers, instructions_with_assertions = load_circuit(hex_path)

    model = circuit_to_model(circuit)
    xml = XMLWriter(model)
    sbml_model = xml.write()
    
    print('Found inputs:', list(inputs.keys()))
    print('Found outputs:', list(outputs.keys()))
    
    # Load ROM data
    rom_data = load_hex_file(hex_path)
    print(f'Loaded {len(rom_data)} instructions from hex file')
    
    # Create gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = bioarm_pb2_grpc.BioArmStub(channel)
        
        initialize_system(stub, sbml_model)
        initialize_rom(stub, inputs, rom_data)
        
        # Run simulation cycles
        clock_bit = inputs.get('clk', [])[0]  # Get the clock bit
        reset_bit = inputs.get('rst', [])[0]  # Get the reset bit
        if not clock_bit:
            print("Error: Circuit does not have clock input")
            return
        if not reset_bit:
            print("Error: Circuit does not have reset input")
            return
            
        # Reset sequence
        print("\n=== Reset Sequence ===")
        # Set reset high
        response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
            species=[f"p_{reset_bit}"],
            scavengers=[]
        ))
        
        # Cycle clock a few times with reset high
        for _ in range(3):  # 3 cycles should be enough to ensure reset
            # Clock high
            response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
                species=[f"p_{clock_bit}", f"p_{reset_bit}"],
                scavengers=[]
            ))
            response = stub.Delay(bioarm_pb2.DelayRequest(seconds=cycle_ticks))
            
            # Clock low
            response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
                species=[f"p_{reset_bit}"],
                scavengers=[f"p_{clock_bit}"]
            ))
            response = stub.Delay(bioarm_pb2.DelayRequest(seconds=cycle_ticks))
        
        # Set reset low
        response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
            species=[],
            scavengers=[f"p_{reset_bit}"]
        ))
        print("Reset complete")
            
        print(f"\n=== Running {num_cycles} cycles ===")
        prev_memory_values = None
        prev_pc = 0  # Track previous PC value for instruction disassembly
        for cycle in range(num_cycles):
            
            # Clock high
            response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
                species=[f"p_{clock_bit}"],
                scavengers=[]
            ))
            response = stub.Delay(bioarm_pb2.DelayRequest(seconds=cycle_ticks))
            
            # Clock low
            response = stub.PipetteIn(bioarm_pb2.PipetteRequest(
                species=[],
                scavengers=[f"p_{clock_bit}"]
            ))
            response = stub.Delay(bioarm_pb2.DelayRequest(seconds=cycle_ticks))
            
            # Store previous register values for change detection
            prev_reg_values = {}
            if cycle > 0:
                for reg_value in prev_cycle_reg_values:
                    reg, value = reg_value.split('=')
                    prev_reg_values[reg] = int(value, 16)
            
            # Read and format register values
            reg_values = []
            current_reg_values = {}  # Store current values for next cycle
            for reg_name, reg_bits in registers.items():
                species_to_read = [f"p_{bit}" for bit in reg_bits]
                response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=species_to_read))
                
                # Convert concentrations to digital values
                digital_values = []
                for bit in reg_bits:
                    conc = response.concentrations[f"p_{bit}"]
                    digital_values.append(1 if conc > 5 else 0)
                
                # Convert binary to integer
                value = sum(v << i for i, v in enumerate(reversed(digital_values)))
                reg_values.append(f"{reg_name}=0x{value:02x}")
                current_reg_values[reg_name] = value

            # Store previous memory values for change detection
            prev_memory_values = memory_values if 'memory_values' in locals() else None
            
            # Read memory values
            memory_values = {}
            for addr in range(32):  # Read all 32 bytes of memory
                mem_bits = memory[f'mem[{addr}]']
                species_to_read = [f"p_{bit}" for bit in mem_bits]
                response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=species_to_read))
                
                # Convert concentrations to digital values
                digital_values = []
                for bit in mem_bits:
                    conc = response.concentrations[f"p_{bit}"]
                    digital_values.append(1 if conc > 5 else 0)
                
                # Convert binary to integer
                value = sum(v << i for i, v in enumerate(reversed(digital_values)))
                memory_values[f'mem[{addr}]'] = value

            # Read circuit outputs
            out_values = []
            for output_name, bits in outputs.items():
                species_to_read = [f"p_{bit}" for bit in bits]
                response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=species_to_read))
                
                if len(bits) > 1:
                    # Multi-bit output
                    digital_values = []
                    for bit in bits:
                        conc = response.concentrations[f"p_{bit}"]
                        digital_values.append(1 if conc > 5 else 0)
                    value = sum(v << i for i, v in enumerate(reversed(digital_values)))
                    out_values.append(f"{output_name}=0x{value:02x}")
                else:
                    # Single-bit output
                    conc = response.concentrations[f"p_{bits[0]}"]
                    digital_value = 1 if conc > 5 else 0
                    out_values.append(f"{output_name}={digital_value}")
            
            # Print cycle number, current instruction (if available), register values, and outputs
            cycle_info = [f"{BOLD}Cycle {cycle}:{RESET}"]
            
            # Get current instruction by disassembling from previous PC
            pc = memory_values.get('mem[0]', 0)  # R0 is PC
            rom_bytes = [int(byte, 2) for byte in rom_data]  # Convert binary strings to integers
            result = disassemble_instruction(rom_bytes, prev_pc)
            if result:
                current_instruction, _ = result
                cycle_info.append(f"{CYAN}[{current_instruction}]{RESET}")
            
            # Store PC for next cycle
            prev_pc = pc
            
            cycle_info.extend([f"{YELLOW}{' '.join(reg_values)}{RESET}", '|', ' '.join(out_values)])
            print(' '.join(cycle_info))
            
            # Print memory values
            for line in format_memory_values(memory_values, prev_memory_values):
                print(line)
            
            # Validate assertions
            if instructions_with_assertions and cycle < len(instructions_with_assertions):
                _, current_assertion = instructions_with_assertions[cycle]
                if current_assertion:
                    asserted_reg, expected_value = current_assertion
                    # Check the asserted register value
                    actual_value = current_reg_values.get(asserted_reg)
                    if actual_value is not None:
                        assertion_passed = actual_value == expected_value
                        status = f"{GREEN}✓ PASS{RESET}" if assertion_passed else f"{RED}✗ FAIL{RESET}"
                        print(f"    Assertion: {asserted_reg}={hex(expected_value)} -> {status} (actual: {hex(actual_value)})")
                    
                    # Check that all other registers (except R0) didn't change
                    for reg_name, current_value in current_reg_values.items():
                        if reg_name == 'R0' or reg_name == asserted_reg:
                            continue
                        prev_value = prev_reg_values.get(reg_name)
                        if prev_value is not None and current_value != prev_value:
                            print(f"    Assertion: {reg_name} unchanged -> {RED}✗ FAIL{RESET} (changed from {hex(prev_value)} to {hex(current_value)})")
            
            print()  # Add blank line between cycles
            
            # Store current values for next cycle
            prev_reg_values = current_reg_values
            prev_memory_values = memory_values  # Save current memory values for next cycle
            cycle_count += 1


def run_auto_step(stub, reset_bit, clk_bit):
    stub.Delay(bioarm_pb2.DelayRequest(seconds=1))
    response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=[f"p_{reset_bit}", f"p_{clk_bit}"]))
    return response.concentrations[f'p_{reset_bit}'], response.concentrations[f'p_{clk_bit}']

def run_cpu_simulation_auto(hex_path, num_cycles):
    circuit, inputs, outputs, memory, registers, instructions_with_assertions = load_circuit(hex_path)

    reset_bit = inputs.get('rst', [])[0]
    if not reset_bit:
        print("Error: Circuit does not have reset input")
        return
    
    clk_bit = inputs.get('clk', [])[0]
    if not clk_bit:
        print("Error: Circuit does not have clock input")
        return

    model = circuit_to_model(circuit, auto_clock=clk_bit, auto_reset=reset_bit)
    xml = XMLWriter(model)
    sbml_model = xml.write()
    
    print('Found inputs:', list(inputs.keys()))
    print('Found outputs:', list(outputs.keys()))
    
    # Load ROM data
    rom_data = load_hex_file(hex_path)
    print(f'Loaded {len(rom_data)} instructions from hex file')

    tracking_species = []
    tracking_species += [f"p_{reset_bit}"]
    tracking_species += [f"p_{clk_bit}"]
    for addr in range(32):  # Read all 32 bytes of memory
        mem_bits = memory[f'mem[{addr}]']
        species_to_read = [f"p_{bit}" for bit in mem_bits]
        tracking_species += species_to_read

    # Create gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = bioarm_pb2_grpc.BioArmStub(channel)
        
        initialize_system(stub, sbml_model)
        initialize_rom(stub, inputs, rom_data)

        last_time = time.time()
        last_clk = False
        cycle_count = 0
        prev_reg_values = {}  # Track previous register values for assertions
        prev_memory_values = None  # Track previous memory values for highlighting changes
        reset_done = False  # Track when reset sequence is complete
        t = 0
        last_pc = 0
        while True:
            t += 1

            if cycle_count > num_cycles:
                break

            show = False
            rst, clk = run_auto_step(stub, reset_bit, clk_bit)
            m = time.time() - last_time
            last_time = time.time()
            line = f'({m:.2f}s)[t={t}] '
            if rst > 0.5:
                line += f'{RED}[RST]{RESET} '
                reset_done = False  # Reset is active, so we're not done with reset
            elif not reset_done and rst < 0.5:
                reset_done = True  # Reset just went low, now we'll start counting on next clock
                line += f'{GREEN}[RESET COMPLETE]{RESET} '
            
            if clk > 0.5 and not last_clk:
                line += f'{CYAN}[HI]{RESET} '
            elif clk < 0.5 and last_clk:
                line += f'{RED}[LOW]{RESET} '
                # Only show and count cycles if reset is done
                if reset_done:
                    show = True
            last_clk = clk > 0.5
            # print(line)

            if show:
                # Read and format register values
                reg_values = []
                current_reg_values = {}  # Store current values for next cycle
                for reg_name, reg_bits in registers.items():
                    species_to_read = [f"p_{bit}" for bit in reg_bits]
                    response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=species_to_read))
                    
                    # Convert concentrations to digital values
                    digital_values = []
                    for bit in reg_bits:
                        conc = response.concentrations[f"p_{bit}"]
                        digital_values.append(1 if conc > 5 else 0)
                    
                    # Convert binary to integer
                    value = sum(v << i for i, v in enumerate(reversed(digital_values)))
                    reg_values.append(f"{reg_name}=0x{value:02x}")
                    current_reg_values[reg_name] = value

                # Read memory values
                memory_values = {}
                for addr in range(32):  # Read all 32 bytes of memory
                    mem_bits = memory[f'mem[{addr}]']
                    species_to_read = [f"p_{bit}" for bit in mem_bits]
                    response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=species_to_read))
                    
                    # Convert concentrations to digital values
                    digital_values = []
                    for bit in mem_bits:
                        conc = response.concentrations[f"p_{bit}"]
                        digital_values.append(1 if conc > 5 else 0)
                    
                    # Convert binary to integer
                    value = sum(v << i for i, v in enumerate(reversed(digital_values)))
                    memory_values[f'mem[{addr}]'] = value

                pc = memory_values.get('mem[0]', 0)  # R0 is PC
                rom_bytes = [int(byte, 2) for byte in rom_data]  # Convert binary strings to integers
                result = disassemble_instruction(rom_bytes, last_pc)
                last_pc = pc

                current_instruction = ''
                if result:
                    current_instruction, _ = result
                if current_instruction is None:
                    current_instruction = '?'

                # Print a blank line before the instruction for better readability
                print()
                # Print the instruction with cyan color for better visibility
                out_line = f'{CYAN}{current_instruction}{RESET}'
                print(out_line)

                # Print memory values
                for line in format_memory_values_pretty(memory_values, prev_memory_values):
                    print(line)

                # Validate assertions if we have them
                if instructions_with_assertions and cycle_count < len(instructions_with_assertions):
                    _, current_assertion = instructions_with_assertions[cycle_count]
                    if current_assertion:
                        asserted_reg, expected_value = current_assertion
                        # Check the asserted register value
                        actual_value = current_reg_values.get(asserted_reg)
                        if actual_value is not None:
                            assertion_passed = actual_value == expected_value
                            status = f"{GREEN}✓ PASS{RESET}" if assertion_passed else f"{RED}✗ FAIL{RESET}"
                            print(f"    Assertion: {asserted_reg}={hex(expected_value)} -> {status} (actual: {hex(actual_value)})")
                        
                        # Check that all other registers (except R0) didn't change
                        for reg_name, current_value in current_reg_values.items():
                            if reg_name == 'R0' or reg_name == asserted_reg:
                                continue
                            prev_value = prev_reg_values.get(reg_name)
                            if prev_value is not None and current_value != prev_value:
                                print(f"    Assertion: {reg_name} unchanged -> {RED}✗ FAIL{RESET} (changed from {hex(prev_value)} to {hex(current_value)})")

                # Check if we've hit output
                out_flag = memory_values.get('mem[8]', 0)
                if out_flag > 0:
                    print(f'{GREEN}Output flag hit!{RESET}')
                    out_str = ''
                    for addr in range(8, 32):
                        out_str += chr(memory_values[f'mem[{addr}]'])
                    out_str = out_str[:out_str.index('\x00')]
                    print(f'Output: {out_str}')
                    break

                # Store current values for next cycle
                prev_reg_values = current_reg_values
                prev_memory_values = memory_values  # Save current memory values for next cycle
                cycle_count += 1


def main():
    parser = argparse.ArgumentParser(description='Run CPU simulation via bioarm RPC')
    parser.add_argument('hex_file', help='Path to hex file containing ROM data')
    parser.add_argument('cycles', type=int, help='Number of cycles to run')
    parser.add_argument('--auto', action='store_true', help='Use automatic clock and reset')
    
    args = parser.parse_args()
    
    try:
        if args.auto:
            run_cpu_simulation_auto(args.hex_file, args.cycles)
        else:
            run_cpu_simulation(args.hex_file, args.cycles)
    except grpc.RpcError as e:
        print(f"RPC failed: {e}")
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()