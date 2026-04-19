import random
from fractions import Fraction
import pyzx as zx

def CNOT_HAD_PHASE_graph(
        qubits: int,
        depth: int,
        p_had: float = 0.2,
        p_t: float = 0.2,
        clifford: bool = False
        ) -> zx.Graph:
    """
    Construct a ZX-Graph consisting of CNOT, HAD and phase gates.
    The default phase gate is the T gate, but if ``clifford=True``, then
    this is replaced by the S gate.

    Args:
        qubits: number of qubits of the circuit
        depth: number of gates in the circuit
        p_had: probability that each gate is a Hadamard gate
        p_t: probability that each gate is a T gate (or if ``clifford`` is set, S gate)
        clifford: when set to True, the phase gates are S gates instead of T gates.

    Returns:
        A ZX-Graph representing the random circuit.
    """
    p_cnot = 1 - p_had - p_t
    g = zx.Graph()
    # Create input boundary vertices
    inputs = []
    outputs = []
    qubit_vertices = []
    for i in range(qubits):
        v_in = g.add_vertex(zx.VertexType.BOUNDARY, i, 0)
        inputs.append(v_in)
        qubit_vertices.append(v_in)
    current_row = 1

    for _ in range(depth):
        r = random.random()
        if r > 1 - p_had:
            # Hadamard gate
            q = random.randrange(qubits)
            v_h = g.add_vertex(zx.VertexType.H_BOX, q, current_row)
            g.add_edge(g.edge(qubit_vertices[q], v_h), zx.EdgeType.SIMPLE)
            qubit_vertices[q] = v_h
        elif r > 1 - p_had - p_t:
            # Phase gate
            q = random.randrange(qubits)
            v_z = g.add_vertex(zx.VertexType.Z, q, current_row,
                               Fraction(1, 4) if not clifford else Fraction(1, 2))
            g.add_edge(g.edge(qubit_vertices[q], v_z), zx.EdgeType.SIMPLE)
            qubit_vertices[q] = v_z
        else:
            # CNOT gate
            tgt = random.randrange(qubits)
            while True:
                ctrl = random.randrange(qubits)
                if ctrl != tgt:
                    break
            v_ctrl = g.add_vertex(zx.VertexType.Z, ctrl, current_row)
            v_tgt = g.add_vertex(zx.VertexType.X, tgt, current_row)
            g.add_edge(g.edge(qubit_vertices[ctrl], v_ctrl), zx.EdgeType.SIMPLE)
            g.add_edge(g.edge(qubit_vertices[tgt], v_tgt), zx.EdgeType.SIMPLE)
            g.add_edge(g.edge(v_ctrl, v_tgt), zx.EdgeType.SIMPLE)
            qubit_vertices[ctrl] = v_ctrl
            qubit_vertices[tgt] = v_tgt
        current_row += 1

    # Add output boundary vertices
    for i in range(qubits):
        v_out = g.add_vertex(zx.VertexType.BOUNDARY, i, current_row)
        g.add_edge(g.edge(qubit_vertices[i], v_out), zx.EdgeType.SIMPLE)
        outputs.append(v_out)

    g.set_inputs(tuple(inputs))
    g.set_outputs(tuple(outputs))
    return g

def PHASE_GADGET_GRAPH(
        gadget_sizes: list[int],
        ) -> zx.Graph:
    """
    Construct a ZX-Graph consisting of phase gadgets.

    Args:
        gadget_sizes: list of integers representing the sizes of each phase gadget
        depth: number of phase gadgets in the circuit
        max_gadget_size: maximum size of each phase gadget
    Returns:
        A ZX-Graph representing the random circuit.

    """
    g = zx.Graph()
    # Create input boundary vertices
    boundary_index = g.add_vertex(zx.VertexType.BOUNDARY)
    green_in_index = g.add_vertex(zx.VertexType.Z, phase = Fraction(0))
    g.add_edge(g.edge(boundary_index, green_in_index), zx.EdgeType.SIMPLE)
    for size in gadget_sizes:
        green_out_index = g.add_vertex(zx.VertexType.Z, phase = Fraction(0))
        # Create size many X spider vertices
        red_spiders = []
        for i in range(size):
            red_spider_index = g.add_vertex(zx.VertexType.X, phase = Fraction(0))
            # Create green spider with random phase
            green_spider_index = g.add_vertex(zx.VertexType.Z, phase = Fraction(random.randint(0, 3), 4))
            red_spiders.append(red_spider_index)
            # Connect red spider to green spider
            g.add_edge((red_spider_index, green_spider_index), zx.EdgeType.SIMPLE)
        # Create all to all connectivity between green spiders and green_in and green_out spiders
        for red_spider in red_spiders:
            g.add_edge((green_in_index, red_spider), zx.EdgeType.SIMPLE)
            g.add_edge((red_spider, green_out_index), zx.EdgeType.SIMPLE)
        # Update green_in and green_out for next gadget
        green_in_index = green_out_index
        
        #green_in_index = g.add_vertex(zx.VertexType.Z, phase = Fraction(0))
    # Connect last green_out to boundary
    boundary_out_index = g.add_vertex(zx.VertexType.BOUNDARY)
    g.add_edge((green_out_index, boundary_out_index), zx.EdgeType.SIMPLE)
    g.set_inputs((boundary_index,))
    g.set_outputs((boundary_out_index,))
    return g