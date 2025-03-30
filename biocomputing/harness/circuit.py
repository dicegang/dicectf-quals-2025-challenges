from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from model import Model, Species, Parameter, Reaction, ADD, DIV, MUL, POW, SUB, MAX, MIN, VAR, CONST, SpeciesReference

@dataclass
class PortInfo:
    direction: str
    bits: List[int]

@dataclass
class Cell:
    type: str
    input: List[int]
    output: List[int]

@dataclass
class Circuit:
    ports: Dict[str, PortInfo]
    cells: Dict[str, Cell]

    @staticmethod
    def load_from_json(filepath: str) -> 'Circuit':
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Get the first module from the JSON
        module_name, module_data = next(iter(data.items()))
        
        # Create the Circuit object
        return Circuit(
            ports={name: PortInfo(**port_data) for name, port_data in module_data['ports'].items()},
            cells={name: Cell(
                type=cell_data['type'],
                input=cell_data.get('input', []),
                output=cell_data.get('output', [])
            ) for name, cell_data in module_data['cells'].items()}
        )


def circuit_to_model(circuit: Circuit, auto_clock: Optional[int] = None, auto_reset: Optional[int] = None) -> Model:
    m = Model(parameters=[], species=[], reactions=[])

    # Add parameters
    m.parameters.extend([
        Parameter(name='k_transcription', value=10.0),
        Parameter(name='k_repression', value=10.0),
        Parameter(name='k_decay', value=1.0),
        Parameter(name='k_clamp', value=5),
    ])

    if auto_clock:
        add_repressilator_clock(m, auto_clock)

    if auto_reset:
        add_auto_decay_reset(m, auto_reset)

    # Add additional parameters for DFF if not already present
    m.parameters.append(Parameter(name='k_delay', value=0.02))

    pins = set()  
    pins.add(0)  # 0 is always zero
    for port in circuit.ports.values():
        for bit in port.bits:
            pins.add(bit)

    for cell in circuit.cells.values():
        for pin in cell.input:
            pins.add(pin)
        for pin in cell.output:
            pins.add(pin)

    if auto_clock:
        pins.remove(auto_clock)

    if auto_reset:
        pins.remove(auto_reset)

    pins = [x for x in pins if type(x) == int]

    for pin in sorted(pins):
        m.species.append(Species(name=f'p_{pin}', initial_amount=0.0))

    # Add reactions for each cell
    delayed_clocks = set()
    
    for cell in circuit.cells.values():
        if cell.type.startswith('NOR'):
            n = int(cell.type[3:])
            handle_nor(m, n, cell)
            continue

        if cell.type == 'DFF_P':
            handle_dff_p(m, cell)

            clk = cell.input[0]
            delayed_clocks.add(clk)

            continue

        raise Exception(f"Unknown cell type: {cell.type}")

    for clk in delayed_clocks:
        # Add a species that is a delayed clock signal
        m.species.append(Species(name=f'p_delayed_{clk}', initial_amount=0.0))

        # Add a reaction that delays the clock signal
        m.reactions.append(Reaction(
            name=f'delay_{clk}',
            reactants=[],
            products=[SpeciesReference(name=f'p_delayed_{clk}')],
            rate=MUL([VAR('k_delay'), VAR(f'p_{clk}')])
        ))

        # Decay the delayed clock signal
        m.reactions.append(Reaction(
            name=f'decay_{clk}',
            reactants=[SpeciesReference(name=f'p_delayed_{clk}')],
            products=[],
            rate=MUL([VAR('k_delay'), VAR(f'p_delayed_{clk}')])
        ))

    return m


