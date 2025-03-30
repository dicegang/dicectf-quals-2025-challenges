import argparse
import json
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import roadrunner
import hashlib
import os

from roadrunner import Config
Config.setValue(Config.LLVM_BACKEND, Config.LLJIT)
Config.setValue(Config.LLJIT_OPTIMIZATION_LEVEL, Config.NONE)
Config.setValue(Config.LOADSBMLOPTIONS_MUTABLE_INITIAL_CONDITIONS, False)

from circuit import Circuit, circuit_to_model
from model import XMLWriter


def get_cache_path(model):
    """Generate cache path based on MD5 hash of the model"""
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    # Generate MD5 hash of the model
    md5_hash = hashlib.md5(model.encode()).hexdigest()
    return os.path.join(cache_dir, f"{md5_hash}.model")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Simulate a circuit with sequential inputs')
    parser.add_argument('circuit', help='JSON circuit definition file')
    parser.add_argument('inputs', help='JSON file containing input sequences')
    parser.add_argument('--cycle', type=int, default=2000, help='Number of simulation ticks per cycle (default: 300)')
    args = parser.parse_args()

    print("starting up")

    # Parse circuit from JSON
    # gates, inputs, outputs, module, input_bits = parse_json_circuit(args.circuit)

    circuit = Circuit.load_from_json(args.circuit)
    inputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'input'}
    outputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'output'}

    input_bits = []
    for p in inputs:
        input_bits += [str(x) for x in circuit.ports[p].bits]

    # Load input sequences
    with open(args.inputs) as f:
        input_sequences = json.load(f)
    
    print('Found inputs:', list(inputs.keys()))
    print('Found outputs:', list(outputs.keys()))
    print(f'Running {len(input_sequences)} cycles with {args.cycle} ticks each')
    
    # Create SBML model
    model = circuit_to_model(circuit)
    xml = XMLWriter(model)
    model = xml.write()
    cache_path = get_cache_path(model)

    print(f"Using cache: {os.path.basename(cache_path)}")
    
    # Try to load from cache first
    if os.path.exists(cache_path):
        rr = roadrunner.RoadRunner()
        print(f"Loading from cache")
        rr.loadState(cache_path)
    else:
        print(f"Initializing and saving to cache")
        rr = roadrunner.RoadRunner()

        rr.setIntegrator('cvode')

        #roadrunner.Logger.setLevel(roadrunner.Logger.LOG_INFORMATION)

        rr.load(model)
        print('after load')

        # all_species = rr.getIds()
        # print("length:", len(all_species))

        # # Initialize all species to 0
        # for species in all_species:
        #     if species.startswith('[') and species.endswith(']'):
        #         print(species)
        #         rr[species] = 0
        rr.setValue('[p_0]', 0)  # 0 is always zero

        print('after set value')

        rr.saveState(cache_path)

        print('after save state')

    rr.getIntegrator().setValue('stiff', False)
    print("Loaded model")
    rr.setIntegrator('cvode')
    rr.getIntegrator().setValue("stiff", False)
    rr.getIntegrator().setValue("absolute_tolerance", 1e-2)
    
    # Simulate each input cycle
    all_results = []
    total_time = 0
    
    for cycle_num, input_values in enumerate(input_sequences):
        print(f"Cycle {cycle_num} inputs: {input_values}")
        # Set input values for this cycle
        for name, value in input_values.items():
            bits = inputs[name]
            v = int(value)
            for i, bit in enumerate(reversed(bits)):
                bit_value = int((v >> i) & 1)
                rr.setValue(f'[p_{bit}]', 10 if bit_value else 0)
        
        # Simulate one cycle
        result = rr.simulate(total_time, total_time + args.cycle, 2)
        all_results.append(result)
        total_time += args.cycle
        
        # Print outputs for this cycle
        print(f"\nCycle {cycle_num} outputs:")
        for output_name, bits in outputs.items():
            if len(bits) > 1:
                digital_values = []
                for bit in bits:
                    final_conc = result[f'[p_{bit}]'][-1]
                    digital_values.append(1 if final_conc > 5 else 0)
                value = sum(v << i for i, v in enumerate(digital_values))
                print(f"{output_name}: {value}")
            else:
                final_conc = result[f'[p_{bits[0]}]'][-1]
                digital_value = 1 if final_conc > 5 else 0
                print(f"{output_name}: {digital_value}")
    
    # Create filtered list of species to plot (only inputs and outputs)
    plot_species = []
    for input_name, bits in inputs.items():
        plot_species.extend(f'[p_{bit}]' for bit in bits)
    for output_name, bits in outputs.items():
        plot_species.extend(f'[p_{bit}]' for bit in bits)

    # Collect time and values only for input/output species
    time = []
    # values = {species: [] for species in all_results[0].colnames if species.startswith('[')}
    values = {species: [] for species in plot_species}
    
    # for result in all_results:
    #     time.extend(result['time'])
    #     for species in result.colnames:
    #         if species.startswith('[') and species.endswith(']'):
    #             values[species].extend(result[species])
    
    for result in all_results:
        time.extend(result['time'])
        for species in result.colnames:
            if species in values:
                values[species].extend(result[species])

    # Plot with more descriptive labels
    fig = go.Figure()
    
    for species, vals in values.items():
        # Remove brackets and 'p_' prefix for cleaner labels
        label = species.replace('[p_', 'bit ').replace(']', '')
        fig.add_trace(go.Scatter(
            x=time,
            y=vals,
            name=label,
            mode='lines'
        ))
    
    fig.update_layout(
        title=f"Circuit Simulation - {len(input_sequences)} cycles",
        xaxis_title='Time',
        yaxis_title='Concentration',
        yaxis=dict(range=[0, 12]),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.05
        ),
        grid=dict(rows=1, columns=1, pattern="independent"),
    )
    
    fig.show()

if __name__ == "__main__":
    main()


