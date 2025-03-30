from collections import namedtuple
import roadrunner
import numpy as np
import matplotlib.pyplot as plt

NOR1 = namedtuple('NOR1', ['a', 'out'])
NOR2 = namedtuple('NOR2', ['a', 'b', 'out'])
NOR3 = namedtuple('NOR3', ['a', 'b', 'c', 'out'])
NOR4 = namedtuple('NOR4', ['a', 'b', 'c', 'd', 'out'])
NOR5 = namedtuple('NOR5', ['a', 'b', 'c', 'd', 'e', 'out'])
NOR6 = namedtuple('NOR6', ['a', 'b', 'c', 'd', 'e', 'f', 'out'])
DFF_P = namedtuple('DFF', ['d', 'clk', 'p'])

GATES = {
    NOR1: open('gates/nor1.sbml').read(),
    NOR2: open('gates/nor2.sbml').read(),
    NOR3: open('gates/nor3.sbml').read(),
    NOR4: open('gates/nor4.sbml').read(),
    NOR5: open('gates/nor5.sbml').read(),
    NOR6: open('gates/nor6.sbml').read(),
    DFF_P: open('gates/dff_p.sbml').read(),
}

def synthesize_sbml(circuit, input_nodes):
    # Constants for reaction rates (moved to parameters section)
    k_transcription = 1.0  # Base transcription rate
    k_mrna_decay = 0.1    # mRNA decay rate
    k_protein_decay = 1  # Protein decay rate
    k_translation = 1.0    # Translation rate
    k_repression = 3.0    # Repression strength
    k_activation = 2.0    # Activation strength

    # Start building SBML model
    sbml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
    <model id="circuit">
        <listOfParameters>
            <parameter id="k_transcription" value="{k_transcription}" constant="true"/>
            <parameter id="k_mrna_decay" value="{k_mrna_decay}" constant="true"/>
            <parameter id="k_protein_decay" value="{k_protein_decay}" constant="true"/>
            <parameter id="k_translation" value="{k_translation}" constant="true"/>
            <parameter id="k_repression" value="{k_repression}" constant="true"/>
            <parameter id="k_activation" value="{k_activation}" constant="true"/>
        </listOfParameters>
        <listOfCompartments>
            <compartment id="cell" size="1"/>
        </listOfCompartments>
        <listOfSpecies>
"""

    # Add species for all nodes (except inputs)
    all_nodes = set()
    for gate in circuit:
        match gate:
            case NOR1(_a, out):
                all_nodes.add(out)
            case NOR2(_a, _b, out):
                all_nodes.add(out)
            case NOR3(_a, _b, _c, out):
                all_nodes.add(out)
            case NOR4(_a, _b, _c, _d, out):
                all_nodes.add(out)
            case NOR5(_a, _b, _c, _d, _e, out):
                all_nodes.add(out)
            case NOR6(_a, _b, _c, _d, _e, _f, out):
                all_nodes.add(out)
            case DFF_P(_d, _clk, p):
                all_nodes.add(p)
            case _:
                raise ValueError(f"Unknown gate: {gate}")
            
    all_nodes = sorted(all_nodes)

    # Add input nodes (protein only)
    for node in input_nodes:
        sbml += f'            <species id="protein_{node}" compartment="cell" initialAmount="0"/>\n'

    # Add internal nodes (both mRNA and protein)
    for node in all_nodes:
        sbml += f'            <species id="mrna_{node}" compartment="cell" initialAmount="0"/>\n'
        sbml += f'            <species id="protein_{node}" compartment="cell" initialAmount="0"/>\n'

    sbml += """        </listOfSpecies>
        <listOfReactions>
"""

    # Add reactions for each internal node
    for node in all_nodes:
        # mRNA decay
        sbml += f"""            <reaction id="mrna_{node}_decay">
                <listOfReactants>
                    <speciesReference species="mrna_{node}"/>
                </listOfReactants>
                <kineticLaw>
                    <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <apply>
                            <times/>
                            <ci>k_mrna_decay</ci>
                            <ci>mrna_{node}</ci>
                        </apply>
                    </math>
                </kineticLaw>
            </reaction>
"""

        # Protein decay
        sbml += f"""            <reaction id="protein_{node}_decay">
                <listOfReactants>
                    <speciesReference species="protein_{node}"/>
                </listOfReactants>
                <kineticLaw>
                    <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <apply>
                            <times/>
                            <ci>k_protein_decay</ci>
                            <ci>protein_{node}</ci>
                        </apply>
                    </math>
                </kineticLaw>
            </reaction>
"""

        # Protein synthesis (translation)
        sbml += f"""            <reaction id="protein_{node}_synthesis">
                <listOfProducts>
                    <speciesReference species="protein_{node}"/>
                </listOfProducts>
                <kineticLaw>
                    <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <apply>
                            <times/>
                            <ci>k_translation</ci>
                            <ci>mrna_{node}</ci>
                        </apply>
                    </math>
                </kineticLaw>
            </reaction>
"""

    # Add transcription reactions with repression
    for gate in circuit:
        schema = GATES[type(gate)]
        sbml += schema.format(gate=gate)

    # Close the SBML document
    sbml += """        </listOfReactions>
    </model>
</sbml>
"""

    # Create and return the model
    return sbml
