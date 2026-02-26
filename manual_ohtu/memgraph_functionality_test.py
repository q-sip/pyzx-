"""Manual Neo4j graph exercises for local testing."""

import os
from time import time
import random
from fractions import Fraction
import numpy as np

from dotenv import load_dotenv
import pyzx as zx
from pyzx.graph.graph_memgraph import GraphMemgraph
from pyzx.graph.graph_s import GraphS
from pyzx.utils import EdgeType, VertexType
from pyzx import memgraph_simplify as mem

load_dotenv()


URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("MEMGRAPH_USER"), os.getenv("MEMGRAPH_PASSWORD"))

# with GraphDatabase.driver(URI, auth=AUTH) as driver:
#     driver.verify_connectivity()
#     g = zx.Graph(backend='neo4j')
#     print("Putsataan vanhaa graafia")

#     print("Luodaan graafi")

#     try:
#         g = zx.generate.cliffordT(3, 20, backend='neo4j')
#     except ImportError:
#         print("Neo4j backend ei saatavilla")
#         raise
#     except Exception as e:
#         print(f"Virhe graafin luonnissa {e}")
#         raise
#     print("-"*30)
#     print(f"Alkuperäisessä graafissa: {g.num_vertices()} nodea, {g.num_edges()} kaarta")

#     try:
#         full_reduce(g)
#     except Exception as e:
#         print(f"full_reduce hajos: {e}")
#         raise

#     print("-" * 30)
#     print(f"Lopullisessa graafissa: {g.num_vertices()} nodea, {g.num_edges()} kaarta")


# MANUAALINEN GRAAFI TESTAUKSEEN!

g = GraphMemgraph(
    uri=URI,
    user=AUTH[0],
    password=AUTH[1],
    database="memgraph",
    graph_id="test_graph",
)
g.remove_all_data()

def graph_step_by_step():
    """Testaa graafin luomista askel askeleelta"""
    i = g.add_vertex(0, 0, 0)
    v = g.add_vertex(1, 0, 1, Fraction(1, 2))
    w = g.add_vertex(2, 0, 2, Fraction(-1, 2))
    o = g.add_vertex(0, 0, 3)
    g.add_edges([(i, v), (v, w), (w, o)])


def large_graph():
    """Suurempi graafi"""
    _ = g.create_graph(
        vertices_data=[
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.Z, "qubit": 0, "row": 2},
            {"ty": VertexType.X, "qubit": 0, "row": 3},
            {"ty": VertexType.X, "qubit": 0, "row": 4},
            {"ty": VertexType.Z, "qubit": 0, "row": 5},
            {"ty": VertexType.X, "qubit": 0, "row": 6},
            {"ty": VertexType.Z, "qubit": 0, "row": 7},
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 8},
        ],
        edges_data=[
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),  # Z-Z spider fusion candidate
            ((2, 3), EdgeType.HADAMARD),  # Hadamard edge
            ((3, 4), EdgeType.SIMPLE),  # X-X spider fusion candidate
            ((4, 5), EdgeType.HADAMARD),  # Hadamard edge
            ((5, 6), EdgeType.SIMPLE),
            ((6, 7), EdgeType.SIMPLE),
            ((7, 8), EdgeType.SIMPLE),
        ],
        inputs=[0],
        outputs=[8],
    )
    print(g.types())


def graph_full_reduce():
    """Neo4j graafin full reduce"""
    graph = zx.generate.cliffordT(3,20, backend="memgraph")
    zx.simplify.full_reduce(graph)
    print(f'num vertices ===== {graph.num_vertices()}')
    #graph.normalise()

#graph_step_by_step()
# graph_full_reduce()


