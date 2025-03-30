#!/usr/bin/env python3
import json
from typing import Dict, List, Union, Optional

class CircuitSimulator:
    def __init__(self, json_path: str):
        """Initialize simulator with synthesized circuit JSON"""
        with open(json_path) as f:
            self.circuit = json.load(f)
        self.reset()
        
    def reset(self):
        """Reset the circuit state"""
        self.state = {}  # Tracks current state of all wires
        self.dff_states = {}  # Tracks D flip-flop states
        self.dff_next_states = {}  # Tracks next state latched on rising edge
        
        # Set all outputs and internal wires to 0
        module = self.circuit[list(self.circuit.keys())[0]]
        for port in module["ports"].values():
            for bit in port["bits"]:
                if isinstance(bit, int):
                    self.state[bit] = 0
                    
        # Initialize all wires used in cells to 0
        for cell in module["cells"].values():
            if cell["type"].startswith("NOR"):
                for wire in cell["input"]:
                    if wire not in self.state:
                        self.state[wire] = 0
                for wire in cell["output"]:
                    if wire not in self.state:
                        self.state[wire] = 0
            elif cell["type"] == "DFF_P":
                for wire in cell["input"]:
                    if wire not in self.state:
                        self.state[wire] = 0
                for wire in cell["output"]:
                    if wire not in self.state:
                        self.state[wire] = 0
                self.dff_states[cell["output"][0]] = 0
                self.dff_next_states[cell["output"][0]] = 0
        
    def _evaluate_nor(self, inputs: List[int]) -> int:
        """Evaluate a NOR gate with given inputs"""
        return 1 if all(self.state.get(i, 0) == 0 for i in inputs) else 0
        
    def _update_dff(self, clk: int, d: int, q: int):
        """Update D flip-flop state on clock edges"""
        if clk == 1:  # Rising edge
            # Latch input value
            self.dff_next_states[q] = d
        else:  # Falling edge
            # Update output with latched value
            self.dff_states[q] = self.dff_next_states[q]
            self.state[q] = self.dff_states[q]

    def _evaluate_combinational(self) -> bool:
        """Evaluate all combinational logic (NOR gates) until settled.
        Returns True if any changes were made."""
        module = self.circuit[list(self.circuit.keys())[0]]
        changed = False
        
        # Evaluate all NOR gates
        for cell in module["cells"].values():
            if cell["type"].startswith("NOR"):
                out = self._evaluate_nor(cell["input"])
                if self.state.get(cell["output"][0], 0) != out:
                    self.state[cell["output"][0]] = out
                    changed = True
        
        return changed
            
    def step(self, inputs: Dict[str, List[int]], reset: bool = False) -> Dict[str, List[int]]:
        """Simulate one clock cycle"""
        if reset:
            self.reset()
            return {name: [0] * len(port["bits"]) 
                   for name, port in self.circuit[list(self.circuit.keys())[0]]["ports"].items() 
                   if port["direction"] == "output"}
            
        # Set input values
        for port_name, values in inputs.items():
            port = self.circuit[list(self.circuit.keys())[0]]["ports"][port_name]
            for bit, value in zip(port["bits"], values):
                self.state[bit] = value
                
        # Evaluate combinational logic until settled
        while self._evaluate_combinational():
            pass
                
        # Update DFFs
        for cell in self.circuit[list(self.circuit.keys())[0]]["cells"].values():
            if cell["type"] == "DFF_P":
                self._update_dff(
                    self.state.get(cell["input"][0], 0),  # Clock
                    self.state.get(cell["input"][1], 0),  # Data
                    cell["output"][0]              # Output
                )
                
        # Evaluate combinational logic again after DFF updates
        while self._evaluate_combinational():
            pass
                
        # Collect outputs
        outputs = {}
        for port_name, port in self.circuit[list(self.circuit.keys())[0]]["ports"].items():
            if port["direction"] == "output":
                outputs[port_name] = [self.state.get(b, 0) if isinstance(b, int) else 0 
                                    for b in port["bits"]]
                
        return outputs 