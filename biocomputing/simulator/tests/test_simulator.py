#!/usr/bin/env python3
import os
import json
import tempfile
from src.simulator import CircuitSimulator

def test_basic_circuit():
    # Create a temporary JSON file with the circuit structure
    circuit_data = {
        "basic": {
            "ports": {
                "inp": {"direction": "input", "bits": [2]},
                "inp2": {"direction": "input", "bits": [1]},
                "res": {"direction": "output", "bits": [3]}
            },
            "cells": {
                "nor1": {
                    "type": "NOR2",  # Two input NOR
                    "input": [2, 1],  # inp and inp2
                    "output": [3]     # res
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(circuit_data, f)
        temp_file = f.name

    try:
        # Initialize simulator with the temporary file
        sim = CircuitSimulator(temp_file)

        # First reset the circuit
        outputs = sim.step({}, reset=True)
        assert outputs["res"] == [0], "Reset should set output to 0"

        # Test cases for the truth table of a NOR gate
        test_cases = [
            ({"inp": [0], "inp2": [0]}, {"res": [1]}),  # 0 NOR 0 = 1
            ({"inp": [0], "inp2": [1]}, {"res": [0]}),  # 0 NOR 1 = 0
            ({"inp": [1], "inp2": [0]}, {"res": [0]}),  # 1 NOR 0 = 0
            ({"inp": [1], "inp2": [1]}, {"res": [0]})   # 1 NOR 1 = 0
        ]

        for inputs, expected_outputs in test_cases:
            outputs = sim.step(inputs)
            assert outputs == expected_outputs, f"Failed for inputs {inputs}"

    finally:
        # Clean up the temporary file
        os.unlink(temp_file)

def int_to_bits(n: int, width: int = 8) -> list:
    """Convert integer to list of bits (LSB first)"""
    return [(n >> i) & 1 for i in range(width)]

def run_fibonacci_test(sim: CircuitSimulator, name: str):
    """Run Fibonacci sequence test on a simulator instance"""
    # Reset should set both outputs to 0
    outputs = sim.step({"clk": [0], "rst": [1]}, reset=True)
    assert outputs["out"] == [0] * 8, "Reset should set out to 0"
    assert outputs["out2"] == [0] * 8, "Reset should set out2 to 0"
    
    # First clock cycle with reset high
    outputs = sim.step({"clk": [1], "rst": [1]})
    
    assert outputs["out"] == [0] * 8, "Reset should set out to 0"
    assert outputs["out2"] == [0] * 8, "Reset should set out2 to 0"
    
    # Clock low, keeping reset high
    outputs = sim.step({"clk": [0], "rst": [0]})

    # Both outputs should be 1 after reset
    assert outputs["out"] == int_to_bits(1), "Reset high should set out to 1"
    assert outputs["out2"] == int_to_bits(1), "Reset high should set out2 to 1"
    
    
    # Start Fibonacci sequence
    # Initial values: out=1, out2=1
    fib_prev = 1  # out
    fib_curr = 1  # out2
    
    # Test first 10 steps of Fibonacci sequence
    for i in range(10):
        # Rising edge, no reset
        outputs = sim.step({"clk": [1], "rst": [0]})
        print(f"After clock {i}:", outputs)
        
        # Calculate expected next Fibonacci number
        fib_next = fib_prev + fib_curr
        
        # Clock low
        outputs = sim.step({"clk": [0], "rst": [0]})
        
        # out gets previous out2, out2 gets sum
        assert outputs["out"] == int_to_bits(fib_curr), f"out should be {fib_curr}"
        assert outputs["out2"] == int_to_bits(fib_next), f"out2 should be {fib_next}"
        
        
        # Update expected values
        fib_prev = fib_curr
        fib_curr = fib_next

def test_dff_circuit():
    """Test the DFF circuit with dff_nor synthesis"""
    sim = CircuitSimulator("../verilog/outputs/dff_dff_nor_final.json")
    run_fibonacci_test(sim, "dff_nor synthesis")

def test_dff_all_nor_circuit():
    """Test the DFF circuit with all_nor synthesis"""
    sim = CircuitSimulator("../verilog/outputs/dff_all_nor_final.json")
    run_fibonacci_test(sim, "all_nor synthesis") 