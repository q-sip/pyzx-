import json
import random
from typing import TYPE_CHECKING

import numpy as np
from qiskit import QuantumCircuit

from pyzx import Graph
from pyzx.graph.multigraph import Multigraph
from pyzx.graph.jsonparser import json_to_graph_old
from pyzx import string_to_phase
import pyzx as zx
from pyzx.circuit import Circuit
from fractions import Fraction

import networkx as nx

import quimb.tensor as qtn

H = (1/np.sqrt(2)) * np.array([[1,1],[1,-1]], dtype=complex)

def pi_string_to_fraction(s: str) -> Fraction:
    s = s.replace(" ", "")  # Remove spaces
    if 'π' not in s:
        return Fraction(s)  # No pi, treat as regular number

    if s == 'π':
        return Fraction(1)

    if s.startswith('π/'):
        return Fraction(1, int(s.split('/')[1]))

    if s.endswith('π'):
        return Fraction(int(s[:-1]))

    if 'π/' in s:
        num = s.split('π/')[0]
        denom = s.split('π/')[1]
        return Fraction(int(num), int(denom))

    raise ValueError(f"Unrecognized format: {s}")


def dict_to_graph(d, backend=None):
    """Converts a Python dict representation a graph produced by `graph_to_dict` into
    a pyzx Graph.
    If backend is given, it will be used as the backend for the graph, 
    otherwise the backend will be read from the dict description."""

    if not 'version' in d:
        # "Version is not specified in dictionary, will try to parse it as an older format")
        return json_to_graph_old(d, backend)
    else:
        if d['version'] != 2:
            raise ValueError("Unsupported version "+str(d['version']))
        
    if backend == None:
        backend = d.get('backend', None)
        if backend is None: raise ValueError("No backend specified in dictionary")
    
    g = Graph(backend)
    g.variable_types = d.get('variable_types',{})
    g._inputs = d.get('inputs', [])
    g._outputs = d.get('outputs', [])
    if g.backend == 'multigraph':
        if TYPE_CHECKING:
            assert isinstance(g, Multigraph)
        b = True if d.get('auto_simplify', True) in ('true', True) else False
        g.set_auto_simplify(b)
    for v_d in d['vertices']:
        pos = v_d['pos']
        v = v_d['id']
        g.add_vertex_indexed(v)
        g.set_type(v,v_d['t'])
        g.set_row(v,pos[0])
        g.set_qubit(v,pos[1])
        if 'phase' in v_d:
            g.set_phase(v,string_to_phase(v_d['phase'],g))
        if 'is_ground' in v_d and v_d['is_ground'] == True:
            g.set_ground(v)
        if 'data' in v_d:
            for k,val in v_d['data'].items():
                g.set_vdata(v,k,val)

    for (s,t,et) in d['edges']:
        g.add_edge((s,t),et)

    return g


def json_to_graph(js, backend=None):

    """Converts the json representation of a pyzx graph (as a string or dict) into
    a `Graph`. If JSON is given as a string, parse it first."""
    if isinstance(js, str):
        d = json.loads(js)
    else:
        d = js
    return dict_to_graph(d, backend)


