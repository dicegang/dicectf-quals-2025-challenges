#!/usr/bin/env python3
import json
import copy
import sys
import os
import subprocess
import re
from collections import Counter

def find_max_port_number(module):
    max_port = 0
    for port in module['ports'].values():
        for bit in port['bits']:
            if isinstance(bit, int):
                max_port = max(max_port, bit)
    
    for cell in module['cells'].values():
        connections = cell['connections']
        for conn_list in connections.values():
            for bit in conn_list:
                if isinstance(bit, int):
                    max_port = max(max_port, bit)
    return max_port

def extract_module_name(verilog_file):
    with open(verilog_file, 'r') as f:
        content = f.read()
    match = re.search(r'module\s+(\w+)\s*[#(]?', content)
    if not match:
        raise ValueError("No module declaration found")
    return match.group(1)

def parse_input(value):
    if isinstance(value, str):
        if value == "0":
            return 0
        raise TypeError(f"String input '{value}' is not '0'")
    if isinstance(value, int):
        return value
    raise TypeError(f"Input must be string or int, got {type(value)}")

def convert_nand_to_nor(json_data):
    result = {}
    for module_name, module in json_data['modules'].items():
        result[module_name] = {
            "ports": copy.deepcopy(module['ports']),
            "cells": {}
        }
        
        for cell_name, cell in module['cells'].items():
            gate_type = cell['type']
            # Convert NOT to NOR1 and NOR to NOR2
            if gate_type == 'NOT':
                gate_type = 'NOR1'
            elif gate_type == 'NOR':
                gate_type = 'NOR2'
            
            assert gate_type.startswith('NOR') or gate_type == 'DFF_P', f"Unknown gate type '{gate_type}' found in cell '{cell_name}'"
            
            if gate_type.startswith('NOR'):
                assert len(gate_type) in [4, 5], f"Invalid NOR gate '{gate_type}' in cell '{cell_name}'. Must be NOR1-NOR99"
                num_inputs = int(gate_type[3:])
                assert 1 <= num_inputs <= 99, f"Invalid NOR gate '{gate_type}' in cell '{cell_name}'. Number must be between 1 and 99"
            
            connections = cell['connections']
            inputs = []
            output = connections['Q' if gate_type == 'DFF_P' else 'Y'][0]
            assert isinstance(output, int), f"Output pin must be a number in cell {cell_name}"
            
            if gate_type.startswith('NOR'):
                # Get all input pins (everything except 'Y')
                input_pins = [pin for pin in connections.keys() if pin != 'Y']
                assert len(input_pins) == num_inputs, f"NOR gate '{gate_type}' expects {num_inputs} inputs but got {len(input_pins)}"
                for pin in input_pins:
                    input_val = parse_input(connections[pin][0])
                    inputs.append(input_val)
            elif gate_type == 'DFF_P':
                # Clock first, then data
                clock = parse_input(connections['C'][0])
                data = parse_input(connections['D'][0])
                inputs = [clock, data]
            
            result[module_name]["cells"][cell_name] = {
                "type": gate_type,
                "input": inputs,
                "output": [output]
            }
    
    return result

def generate_yosys_script(input_file, output_json, synth_type):
    module_name = extract_module_name(input_file)
    script = f"""read -sv {input_file}
hierarchy -top {module_name}
check
clean
proc
fsm; opt
memory; opt
techmap
synth
dfflibmap -liberty options/{synth_type}.v
abc -liberty options/{synth_type}.v
techmap -map all2nor.v

freduce
opt
opt_clean

check
stat
proc_init
json -o {output_json}"""

    script_path = 'synth.ys'
    with open(script_path, 'w') as f:
        f.write(script)
    return script_path

def process_verilog_file(input_file, output_dir, synth_type):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_json = os.path.join(output_dir, f"{base_name}_{synth_type}.json")
    output_nor_json = os.path.join(output_dir, f"{base_name}_{synth_type}_final.json")
    
    script_path = generate_yosys_script(input_file, output_json, synth_type)
    result = subprocess.run(['yosys', '-q', script_path], capture_output=True, text=True)
    os.remove(script_path)
    
    if result.returncode != 0:
        sys.stderr.write(f"Error during synthesis of {input_file}:\n{result.stderr}\n")
        return
    
    with open(output_json, 'r') as f:
        json_data = json.load(f)
    
    gate_counts = Counter()
    total_gates = 0
    for module in json_data['modules'].values():
        for cell in module['cells'].values():
            gate_counts[cell['type']] += 1
            total_gates += 1
    
    print("\nGate counts before conversion:")
    for gate_type, count in sorted(gate_counts.items()):
        print(f"- {gate_type}: {count}")
    print(f"Total gates: {total_gates}")
    
    print("\nConverting to NOR+DFF_P...")
    converted_data = convert_nand_to_nor(json_data)
    
    with open(output_nor_json, 'w') as f:
        json.dump(converted_data, f, indent=2)
    
    print(f"\nOutputs written to:")
    print(f"- {output_json}")
    print(f"- {output_nor_json}")

def process_directory(input_path, synth_type):
    output_dir = os.path.join(os.path.dirname(input_path), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.v'):
                input_file = os.path.join(root, file)
                process_verilog_file(input_file, output_dir, synth_type)

def main():
    if len(sys.argv) != 3:
        sys.stderr.write(f"Usage: {sys.argv[0]} <input_file_or_directory> <synth_type>\n")
        sys.exit(1)
    
    input_path = os.path.abspath(sys.argv[1])
    synth_type = sys.argv[2]
    
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Path {input_path} not found\n")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(os.path.dirname(input_path), 'options', f'{synth_type}.v')):
        sys.stderr.write(f"Error: Synthesis type {synth_type} not found in options directory\n")
        sys.exit(1)
    
    if os.path.isdir(input_path):
        process_directory(input_path, synth_type)
    else:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(input_path)), 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        process_verilog_file(input_path, output_dir, synth_type)

if __name__ == "__main__":
    main() 