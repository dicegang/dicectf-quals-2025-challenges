
import argparse
import base64
import json
import os
import time
import roadrunner
from roadrunner import Config
Config.setValue(Config.LLVM_BACKEND, Config.LLJIT)
Config.setValue(Config.LLJIT_OPTIMIZATION_LEVEL, Config.NONE)
Config.setValue(Config.LOADSBMLOPTIONS_MUTABLE_INITIAL_CONDITIONS, False)


FIDELITY = 20


GREEN = '\033[92m'
RESET = '\033[0m'


class Experiment:
    def __init__(self, platform):
        a = time.time()
        print('Loading BIOS...')
        self.platform_cfg = json.load(open(os.path.join(os.path.dirname(__file__), f'{platform}.json'), 'r'))
        self.platform_debug = json.load(open(os.path.join(os.path.dirname(__file__), f'{platform}_debug.json'), 'r'))
        self.rr = roadrunner.RoadRunner()
        self.rr.load(os.path.join(os.path.dirname(__file__), f'{platform}.xml'))
        self.rr.setIntegrator('cvode')
        self.rr.getIntegrator().setValue("stiff", False)
        self.t = 0
        print('BIOS loaded in', time.time() - a)

    def pipette(self, species, scavengers):
        self.rr.setValue('[p_0]', 0)
        for species in species:
            self.rr.setValue(f'[{species}]', 10)
        for scavenger in scavengers:
            self.rr.setValue(f'[{scavenger}]', 0)

    def delay(self, seconds):
        self.rr.simulate(self.t, self.t + seconds, int(seconds * FIDELITY))
        self.t += seconds

    def measure(self, species):
        return self.rr.getValue(f'[{species}]')


def run_experiment(experiment, input):
    info = json.load(open(experiment, 'r'))
    init = bytes.fromhex(info['initial_conditions']) + input

    exp = Experiment(platform=info['platform'])
    
    species, scavengers = [], []
    for i in range(len(init)):
        for j in range(7,-1,-1):
            k = exp.platform_cfg['initializer'][i * 8 + j]
            if init[i] & (1 << j):
                species.append(f'p_{k}')
            else:
                scavengers.append(f'p_{k}')

    exp.pipette(species, scavengers)

    last_clk = False
    while True:
        exp.delay(1)

        if any(exp.measure(f'p_{exp.platform_cfg["signals"][i]}') > 5 for i in range(len(exp.platform_cfg['signals'][:8]))):
            print('completed at', exp.t)
            break

        clk = exp.measure(f'p_{exp.platform_debug["clock_bit"]}') > 5
        rst = exp.measure(f'p_{exp.platform_debug["reset_bit"]}') > 5
        
        clk_hi = clk and not last_clk
        last_clk = clk

        l = f'[{exp.t:04d}]'
        if clk:
            l += '[C]'
        if rst:
            l += '[R]'
        
        if not rst and clk_hi:
            # Read memory
            mem = {}
            for k in exp.platform_debug['memory']:
                bits = exp.platform_debug['memory'][k]
                bitstring = ''.join([str(int(exp.measure(f'p_{b}') > 5)) for b in bits])
                mem[k] = int(bitstring, 2)

            # Read output
            out = [str(int(exp.measure(f'p_{exp.platform_cfg["signals"][i]}') > 5)) for i in range(len(exp.platform_cfg['signals']))]
            out = [int(''.join(out[i:i+8][::-1]), 2) for i in range(0, len(out), 8)]
            out_str = ' '.join([f'{o:02x}' for o in out])

            # format registers
            reg_str = ''
            for i in range(8):
                v = mem[f'mem[{i}]']
                reg_str += f'[r{i}: {GREEN}{v:02x}{RESET}] '

            rest = [mem[f'mem[{i}]'] for i in range(8, 32)]
            rest_str = ' '.join([f'{i:02x}' for i in rest])

            l += f'\nreg: {reg_str}\nmem: {rest_str}\nout: {out_str}'
            print(l)

            if 'comp' in exp.platform_debug:
                comp = {}
                for k in exp.platform_debug['comp']:
                    bits = exp.platform_debug['comp'][k]
                    bitstring = ''.join([str(int(exp.measure(f'p_{b}') > 5)) for b in bits])
                    comp[k] = int(bitstring, 2)
                print('comp:', ' '.join([f'{comp[k]:02x}' for k in comp]))


    out = [str(int(exp.measure(f'p_{exp.platform_cfg["signals"][i]}') > 5)) for i in range(len(exp.platform_cfg['signals']))]
    out = [int(''.join(out[i:i+8][::-1]), 2) for i in range(0, len(out), 8)]
    return bytes(out)


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument('--experiment', type=str, required=True)
    args.add_argument('--input_b64', type=str, required=True)
    args = args.parse_args()

    input = base64.b64decode(args.input_b64)
    out = run_experiment(args.experiment, input)
    print('output:', out)