def extract_circuit_from_zx_graph(G: nx.Graph):
    """
    Simplified version of ZX-diagram circuit extraction.
    Input: G - a NetworkX graph representing a ZX-diagram.
    Output: Qiskit QuantumCircuit.
    """
    # 1. Identify input and output nodes
    input_nodes = [n for n, d in G.nodes(data=True) if d.get("is_input")]
    output_nodes = [n for n, d in G.nodes(data=True) if d.get("is_output")]

    n_qubits = len(output_nodes)
    qc = QuantumCircuit(n_qubits)

    # 2. Build initial "frontier": the neighbor of each output (excluding outputs)
    frontier = []
    wire_map = {}
    for i, out in enumerate(output_nodes):
        neighbors = [n for n in G.neighbors(out) if not G.nodes[n].get("is_output")]
        if neighbors:
            v = neighbors[0]
            frontier.append(v)
            wire_map[v] = i

    # 3. Main extraction loop
    while frontier:
        v = frontier.pop(0)
        vdata = G.nodes[v]
        q = wire_map[v]

        # 3a. Apply Hadamard if any incident edge is hadamard
        for neighbor in list(G.neighbors(v)):
            edata = G.get_edge_data(v, neighbor)
            if edata and edata.get("type") == "hadamard":
                qc.h(q)
                G.remove_edge(v, neighbor)

        # 3b. Apply phase if present
        phase = vdata.get("phase", 0)
        if phase != 0:
            if vdata.get("type") == "Z":
                qc.rz(phase, q)
            elif vdata.get("type") == "X":
                qc.rx(phase, q)
        
        # 3c. Check for 2-qubit connections (CNOT/CZ)
        for neighbor in list(G.neighbors(v)):
            if neighbor in wire_map:
                q2 = wire_map[neighbor]
                edata = G.get_edge_data(v, neighbor)
                if vdata.get("type") == "Z" and G.nodes[neighbor].get("type") == "X":
                    qc.cx(q, q2)
                elif vdata.get("type") == "Z" and G.nodes[neighbor].get("type") == "Z":
                    qc.cz(q, q2)
                elif vdata.get("type") == "X" and G.nodes[neighbor].get("type") == "X":
                    qc.cx(q, q2)  # For simplicity; real ZX may use XCX
                G.remove_edge(v, neighbor)

        # 3d. Remove node, update frontier
        for neighbor in list(G.neighbors(v)):
            if not G.nodes[neighbor].get("is_input") and neighbor not in frontier:
                frontier.append(neighbor)
                wire_map[neighbor] = q
        G.remove_node(v)

    # 4. Final swaps/Hadamards for correct output mapping (optional, not implemented here)
    return qc


def pyzx_to_networkx_manual(g: zx.Graph):
    """Manually converts a pyzx.Graph to a networkx.Graph, preserving properties."""
    nxg = nx.Graph()
    for v in g.vertices():
        nxg.add_node(
            v, 
            type=g.type(v), 
            phase=g.phase(v)
        )
    for e in g.edges():
        source, target = g.edge_s(e), g.edge_t(e)
        nxg.add_edge(
            source, 
            target, 
            type=g.edge_type(e)
        )
    return nxg


def node_matcher(node1_data, node2_data):
    """Returns True if nodes have the same type and phase."""
    if node1_data.get('type') != node2_data.get('type'):
        return False
    phase1 = node1_data.get('phase', 0)
    phase2 = node2_data.get('phase', 0)
    # Use a tolerance for comparing floating point phases if necessary
    #print(f"Comparing phases: {phase1} and {phase2} with types {type(phase1)} and {type(phase2)}")
    if type(phase1) == Fraction and type(phase2) == Fraction:
        return phase1 == phase2
    elif type(phase1) == float and type(phase2) == float:
        return np.isclose(phase1, phase2, atol=1e-9)
    elif type(phase1) == int and type(phase2) == Fraction:
        return np.isclose(float(phase1), float(phase2), atol=1e-9)
    elif type(phase1) == Fraction and type(phase2) == int:
        return np.isclose(float(phase1), float(phase2), atol=1e-9)
    are_close = np.isclose(phase1, phase2, atol=1e-9)
    #if not are_close:
    #    print(f"Phase mismatch: {phase1} vs {phase2}")
    return are_close


def edge_matcher(edge1_data, edge2_data):
    """Returns True if edges have the same type."""
    #print(f"Comparing edge types: {edge1_data.get('type')} and {edge2_data.get('type')}")
    return edge1_data.get('type') == edge2_data.get('type')


def phase_poly_term_to_graph(
    coeff: float | Fraction,
    interactions: list[int],
    num_qubits: int,
    prev_circuit: Circuit | None = None
) -> zx.Graph:
    """
    Creates a ZX-diagram for a single term of a phase polynomial.

    The term corresponds to the unitary exp(i * coeff * Z_i * Z_j * ...),
    where i, j, ... are the qubits in the `interactions` list.

    This is implemented by creating a CNOT ladder to compute the parity,
    applying an Rz rotation, and then un-computing the CNOT ladder.

    Args:
        coeff: The phase coefficient of the term (alpha).
        interactions: A list of qubit indices involved in the Pauli Z product.
        num_qubits: The total number of qubits in the circuit.

    Returns:
        A pyzx.Graph representing the circuit for this term.
    """
    interactions = sorted(list(set(interactions)))

    if prev_circuit is None:
        c = Circuit(num_qubits)
    else:
        c = prev_circuit

    if len(interactions) == 1:
        qubit = interactions[0]
        c.add_gate("ZPhase", qubit, phase=2 * coeff)

    elif len(interactions) > 1:
        target_qubit = interactions[-1]

        for i in range(len(interactions) - 1):
            control = interactions[i]
            target = interactions[i+1]
            c.add_gate("CNOT", control, target)

        c.add_gate("ZPhase", target_qubit, phase=2 * coeff)

        for i in range(len(interactions) - 2, -1, -1):
            control = interactions[i]
            target = interactions[i+1]
            c.add_gate("CNOT", control, target)
    else:
        pass

    #g = c.to_graph()
    
    #if not interactions:
    #    g.scalar.add_phase(coeff)

    return c