def iterable_graph_creation():
    """Create and repeatedly reduce graphs of increasing size."""
    num = 0
    choices = [VertexType.X, VertexType.Z]
    while True:
        g.remove_all_data()
        g.add_vertex(VertexType.BOUNDARY, 0, 0)
        g.add_vertex(VertexType.BOUNDARY, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.X, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.X, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        sg = GraphS()
        sg.add_vertex(VertexType.BOUNDARY, 0, 0)
        sg.add_vertex(VertexType.BOUNDARY, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        sg.add_vertex(VertexType.X, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        sg.add_vertex(VertexType.X, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        sg.add_vertex(VertexType.Z, 0, 0)
        for e in [(0, 2), (2, 3), (3, 4), (4, 1)]:
            g.add_edge(e)
        for _ in range(num):
            g.add_vertex(random.choice(choices), 0, 0)
            g.add_vertex(random.choice(choices), 0, 0)
            g.add_edge(
                (
                    random.randint(2, g.num_vertices() - 1),
                    random.randint(2, g.num_vertices() - 1),
                )
            )
        for e in [(0, 2), (2, 3), (3, 4), (4, 1)]:
            sg.add_edge(e)
        for _ in range(num):
            sg.add_vertex(random.choice(choices), 0, 0)
            sg.add_vertex(random.choice(choices), 0, 0)
            sg.add_edge(
                (
                    random.randint(2, sg.num_vertices() - 1),
                    random.randint(2, sg.num_vertices() - 1),
                )
            )
        # tää ei sit toimi varmaa, koska full reduce poistaa joitain nodeja.
        # Ainaki mulla crashas, koska vertex 2 ei ollu tyyppia.
        print(f'memgraph full reduce starting...')
        time1 = time()
        mem.full_reduce(g)
        time2 = time()
        print(f'memgraph took {time2-time1}s')
        print(f'simple graph full reduce starting...')
        time1 = time()
        zx.full_reduce(sg)
        time2 = time()
        print(f'simple graph took {time2-time1}s')
        # t = zx.compare_tensors(g, sg)
        print(f"{num} succesful")
        num += 1

def test_num_vertices_against_simple_graph(qubits, depth):
    g_mem = zx.generate.cliffordT(qubits, depth, backend="memgraph", seed=10)
    
    # Store initial
    g_mem_initial = g_mem.copy(backend="simple")
    
    g_s = zx.generate.cliffordT(qubits, depth, seed=10)

    print(f"depth={depth}, qubits={qubits} memgraph full reduce starting...")
    time1 = time()
    mem.full_reduce(g_mem)
    time2 = time()
    print(f"depth={depth}, qubits={qubits} memgraph took {time2 - time1}s")
    print(f"depth={depth}, qubits={qubits} simplegraph full reduce starting...")
    time1 = time()
    zx.full_reduce(g_s)
    time2 = time()
    print(f"depth={depth}, qubits={qubits} simplegraph took {time2 - time1}s")

    g_mem_num = g_mem.num_vertices()
    g_s_num = g_s.num_vertices()
    print(f'g_mem vertices: {g_mem_num}, g_s vertices: {g_s_num}')

    print("Comparing tensors...")
    # Create a local copy of the memgraph graph to avoid database overhead during tensor calculation
    # Using backend=None might default to Memgraph if not handled carefully, 
    # so we explicitly request a simple graph backend if possible, or rely on BaseGraph.copy mechanics.
    # Actually, simpler way: define a new GraphS and copy into it if needed, 
    # or rely on compare_tensors handling it (slowly).
    # Fast approach:
    try:
        # Assuming copy(backend="simple") works or returns a GraphS
        g_mem_local = g_mem.copy(backend="simple")
    except Exception:
        # Fallback if backend string not recognized, just use copy() and hope it's local
        # or implement manual copy if needed.
        # But actually, pyzx.Graph(backend=None) usually returns GraphS.
        # So providing backend="simple" to copy() usually works.
        g_mem_local = g_mem

    # Debug inputs/outputs
    print(f"Inputs: {g_mem_local.inputs()}")
    print(f"Outputs: {g_mem_local.outputs()}")
    for o in g_mem_local.outputs():
        d = len(list(g_mem_local.neighbors(o)))
        print(f"Output {o} degree: {d} neighbors: {list(g_mem_local.neighbors(o))}")
        if d != 1:
            print(f"WARNING: Output {o} has degree {d} != 1")
    
    # Also check inputs
    for i in g_mem_local.inputs():
        d = len(list(g_mem_local.neighbors(i)))
        print(f"Input {i} degree: {d}")

    # Create valid local copies for tensor comparison
    try:
        g_mem_initial_copy = g_mem_initial.copy(backend="simple")
    except:
        g_mem_initial_copy = g_mem_initial
        
    try:
        g_mem_copy = g_mem.copy(backend="simple")
    except:
        g_mem_copy = g_mem

    print(f"Comparing Initial vs Memgraph Reduced...")
    if zx.compare_tensors(g_mem_initial_copy, g_mem_copy, preserve_scalar=False):
        print("Initial vs Memgraph Reduced: MATCH!")
    else:
        print("Initial vs Memgraph Reduced: MISMATCH!")

    print(f"Comparing Initial vs SimpleGraph Reduced...")
    if zx.compare_tensors(g_mem_initial_copy, g_s, preserve_scalar=False):
        print("Initial vs SimpleGraph Reduced: MATCH!")
    else:
        print("Initial vs SimpleGraph Reduced: MISMATCH!")

    print("Comparing Memgraph Reduced vs SimpleGraph Reduced...")
    # If comparison fails, we want to know why, but first let's just try
    try:
        match = zx.compare_tensors(g_mem_copy, g_s, preserve_scalar=False)
        if match:
            print("Tensors match (up to scalar)!")
        else:
            print("Tensors do NOT match!")
            
            # Debugging the mismatch
            t_mem = zx.tensorfy(g_mem_local)
            t_s = zx.tensorfy(g_s)
            
            # Check for zero tensors
            if np.allclose(t_mem, 0):
                print("DEBUG: Memgraph tensor is effectively ZERO!")
            if np.allclose(t_s, 0):
                print("DEBUG: SimpleGraph tensor is effectively ZERO!")
                
            # Print shapes and a few values
            print(f"Memgraph tensor shape: {t_mem.shape}")
            print(f"SimpleGraph tensor shape: {t_s.shape}")
            
            flat_mem = t_mem.flatten()
            flat_s = t_s.flatten()
            
            # Find first non-zero to compare ratio
            idx = -1
            for i in range(len(flat_s)):
                if abs(flat_s[i]) > 1e-10:
                    idx = i
                    break
            
            if idx != -1:
                val_s = flat_s[idx]
                val_mem = flat_mem[idx]
                if abs(val_mem) > 1e-10:
                    ref_ratio = val_s / val_mem
                    print(f"Ref Ratio at {idx}: {ref_ratio} (Mag: {abs(ref_ratio)}, Phase: {np.angle(ref_ratio)/np.pi} pi)")
                    
                    # Check other indices
                    mismatches = 0
                    for i in range(len(flat_s)):
                        if abs(flat_s[i]) > 1e-10:
                            if abs(flat_mem[i]) < 1e-10:
                                print(f"Index {i}: SG non-zero ({flat_s[i]}), MEM zero!")
                                mismatches += 1
                            else:
                                ratio = flat_s[i] / flat_mem[i]
                                if not np.isclose(ratio, ref_ratio):
                                    print(f"Index {i}: Ratio mismatch! {ratio} vs {ref_ratio}")
                                    mismatches += 1
                        elif abs(flat_mem[i]) > 1e-10:
                             print(f"Index {i}: SG zero, MEM non-zero ({flat_mem[i]})!")
                             mismatches += 1
                        
                        if mismatches > 5:
                            print("Too many mismatches, stopping.")
                            break
                else:
                    print("MEM value is zero at this index (mismatch!)")
            else:
                print("SG tensor is all zeros (unexpected)")

    except Exception as e:
        print(f"Tensor comparison failed with error: {e}")

def test_depths_qubits(start_qubits: int, end_qubits: int, max_depth: int = 100):
    """Run memgraph full reduce over qubit/depth grid."""
    for qubits in range(start_qubits, end_qubits + 1):
        print(f"\n=== qubits={qubits} ===")
        for depth in range(0, max_depth + 1, 10):
            g_mem = zx.generate.cliffordT(qubits, depth, backend="memgraph", seed=10)
            g_s = zx.generate.cliffordT(qubits, depth, seed=10)
            try:
                print(f"depth={depth}, qubits={qubits} memgraph full reduce starting...")
                time1 = time()
                mem.full_reduce(g_mem)
                time2 = time()
                print(f"depth={depth}, qubits={qubits} memgraph took {time2 - time1}s")
                print(f"depth={depth}, qubits={qubits} simplegraph full reduce starting...")
                time1 = time()
                zx.full_reduce(g_s)
                time2 = time()
                print(f"depth={depth}, qubits={qubits} simplegraph took {time2 - time1}s")
                g_mem_num = g_mem.num_vertices()
                g_s_num = g_s.num_vertices()
                print(f'g_mem vertices: {g_mem_num}, g_s vertices: {g_s_num}')
                print('Comparing...')
                if g_mem_num == g_s_num:
                    print('Success')
                else:
                    print('fail')
                # print(f'DEBUG: num_vertices ==== {g_mem.num_vertices()}')
                # print(f'DEBUG: vertices ==== {g_mem.vertices()}')
                # t = zx.compare_tensors(g_s, g_mem)
                # if t:
                #     print('tensors match')
                # else:
                #     print('fail')
            finally:
                g_mem.remove_all_data()
                g_mem.close()



# iterable_graph_creation()
# test_depths_qubits(2, 100, 100)
# large_graph()
# test_num_vertices_against_simple_graph(2, 100)
c = zx.generate.CNOT_HAD_PHASE_circuit(2, 20, seed=50)
g = c.to_graph(backend='memgraph')