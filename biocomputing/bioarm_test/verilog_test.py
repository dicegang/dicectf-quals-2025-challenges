import argparse
import json
import sys
import os
import grpc
import time
import logging

# Add the bioarm directory to the Python path to import the generated protobuf files
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bioarm'))
# Add harness to Python path to import circuit compilation code
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'harness'))

import bioarm_pb2
import bioarm_pb2_grpc
from circuit import Circuit, circuit_to_model
from model import XMLWriter

def compile_verilog_to_sbml(circuit_path):
    """
    Compile a Verilog circuit JSON file to SBML
    
    Args:
        circuit_path: Path to the Verilog circuit JSON file
    Returns:
        tuple: (sbml_string, inputs_dict, outputs_dict)
    """
    # Parse circuit from JSON
    circuit = Circuit.load_from_json(circuit_path)
    inputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'input'}
    outputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'output'}

    # Create SBML model
    model = circuit_to_model(circuit)
    xml = XMLWriter(model)
    sbml_string = xml.write()
    
    return sbml_string, inputs, outputs

def run_simulation(circuit_path, input_path, cycle_ticks=100):
    """
    Run a simulation using the bioarm RPC service
    
    Args:
        circuit_path: Path to the Verilog circuit JSON file
        input_path: Path to the JSON input file
        cycle_ticks: Number of simulation ticks per cycle
    """
    # Compile circuit to SBML
    print("Compiling circuit to SBML...")
    sbml_model, inputs, outputs = compile_verilog_to_sbml(circuit_path)
    print('Found inputs:', list(inputs.keys()))
    print('Found outputs:', list(outputs.keys()))
    
    # Read input sequences
    with open(input_path, 'r') as f:
        input_sequences = json.load(f)
    
    print(f'Running {len(input_sequences)} cycles with {cycle_ticks} ticks each')
    
    # Create gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = bioarm_pb2_grpc.BioArmStub(channel)
        
        # Initialize system with SBML model
        print("\n=== Initializing System ===")
        response = stub.InitializeSystem(bioarm_pb2.InitializeRequest(sbml_string=sbml_model))
        if not response.success:
            print(f"Failed to initialize system: {response.error_message}")
            return
        print("System initialized successfully")
        
        # Process each input cycle
        for cycle_num, input_values in enumerate(input_sequences):
            print(f"\n=== Cycle {cycle_num} ===")
            print(f"Inputs: {input_values}")
            
            # Convert input values to species names and set them
            species_to_add = []
            scavengers = []
            for name, value in input_values.items():
                bits = inputs[name]
                v = int(value)
                for i, bit in enumerate(reversed(bits)):
                    bit_value = (v >> i) & 1
                    if bit_value:
                        species_to_add.append(f"p_{bit}")
                    else:
                        scavengers.append(f"p_{bit}")
            
            response = stub.PipetteIn(bioarm_pb2.PipetteRequest(species=species_to_add, scavengers=scavengers))
            
            # Run simulation for one cycle
            print(f"Simulating for {cycle_ticks} ticks...")
            response = stub.Delay(bioarm_pb2.DelayRequest(seconds=cycle_ticks/100.0))  # Convert ticks to seconds
            
            # Read output concentrations and convert to digital values
            print("\nOutputs:")
            for output_name, bits in outputs.items():
                species_to_read = [f"p_{bit}" for bit in bits]
                response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=species_to_read))

                if len(bits) > 1:
                    # Multi-bit output
                    digital_values = []
                    for bit in bits:
                        conc = response.concentrations[f"p_{bit}"]
                        digital_values.append(1 if conc > 5 else 0)
                    value = sum(v << i for i, v in enumerate(digital_values))
                    print(f"{output_name}: {value}")
                else:
                    # Single-bit output
                    conc = response.concentrations[f"p_{bits[0]}"]
                    digital_value = 1 if conc > 5 else 0
                    print(f"{output_name}: {digital_value}")

def main():
    parser = argparse.ArgumentParser(description='Run Verilog circuit simulation via RPC')
    parser.add_argument('circuit', help='Path to Verilog circuit JSON file')
    parser.add_argument('inputs', help='Path to JSON input sequences')
    parser.add_argument('--cycle', type=int, default=100, 
                      help='Number of simulation ticks per cycle (default: 100)')
    
    args = parser.parse_args()
    
    try:
        run_simulation(args.circuit, args.inputs, args.cycle)
    except grpc.RpcError as e:
        print(f"RPC failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main() 