def z_spider_tensor(num_legs, phase_radians=0.0):
    shape = (2,) * num_legs
    T = np.zeros(shape, dtype=complex)
    T[(0,)*num_legs] = 1.0
    T[(1,)*num_legs] = np.exp(1j * phase_radians)
    return T


def spider_tensor(num_legs, phase=0.0, basis='Z'):
    """
    phase: the same 'phase' as PyZX's internal: p where PyZX uses phase = pi*p.
           If you pass g.phase(v) (which is p), then multiply by pi below.
    """
    phase_radians = np.pi * phase

    if basis == 'Z':
        return z_spider_tensor(num_legs, phase_radians)
    
    T = z_spider_tensor(num_legs, phase_radians)
    for leg in range(num_legs):
        T = np.tensordot(H, T, axes=([1], [leg]))
        # result has H axis 0 inserted at front; move it to the original leg position
        T = np.moveaxis(T, 0, leg)
    return T


def hadamard_tensor():
    """Hadamard edge node."""
    return (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]])


def pyzx_to_networkx_tensor_graph(g: zx.Graph):
    """
    Converts a pyzx.Graph to a NetworkX tensor graph, replacing Hadamard edges
    with explicit H-BOX nodes, computing node tensors, and marking boundaries.
    """
    nxg = nx.Graph()
    # Step 1: Add original vertices
    for v in g.vertices():
        vtype = g.type(v)
        phase = float(g.phase(v)) if g.phase(v) is not None else 0.0
        if vtype == zx.VertexType.BOUNDARY:
            tensor = np.eye(2)  # boundary acts like identity wire
            nxg.add_node(v, tensor=tensor, boundary=True, type=vtype, phase=phase)
        elif vtype == zx.VertexType.Z:
            deg = len(list(g.neighbors(v)))
            tensor = spider_tensor(deg, phase, basis='Z')
            nxg.add_node(v, tensor=tensor, boundary=False, type=vtype, phase=phase)
        elif vtype == zx.VertexType.X:
            deg = len(list(g.neighbors(v)))
            tensor = spider_tensor(deg, phase, basis='X')
            nxg.add_node(v, tensor=tensor, boundary=False, type=vtype, phase=phase)
        elif vtype == zx.VertexType.H_BOX:
            tensor = hadamard_tensor()
            nxg.add_node(v, tensor=tensor, boundary=False, type=vtype, phase=phase)
        else:
            raise ValueError(f"Unknown vertex type {vtype}")

    # Step 2: Process edges — replace Hadamard edges with explicit nodes
    next_id = max(g.vertices()) + 1 if g.num_vertices() > 0 else 0
    for e in g.edges():
        s, t = g.edge_s(e), g.edge_t(e)
        etype = g.edge_type(e)
        if etype == 2:
            # Create intermediate H-BOX node
            h_node = next_id
            next_id += 1
            tensor = hadamard_tensor()
            nxg.add_node(h_node, tensor=tensor, type=zx.VertexType.H_BOX, boundary=False)
            nxg.add_edges_from([(s, h_node), (h_node, t)])
        else:
            nxg.add_edge(s, t, type=etype)

    return nxg


