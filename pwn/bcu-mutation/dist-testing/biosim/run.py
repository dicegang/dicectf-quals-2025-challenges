
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


class Experiment:
    def __init__(self, platform):
        self.platform_cfg = json.load(open(os.path.join(os.path.dirname(__file__), f'{platform}.json'), 'r'))
        self.rr = roadrunner.RoadRunner()
        self.rr.load(os.path.join(os.path.dirname(__file__), f'{platform}.xml'))
        self.rr.setIntegrator('cvode')
        self.rr.getIntegrator().setValue("stiff", False)
        self.t = 0

    def pipette(self, species, scavengers):
        self.rr.setValue('[p_0]', 0)
        for species in species:
            self.rr.setValue(f'[{species}]', 10)
        for scavenger in scavengers:
            self.rr.setValue(f'[{scavenger}]', 0)
        time.sleep(1)

    def delay(self, seconds):
        self.rr.simulate(self.t, self.t + seconds, int(seconds * FIDELITY))
        self.t += seconds

    def measure(self, species):
        return self.rr.getValue(f'[{species}]')


def run_experiment(experiment, input):
    info = json.load(open(experiment, 'r'))
    init = bytes.fromhex(info['initial_conditions']) + input

    print(json.dumps({'status': 'loading'}), flush=True)
    exp = Experiment(platform=info['platform'])
    
    print(json.dumps({'status': 'pipetting'}), flush=True)
    species, scavengers = [], []
    for i in range(len(init)):
        for j in range(8):
            k = exp.platform_cfg['initializer'][i * 8 + j]
            if init[i] & (1 << j):
                species.append(f'p_{k}')
            else:
                scavengers.append(f'p_{k}')

    exp.pipette(species, scavengers)

    print(json.dumps({'status': 'running', 'progress': 0}))
    while True:
        exp.delay(1)
        if any(exp.measure(f'p_{exp.platform_cfg["signals"][i]}') > 5 for i in range(len(exp.platform_cfg['signals'][:8]))):
            break

        print(json.dumps({
            'status': 'running',
            'progress': exp.t / info['expected_duration'],
        }), flush=True)

    out = [str(int(exp.measure(f'p_{exp.platform_cfg["signals"][i]}') > 5)) for i in range(len(exp.platform_cfg['signals']))]
    out = [int(''.join(out[i:i+8][::-1]), 2) for i in range(0, len(out), 8)]
    print(json.dumps({
        'status': 'completed',
        'output': bytes(out).decode('ascii'),
    }), flush=True)


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument('--experiment', type=str, required=True)
    args.add_argument('--input_b64', type=str, required=True)
    args = args.parse_args()

    input = base64.b64decode(args.input_b64)
    run_experiment(args.experiment, input)