def handle_nor(m: Model, n: int, cell: Cell):
    y = cell.output[0]  # Get the output pin
    terms = cell.input  # Get the input pins

    # s is +1 for growth, -1 for decay
    s = SUB(
        MIN([
            ADD([
                MAX([SUB(VAR(f'p_{term}'), CONST(2)), CONST(0)]) for term in terms
            ]),
            CONST(2)
        ]),
        CONST(1)
    )

    growth = MUL([
        CONST(10),
        SUB(CONST(10), VAR(f'p_{y}'))
    ])

    decay = MUL([
        CONST(-10),
        MAX([SUB(VAR(f'p_{y}'), CONST(0.1)), CONST(0)])
    ])

    mixed = ADD([
        MUL([decay, MAX([s, CONST(0)])]),
        MUL([growth, MAX([SUB(CONST(1), s), CONST(0)])])
    ])

    # Add the reaction that produces y
    m.reactions.append(Reaction(
        name=f'synthesis_{y}',
        reactants=[],
        products=[SpeciesReference(name=f'p_{y}')],
        rate=mixed
    ))

def handle_dff_p(m: Model, cell: Cell):
    p = cell.output[0]
    clk = cell.input[0]
    d = cell.input[1]

    # Add an intermediate value species
    po = f'p_{p}'
    pi = f'p_i_{p}_{d}_{clk}'
    m.species.append(Species(name=pi, initial_amount=0.0))

    # When clock is high, p_i should follow d
    sel_i = SUB(MAX([MIN([VAR(f'p_{d}'), CONST(2)]), CONST(0)]), CONST(1))

    growth_i = MUL([
        CONST(10),
        SUB(CONST(10), VAR(pi))
    ])

    decay_i = MUL([
        CONST(-10),
        MAX([SUB(VAR(pi), CONST(0.1)), CONST(0)])
    ])

    gate_i = MIN([MAX([SUB(VAR(f'p_{clk}'), CONST(5)), CONST(0)]), CONST(1)])

    mixed_i = MUL([
        gate_i,
        ADD([
            MUL([growth_i, MAX([sel_i, CONST(0)])]),
            MUL([decay_i, MAX([SUB(CONST(1), sel_i), CONST(0)])])
        ])
    ])

    m.reactions.append(Reaction(
        name=f'latch_{p}_{d}_{clk}',
        reactants=[],
        products=[SpeciesReference(name=pi)],
        rate=mixed_i
    ))

    # When clock is low, p should follow p_i
    sel_o = SUB(MAX([MIN([VAR(pi), CONST(2)]), CONST(0)]), CONST(1))

    growth_o = MUL([
        CONST(10),
        SUB(CONST(10), VAR(po))
    ])

    decay_o = MUL([
        CONST(-10),
        MAX([SUB(VAR(po), CONST(0.1)), CONST(0)])
    ])

    gate_o = MIN([MAX([SUB(CONST(5), VAR(f'p_{clk}')), CONST(0)]), CONST(1)])

    mixed_o = MUL([
        gate_o,
        ADD([
            MUL([growth_o, MAX([sel_o, CONST(0)])]),
            MUL([decay_o, MAX([SUB(CONST(1), sel_o), CONST(0)])])
        ])
    ])

    m.reactions.append(Reaction(
        name=f'transfer_{p}_{d}_{clk}',
        reactants=[],
        products=[SpeciesReference(name=po)],
        rate=mixed_o
    ))



# def handle_dff_p(m: Model, cell: Cell):
#     p = cell.output[0]
#     clk = cell.input[0]
#     d = cell.input[1]

#     clk_delayed = f'p_delayed_{clk}'

#     # Add an intermediate value species
#     m.species.append(Species(name=f'p_i_{p}_{d}_{clk}', initial_amount=0.0))

#     # p_conc from 0 to 1
#     p_conc = DIV(MAX([MIN([VAR(f'p_i_{p}_{d}_{clk}'), CONST(10)]), CONST(0)]), CONST(10))

#     E = CONST(2.71)
#     K = CONST(10)