def graph_to_quimb_tn(graph : nx.Graph) -> qtn.TensorNetwork:
    """
    Convert a NetworkX graph with tensor-valued nodes into a Quimb TensorNetwork.

    Each node should have:
        - 'tensor': a NumPy or Quimb tensor array
        - optional 'boundary': bool indicating whether this node is a boundary node

    Each edge will be assigned a unique index label shared by its endpoint tensors.

    Args:
        graph (nx.Graph): Graph whose nodes have 'tensor' attributes (and optional 'boundary').

    Returns:
        qtn.TensorNetwork: The resulting Quimb tensor network.
    """

    # deterministic edge list (tuples sorted by endpoint ordering)
    tensors = []
    edge_list = sorted(tuple(sorted(e)) for e in graph.edges())
    for i, (u, v) in enumerate(edge_list):
        graph[u][v]['index'] = f"e{i}"

    # When building per-node indices:
    def sorted_neighbors_for_node(graph, node):
        # choose a stable sort: by degree, then node id (or by a provided ordering)
        return sorted(graph.neighbors(node))

    for node, data in graph.nodes(data=True):
        neighbors = sorted_neighbors_for_node(graph, node)
        inds = [graph[node][nbr]['index'] for nbr in neighbors]
        if data.get("boundary", False):
            inds.append(f"b_{node}")
        qtensor = qtn.Tensor(data["tensor"], inds=inds, tags=[f"n{node}"])
        tensors.append(qtensor)

    # Step 4: Combine into a tensor network
    tn = qtn.TensorNetwork(tensors)
    return tn


def compose_zx_graphs(g1: zx.Graph, g2: zx.Graph, connected_ratio: float) -> zx.Graph:
    """
    Compose two ZX graphs: connect outputs of g1 to inputs of g2.
    Returns a new ZX graph representing g2 ∘ g1.
    """
    connected_ratio = connected_ratio / 2
    # Make copies to avoid modifying originals
    g2 = g2.copy()
    g_2_index_map = {}
    for v in g2.vertices():
        new_index = g1.add_vertex(ty=g2.type(v), phase=g2.phase(v))
        # Use a reasonable offset for row and qubit to avoid overlap with existing g1 vertices
        row_offset = max([g1.row(v) for v in g1.vertices()]) + 1 if g1.num_vertices() > 0 else 0
        qubit_offset = max([g1.qubit(v) for v in g1.vertices()]) + 1 if g1.num_vertices() > 0 else 0
        g1.set_position(new_index, round(g2.qubit(v) + qubit_offset//2, 3), round(g2.row(v) + row_offset//2, 3))
        g_2_index_map[v] = new_index

    for e in g2.edges():
        s, t = g2.edge_s(e), g2.edge_t(e)
        new_s = g_2_index_map[s]
        new_t = g_2_index_map[t]
        g1.add_edge((new_s, new_t), g2.edge_type(e))

    types = g1.types()
    boundaries = 0
    for v in g1.vertices():
        if types[v] == zx.VertexType.BOUNDARY or types[v] == 0:
            boundaries += 1

    print(f"Total boundaries in composed graph: {boundaries}")
    # Take half of boundaries as outputs
    outs = []
    ins = []
    for v in g1.vertices():
        if (types[v] == zx.VertexType.BOUNDARY or types[v] == 0) and len(outs) < boundaries // 2:
            outs.append(v)
        elif (types[v] == zx.VertexType.BOUNDARY or types[v] == 0) and len(outs) >= boundaries // 2:
            ins.append(v)

    if len(outs) != len(ins):
        raise ValueError("Number of outputs of g1 must match number of inputs of g2 for composition.")

    # Suffle ins and outs
    random.shuffle(outs)
    random.shuffle(ins)

    to_be_connected_ins = ins[:int(boundaries * connected_ratio)]
    to_be_connected_outs = outs[:int(boundaries * connected_ratio)]
    new_outs = outs[int(boundaries * connected_ratio):]
    new_ins = ins[int(boundaries * connected_ratio):]

    # Compose: connect each output of g1 to corresponding input of g2
    for v1, v2 in zip(to_be_connected_ins, to_be_connected_outs):
        # Remove boundary status from g1 output and g2 input
        g1.set_type(v1, zx.VertexType.Z)
        g1.set_phase(v1, 0)
        g1.set_type(v2, zx.VertexType.Z)
        g1.set_phase(v2, 0)
        # Add edge between them
        g1.add_edge(g1.edge(v1, v2), zx.EdgeType.SIMPLE)

    # Set inputs/outputs of the composed graph
    g1.set_inputs(tuple(new_outs))
    g1.set_outputs(tuple(new_ins))

    return g1, len(new_ins)

def qubit_count(circuit) -> int:
    """Returns the number of qubits in the ZX graph based on boundary vertices."""
    count = 0
    for v in circuit.vertices():
        if circuit.type(v) == zx.VertexType.BOUNDARY:
            count += 1
    if count % 2 != 0:
        print("Warning: Odd number of boundary vertices detected. This is not a valid circuit.")
    return count//2