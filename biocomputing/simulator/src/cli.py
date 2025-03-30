#!/usr/bin/env python3
import sys
import json
import argparse
from pathlib import Path
from simulator import CircuitSimulator

def format_bits(bits):
    """Format a list of bits into a binary string with leading zeros."""
    # Reverse the bits for display
    return ''.join(str(b) for b in reversed(bits))

def print_header(text):
    """Print a section header."""
    print(f"\n\033[1;34m=== {text} ===\033[0m")

def print_step_header(cycle, clock):
    """Print a step header."""
    print(f"\n\033[1;36m--- Cycle {cycle}, Clock {clock} ---\033[0m")

def print_outputs(outputs, prefix=""):
    """Pretty print the outputs."""
    for name, bits in outputs.items():
        binary = format_bits(bits)
        # Calculate decimal value from reversed bits for correct value
        decimal = sum(b << i for i, b in enumerate(bits))
        # Calculate signed value (if highest bit is 1, subtract 256)
        signed = decimal if decimal < 128 else decimal - 256
        print(f"{prefix}\033[1;32m{name:>8}\033[0m: {binary} (0x{decimal:02x}, {decimal}, {signed})")

def main():
    parser = argparse.ArgumentParser(description='Simulate synthesized Verilog circuits')
    parser.add_argument('circuit_json', type=str, help='Path to the synthesized circuit JSON file')
    parser.add_argument('--cycles', type=int, default=5, help='Number of clock cycles to simulate')
    args = parser.parse_args()

    # Load circuit
    sim = CircuitSimulator(args.circuit_json)
    module = list(sim.circuit.values())[0]
    
    # Get input port names
    input_ports = [name for name, port in module["ports"].items() 
                  if port["direction"] == "input"]
    
    # Check for clock and reset
    has_clk = "clk" in input_ports
    has_rst = "rst" in input_ports
    
    print_header(f"Starting simulation for {args.cycles} clock cycles")
    
    # Reset circuit for one full clock cycle
    if has_rst:
        print_header("Reset sequence")
        if has_clk:
            for clk in [0, 1]:
                inputs = {"rst": [0]}
                if has_clk:
                    inputs["clk"] = [clk]
                outputs = sim.step(inputs)
                print_step_header("Reset", clk)
                print_outputs(outputs)
            for clk in [0]:
                inputs = {"rst": [1]}
                if has_clk:
                    inputs["clk"] = [clk]
                outputs = sim.step(inputs)
                print_step_header("Reset", clk)
                print_outputs(outputs)
            for clk in [1]:
                inputs = {"rst": [0]}
                if has_clk:
                    inputs["clk"] = [clk]
                outputs = sim.step(inputs)
                print_step_header("Reset", clk)
                print_outputs(outputs)
        else:
            outputs = sim.step({"rst": [1]})
            print_outputs(outputs, "    ")
    else:
        print_header("Initial state")
        outputs = sim.step({}, reset=True)
        print_outputs(outputs, "    ")
    
    # Run simulation
    print_header("Simulation")
    if has_clk:
        # Run for specified number of clock cycles
        for cycle in range(args.cycles):
            for clk_val in [0, 1]:  # Toggle clock
                inputs = {"clk": [clk_val]}
                if has_rst:
                    inputs["rst"] = [0]  # Keep reset de-asserted
                    
                outputs = sim.step(inputs)
                print_step_header(cycle + 1, clk_val)
                print_outputs(outputs, "    ")
    else:
        print("\033[1;33mNo clock signal found in circuit\033[0m")

if __name__ == "__main__":
    main() 