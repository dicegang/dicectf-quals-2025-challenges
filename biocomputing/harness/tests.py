import roadrunner
import matplotlib.pyplot as plt
from collections import namedtuple

# from synth import synthesize_sbml, NOR1, NOR2, NOR3, NOR4, DFF_P
from circuit import Circuit, circuit_to_model, Cell
from model import XMLWriter
from runner import Runner


# Mock circuit
NOR1 = namedtuple('NOR1', ['a', 'out'])
NOR2 = namedtuple('NOR2', ['a', 'b', 'out'])
NOR3 = namedtuple('NOR3', ['a', 'b', 'c', 'out'])
NOR4 = namedtuple('NOR4', ['a', 'b', 'c', 'd', 'out'])
DFF_P = namedtuple('DFF_P', ['d', 'clk', 'p'])

def mock_circuit(elements) -> Circuit:
    cells = {}
    idx = 0
    for element in elements:
        match element:
            case NOR1(a, out):
                cells[idx] = Cell(type='NOR1', input=[a], output=[out])
                idx += 1
            case NOR2(a, b, out):
                cells[idx] = Cell(type='NOR2', input=[a, b], output=[out])
                idx += 1
            case NOR3(a, b, c, out):
                cells[idx] = Cell(type='NOR3', input=[a, b, c], output=[out])
                idx += 1
            case NOR4(a, b, c, d, out):
                cells[idx] = Cell(type='NOR4', input=[a, b, c, d], output=[out])
                idx += 1
            case DFF_P(d, clk, p):
                cells[idx] = Cell(type='DFF_P', input=[clk, d], output=[p])
                idx += 1
    return Circuit(ports={}, cells=cells)


basic_nor = {
    "name": "basic_nor",
    "circuit": [
        NOR2(a=1, b=2, out=3),
    ],
    "values": [
        {"a": 0, "b": 0},
        {"a": 0, "b": 1},
        {"a": 1, "b": 0},
        {"a": 1, "b": 1},
    ],
    "inputs": {
        'a': [1],
        'b': [2],
    },
    "outputs": {
        'out': [3],
    },
    "expected": [
        {'out': 1},
        {'out': 0},
        {'out': 0},
        {'out': 0},
    ],
}

basic_not = {
    "name": "basic_not",
    "circuit": [
        NOR1(a=1, out=2),
    ],
    "values": [
        {"a": 0},
        {"a": 1},
    ],
    "inputs": {
        'a': [1],
    },
    "outputs": {
        'out': [2],
    },
    "expected": [
        {'out': 1},
        {'out': 0},
    ],
}

chained_not = {
    "name": "chained_not",
    "circuit": [
        NOR1(a=1, out=2),
        NOR1(a=2, out=3),
        NOR1(a=3, out=4),
        NOR1(a=4, out=5),
        NOR1(a=5, out=6),
        NOR1(a=6, out=7),
        NOR1(a=7, out=8),
        NOR1(a=8, out=9),
        NOR1(a=9, out=10),
        NOR1(a=10, out=11),
        NOR1(a=11, out=12),
        NOR1(a=12, out=13),
        NOR1(a=13, out=14),
        NOR1(a=14, out=15),
    ],
    "values": [
        {"a": 0},
        {"a": 1},
    ],
    "inputs": {
        'a': [1],
    },
    "outputs": {
        'out': [15],
    },
    "expected": [
        {'out': 0},
        {'out': 1},
    ],
}

multiple_usage = {
    "name": "multiple_usage",
    "circuit": [
        NOR1(a=1, out=2),
        NOR1(a=1, out=3),
        NOR1(a=1, out=4),
        NOR1(a=2, out=5),
        NOR1(a=2, out=6),
        NOR1(a=3, out=7),
        NOR1(a=3, out=8),
        NOR1(a=3, out=9),
        NOR1(a=4, out=10),
        NOR1(a=4, out=11),
        NOR1(a=4, out=12),
        NOR1(a=4, out=13),
        NOR1(a=4, out=14),
        NOR1(a=4, out=15),
    ],
    "values": [
        {"a": 0},
        {"a": 1},
    ],
    "inputs": {
        'a': [1],
    },
    "outputs": {
        'out': [15],
    },
    "expected": [
        {'out': 0},
        {'out': 1},
    ],
}


basic_dff = {
    "name": "basic_dff",
    "circuit": [
        DFF_P(d=1, clk=2, p=3),
    ],
    "values": [
        {"d": 0, "clk": 0},
        {"d": 0, "clk": 1},
        {"d": 0, "clk": 0},
        {"d": 0, "clk": 1},
        {"d": 1, "clk": 0},
        {"d": 1, "clk": 1},
        {"d": 1, "clk": 0},
        {"d": 0, "clk": 1},
        {"d": 0, "clk": 0},
        {"d": 0, "clk": 1},
        {"d": 1, "clk": 0},
        {"d": 0, "clk": 1},
        {"d": 1, "clk": 0},
    ],
    "inputs": {
        'd': [1],
        'clk': [2],
    },
    "outputs": {
        'p': [3],
    },
    "expected": [
        {'p': 0},
        {'p': 0},
        {'p': 0},
        {'p': 0},
        {'p': 0},
        {'p': 0},
        {'p': 1},
        {'p': 1},
        {'p': 0},
        {'p': 0},
        {'p': 0},
        {'p': 0},
        {'p': 0},
    ],
}


def test_circuit(circuit, plot=False, debug=False):
    inputs = []
    for i in circuit['inputs']:
        inputs += circuit['inputs'][i]

    model = circuit_to_model(mock_circuit(circuit['circuit']))
    xml_writer = XMLWriter(model)
    sbml = xml_writer.write()
    # print(sbml)
    rr = roadrunner.RoadRunner(sbml)
    runner = Runner(rr)

    nodes = []
    for i in circuit['inputs']:
        nodes += circuit['inputs'][i]

    for i in circuit['outputs']:
        nodes += circuit['outputs'][i]

    if plot:
        nodes += plot
    nodes = list(set(nodes))

    results, outputs = runner.run(circuit['values'], circuit['inputs'], debug=debug, outputs=circuit['outputs'], capture=nodes)

    if plot:
        for i in nodes:
            plt.plot(results[i], label=f'bit {i}')
        plt.xlabel('Time')
        plt.ylabel('Concentration')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.ylim(-1, 11)
        plt.tight_layout()
        plt.show()

    err = False
    logs = []
    if circuit['expected']:
        for i, b in enumerate(circuit['expected']):
            a = outputs[i]
            for k in a:
                if a[k] != b[k]:
                    logs.append(f"{i} {k}: {a} != {b}")
                    err = True

    if err:
        print(f"Test failed for circuit {circuit.get('name', 'unnamed')}:")
        for log in logs:
            print(log)
    else:
        print(f"Test successful for circuit {circuit.get('name', 'unnamed')}")


if __name__ == "__main__":
    # test_circuit(basic_nor, plot=[0,1,2,3])
    # test_circuit(basic_not, plot=[0,1,2])
    # test_circuit(chained_not, plot=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    # test_circuit(multiple_usage, plot=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    test_circuit(basic_dff, plot=[0,1,2,f'p_i_3_1_2'])
