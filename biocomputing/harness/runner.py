import roadrunner


class Runner(object):
    def __init__(self, model):
        self.rr = roadrunner.RoadRunner(model)

    def run(self, values, inputs, tick_size=2, debug=False, outputs=None, capture=None):
        for species in self.rr.getIds():
            if species.startswith('[') and species.endswith(']'):
                self.rr[species] = 0

        # Fixed at 0
        try:
            self.rr.setValue('[p_0]', 0)
        except Exception as e:
            pass

        # Simulate each input cycle
        all_results = {}
        total_time = 0
        output_results = []

        for cycle_num, input_values in enumerate(values):
            if debug:
                print(f"Cycle {cycle_num} inputs: {input_values}")

            # Set input values for this cycle
            for name, value in input_values.items():
                bits = inputs[name]
                v = int(value)
                for i, bit in enumerate(reversed(bits)):
                    bit_value = int((v >> i) & 1)
                    self.rr.setValue(f'[p_{bit}]', 10 if bit_value else 0)

            # Simulate one cycle
            result = self.rr.simulate(total_time, total_time + tick_size, tick_size * 20)
            total_time += tick_size

            if capture:
                for bit in capture:
                    if not bit in all_results:
                        all_results[bit] = []

                    if type(bit) == int:
                        all_results[bit] += list(result[f'[p_{bit}]'])
                    else:
                        all_results[bit] += list(result[f'[{bit}]'])

            # Print outputs for this cycle
            if outputs:
                if debug:
                    print(f"\nCycle {cycle_num} outputs:")

                res = {}

                for output_name, bits in outputs.items():
                    value = 0
                    if len(bits) > 1:
                        digital_values = []
                        for bit in bits:
                            final_conc = result[f'[p_{bit}]'][-1]
                            digital_values.append(1 if final_conc > 5 else 0)
                        value = sum(v << i for i, v in enumerate(digital_values))
                    else:
                        final_conc = result[f'[p_{bits[0]}]'][-1]
                        value = 1 if final_conc > 5 else 0

                    if debug:
                        print(f"{output_name}: {value}")
                    res[output_name] = value

                output_results.append(res)

        return all_results, output_results