#     mod_pos = SUB(DIV(CONST(2), ADD([CONST(1), POW(E, MUL([K, SUB(p_conc, CONST(1))]))])), CONST(1))
#     mod_neg = SUB(DIV(CONST(2), ADD([CONST(1), POW(E, MUL([CONST(-1), K, p_conc]))])), CONST(1))

#     # clamp to [0,1]
#     mod_pos = MAX([MIN([mod_pos, CONST(1)]), CONST(0)])
#     mod_neg = MAX([MIN([mod_neg, CONST(1)]), CONST(0)])

#     diff = MAX([SUB(VAR(f'p_{clk}'), VAR(clk_delayed)), CONST(0)])
#     diff_pos = MUL([DIV(clamp(d), CONST(10)), diff])

#     m.reactions.append(Reaction(
#         name=f'latch_{p}_{d}_{clk}',
#         reactants=[],
#         products=[SpeciesReference(name=f'p_i_{p}_{d}_{clk}')],
#         rate=MUL([mod_pos, diff_pos])
#     ))

#     diff_neg = MUL([DIV(SUB(CONST(10), clamp(d)), CONST(10)), diff])

#     m.reactions.append(Reaction(
#         name=f'unlatch_{p}_{d}_{clk}',
#         reactants=[SpeciesReference(name=f'p_i_{p}_{d}_{clk}')],
#         products=[],
#         rate=MUL([mod_neg, diff_neg])
#     ))

#     inv_diff = DIV(SUB(CONST(10), VAR(f'p_{clk}')), CONST(10))

#     # When the clock is low, output species should be the same as the intermediate value
#     m.reactions.append(Reaction(
#         name=f'output_inc_{p}_{d}_{clk}',
#         reactants=[],
#         products=[SpeciesReference(name=f'p_{p}')],
#         rate=MUL([inv_diff, SUB(VAR(f'p_i_{p}_{d}_{clk}'), VAR(f'p_{p}'))])
#     ))

#     m.reactions.append(Reaction(
#         name=f'output_dec_{p}_{d}_{clk}',
#         reactants=[SpeciesReference(name=f'p_{p}')],
#         products=[],
#         rate=MUL([inv_diff, SUB(VAR(f'p_{p}'), VAR(f'p_i_{p}_{d}_{clk}'))])
#     ))

def add_repressilator_clock(m: Model, auto_clock: int):
    clk = f'p_{auto_clock}'

    # Parameters
    m.parameters.extend([
        Parameter(name='beta', value=16),
        Parameter(name='n', value=3),
        Parameter(name='gamma', value=1),
        Parameter(name='k_high', value=100.0),  # Fast switching rate to high
        Parameter(name='k_low', value=100.0),   # Fast switching rate to low
        Parameter(name='threshold', value=7.0),  # Threshold for switching
    ])

    # Three genes in the cycle: A -> B -> C -> A (where -> means "represses")
    m.species = [
        Species(name="repA", initial_amount=9.5),
        Species(name="repB", initial_amount=1.5),
        Species(name="repC", initial_amount=1.5),
        Species(name=clk, initial_amount=0.0),
    ]

    # Create reactions for each protein
    # Each protein's production is repressed by the previous protein in the cycle
    # A is repressed by C, B by A, C by B

    # Clock reactions - switches clk high when protein_A > threshold, and low when protein_A < threshold
    m.reactions.extend([
        Reaction(
            name="clk_high",
            reactants=[],
            products=[SpeciesReference(name=clk)],
            rate=MUL([
                VAR('k_high'),
                SUB(CONST(10), VAR(clk)),  # (1 - clk) ensures it approaches 1
                POW(
                    DIV(VAR('repA'), VAR('threshold')),
                    CONST(4)
                )
            ])
        ),
        Reaction(
            name="clk_low",
            reactants=[SpeciesReference(name=clk)],
            products=[],
            rate=MUL([
                VAR('k_low'),
                VAR(clk),  # clk ensures it approaches 0
                MAX([SUB(VAR('repB'), CONST(4)), CONST(0)]),
            ])
        )
    ])

    # Production and degradation of protein A
    m.reactions.append(
        Reaction(
            name="prod_A",
            reactants=[],
            products=[SpeciesReference(name="repA")],
            rate=MUL([
                SUB(
                    DIV(
                        VAR('beta'),
                        ADD([
                            CONST(1),
                            POW(
                                VAR('repC'),
                                VAR('n')
                            )
                        ])
                    ),
                    VAR('repA')
                ),
                VAR('gamma')
            ])
        )
    )

    m.reactions.append(
        Reaction(
            name='prod_B',
            reactants=[],
            products=[SpeciesReference(name='repB')],
            rate=MUL([
                SUB(
                    DIV(
                        VAR('beta'),
                        ADD([
                            CONST(1),
                            POW(
                                VAR('repA'),
                                VAR('n')
                            )
                        ])
                    ),
                    VAR('repB')
                ),
                VAR('gamma')
            ])
        )
    )

    m.reactions.append(
        Reaction(
            name='prod_C',
            reactants=[],
            products=[SpeciesReference(name='repC')],
            rate=MUL([
                SUB(
                    DIV(
                        VAR('beta'),
                        ADD([
                            CONST(1),
                            POW(VAR('repB'), VAR('n'))
                        ])
                    ),
                    VAR('repC')
                ),
                VAR('gamma')
            ])
        )
    )

