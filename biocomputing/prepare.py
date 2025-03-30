import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'harness'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'assembler'))

from circuit import Circuit, circuit_to_model
from model import XMLWriter


def load_hex_file(hex_path):
    """Load and parse a hex file into a list of binary instructions"""
    with open(hex_path, 'r') as f:
        # Read all lines and join them, then split on whitespace to get all hex bytes
        hex_bytes = f.read().replace('\n', '').replace(' ', '')

    return hex_bytes


def main():

    MODELS = [
        ('bios', 'cpu'),
        ('bios_plus', 'cpu_extended'),
    ]

    for model_name, model_type in MODELS:
        cpu_path = os.path.join(os.path.dirname(__file__), 'verilog', 'outputs', f'{model_type}_dff_nor_final.json')
        circuit = Circuit.load_from_json(cpu_path)
        inputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'input'}
        outputs = {p: circuit.ports[p].bits for p in circuit.ports if circuit.ports[p].direction == 'output'}

        # For debug mode
        cpu_meta = os.path.join(os.path.dirname(__file__), 'verilog', 'outputs', f'{model_type}_dff_nor.json')
        cpu_meta = json.load(open(cpu_meta, 'r'))
        memory = {
            f'mem[{idx}]': cpu_meta['modules']['cpu']['netnames'][f'memory[{idx}]']['bits'][::-1]
            for idx in range(32)
        }
        clock_bit = inputs.get('clk', [])[0]  # Get the clock bit
        reset_bit = inputs.get('rst', [])[0]  # Get the reset bit
        parts = {
            'memory': memory,
            'clock_bit': clock_bit,
            'reset_bit': reset_bit,
        }

        if model_name == 'bios_plus':
            comp = {
                f'comp[{idx}]': cpu_meta['modules']['cpu']['netnames'][f'comp[{idx}]']['bits'][::-1]
                for idx in range(16)
            }
            parts['comp'] = comp

        with open(f'./dist/biosim/{model_name}_debug.json', 'w') as f:
            json.dump(parts, f)

        model = circuit_to_model(circuit, auto_clock=clock_bit, auto_reset=reset_bit)
        xml_writer = XMLWriter(model)
        sbml_model = xml_writer.write()

        with open(f'./dist/biosim/{model_name}.xml', 'w') as f:
            f.write(sbml_model)

        rom_bits = inputs.get('rom', [])
        mem_out = outputs.get('memory_out', [])

        info = {
            'initializer': rom_bits,
            'signals': mem_out,
        }
        with open(f'./dist/biosim/{model_name}.json', 'w') as f:
            json.dump(info, f)


    # chal 1
    with open('./dist/biosim/experiments/chall1.json', 'w') as f:
        json.dump({
            'initial_conditions': load_hex_file('./assembler/bin/chall1.hex'),
            'platform': 'bios',
            'expected_duration': 1117,
        }, f)

    # debug good
    with open('./dist/biosim/experiments/debug_good.json', 'w') as f:
        json.dump({
            'initial_conditions': load_hex_file('./assembler/bin/debug_good.hex'),
            'platform': 'bios',
            'expected_duration': 69,
        }, f)

    # rev circuit
    with open('./dist/biosim/experiments/rev_circuit.json', 'w') as f:
        json.dump({
            'initial_conditions': load_hex_file('./assembler/bin/rev_circuit.hex'),
            'platform': 'bios_plus',
            'expected_duration': 105,
        }, f)


if __name__ == "__main__":
    main()

