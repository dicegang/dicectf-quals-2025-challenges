import roadrunner
import matplotlib.pyplot as plt
import numpy as np
import sys

# import model
sys.path.append('..')
from harness.model import XMLWriter, Model, Parameter, Species, Reaction, SpeciesReference, RATE_TYPE, ADD, MUL, DIV, POW, SUB, VAR, CONST, MIN, MAX

# Create a repressilator model
m = Model(parameters=[], species=[], reactions=[])

# Parameters
m.parameters = [
    Parameter(name='beta', value=16),
    Parameter(name='n', value=3),
    Parameter(name='gamma', value=1),
    Parameter(name='k_high', value=100.0),  # Fast switching rate to high
    Parameter(name='k_low', value=100.0),   # Fast switching rate to low
    Parameter(name='threshold', value=7.0),  # Threshold for switching
]

# Three genes in the cycle: A -> B -> C -> A (where -> means "represses")
m.species = [
    Species(name="protein_A", initial_amount=9.5),
    Species(name="protein_B", initial_amount=1.5),
    Species(name="protein_C", initial_amount=1.5),
    Species(name="clk", initial_amount=0.0),  # Clock signal starts low
    Species(name="reset", initial_amount=10.0),
    Species(name="reset_decay", initial_amount=10.0),
]

# Create reactions for each protein
# Each protein's production is repressed by the previous protein in the cycle
# A is repressed by C, B by A, C by B

# Clock reactions - switches clk high when protein_A > threshold, and low when protein_A < threshold
m.reactions.extend([
    Reaction(
        name="clk_high",
        reactants=[],
        products=[SpeciesReference(name="clk")],
        rate=MUL([
            VAR('k_high'),
            SUB(CONST(10), VAR('clk')),  # (1 - clk) ensures it approaches 1
            POW(
                DIV(VAR('protein_A'), VAR('threshold')),
                CONST(4)
            )
        ])
    ),
    Reaction(
        name="clk_low",
        reactants=[SpeciesReference(name="clk")],
        products=[],
        rate=MUL([
            VAR('k_low'),
            VAR('clk'),  # clk ensures it approaches 0
            MAX([SUB(VAR('protein_B'), CONST(4)), CONST(0)]),
        ])
    )
])

# Production and degradation of protein A
m.reactions.append(
    Reaction(
        name="prod_A",
        reactants=[],
        products=[SpeciesReference(name="protein_A")],
        rate=MUL([
            SUB(
                DIV(
                    VAR('beta'),
                    ADD([
                        CONST(1),
                        POW(
                            VAR('protein_C'),
                            VAR('n')
                        )
                    ])
                ),
                VAR('protein_A')
            ),
            VAR('gamma')
        ])
    )
)

m.reactions.append(
    Reaction(
        name='prod_B',
        reactants=[],
        products=[SpeciesReference(name='protein_B')],
        rate=MUL([
            SUB(
                DIV(
                    VAR('beta'),
                    ADD([
                    CONST(1),
                    POW(
                        VAR('protein_A'),
                        VAR('n')
                        )
                    ])
                ),
                VAR('protein_B')
            ),
            VAR('gamma')
        ])
    )
)

m.reactions.append(
    Reaction(
        name='prod_C',
        reactants=[],
        products=[SpeciesReference(name='protein_C')],
        rate=MUL([
            SUB(
                DIV(
                    VAR('beta'),
                    ADD([
                        CONST(1),
                        POW(VAR('protein_B'), VAR('n'))
                    ])
                ),
                VAR('protein_C')
            ),
            VAR('gamma')
        ])
    )
)

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
        reactants=[SpeciesReference(name='reset')],
        products=[],
        rate=MUL([
            CONST(20),
            MAX([SUB(CONST(1), VAR('reset_decay')), CONST(0)]),
            MAX([SUB(VAR('reset'), CONST(0.1)), CONST(0)])
        ])
    )
])

# Generate SBML
xml = XMLWriter(m)
model = xml.write()

# print(model)

# Create a roadrunner instance
r = roadrunner.RoadRunner(model)

print('after model')

# Set integrator settings for better accuracy
r.setIntegrator('cvode')
r.getIntegrator().setValue('relative_tolerance', 1e-6)
r.getIntegrator().setValue('absolute_tolerance', 1e-12)
r.getIntegrator().setValue('stiff', False)

# Simulate for 100 seconds with 1000 points
result = r.simulate(0, 20, 1000)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(result[:, 0], result[:, 1], label='Protein A')
plt.plot(result[:, 0], result[:, 2], label='Protein B')
plt.plot(result[:, 0], result[:, 3], label='Protein C')
plt.plot(result[:, 0], result[:, 4], label='Clock', linestyle='--', color='black')
plt.plot(result[:, 0], result[:, 5], label='Reset', linestyle='--', color='red')
plt.plot(result[:, 0], result[:, 6], label='Reset Decay', linestyle='--', color='blue')
plt.xlabel('Time (s)')
plt.ylabel('Concentration')
plt.title('Repressilator with Clock Signal')
plt.grid(True)
plt.legend()
plt.show() 