def add_auto_decay_reset(m: Model, auto_reset: int):
    # Sets the auto_reset pin to high which will automatically decay to low rapidly after a few clock cycles
    m.species.extend([
        Species(name=f'p_{auto_reset}', initial_amount=10.0),
        Species(name=f'reset_decay', initial_amount=10.0),
    ])

    m.reactions.extend([
        Reaction(
            name='reset_decay',
            reactants=[SpeciesReference(name='reset_decay')],
            products=[],
            rate=MUL([
                CONST(0.2),
                MAX([SUB(VAR('reset_decay'), CONST(0.1)), CONST(0)])
            ])
        ),
        Reaction(
            name='reset_trigger',
            reactants=[SpeciesReference(name=f'p_{auto_reset}')],
            products=[],
            rate=MUL([
                CONST(20),
                MAX([SUB(CONST(1), VAR('reset_decay')), CONST(0)]),
                MAX([SUB(VAR(f'p_{auto_reset}'), CONST(0.1)), CONST(0)])
            ])
        )
    ])

def draw_circuit(circuit: Circuit) -> str:
    """
    Generate a Graphviz visualization of the circuit.
    
    Args:
        circuit: The Circuit object to visualize
        output_file: The output file path for the dot file
    """
    dot_str = ['digraph G {']
    dot_str.append('    rankdir=LR;')  # Left to right layout
    dot_str.append('    node [shape=box];')  # Default node shape
    
    # Add input/output ports
    for port_name, port_info in circuit.ports.items():
        if port_info.direction == 'input':
            shape = 'triangle'
        else:
            shape = 'invtriangle'
        
        # Create a node for each port bit
        for bit in port_info.bits:
            dot_str.append(f'    port_{bit} [label="{port_name}[{bit}]" shape={shape}];')
    
    # Add cells
    for cell_name, cell in circuit.cells.items():
        sanitized_name = cell_name.replace('$', '_').replace('.', '_').replace(':', '_')

        # Create cell node
        dot_str.append(f'    {sanitized_name} [label="{cell.type}"];')
        
        # Add edges from inputs to cell
        for i, input_pin in enumerate(cell.input):
            dot_str.append(f'    p_{input_pin} -> {sanitized_name} [label="in{i}"];')
        
        # Add edges from cell to outputs
        for i, output_pin in enumerate(cell.output):
            dot_str.append(f'    {sanitized_name} -> p_{output_pin} [label="out{i}"];')
    
    dot_str.append('}')
    
    return '\n'.join(dot_str)
