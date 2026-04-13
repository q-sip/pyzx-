from time import time
import os
import pyzx as zx
import pyzx.memgraph_simplify as mem
from pyzx.graph.zxdb.zxdb import ZXdb
from dotenv import load_dotenv


load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))

def comparison_1(seed: int, backend: str | None = None):
    """compares neo4j-backend circuit reduction to itself
    backend = "neo4j" for neo4j
    backend = "igraph" for GraphIG
    backend = "simple" or None or leave parameter uninitialized for simple, default graph
    backend = "multigraph" for Multigraph
    backend = "graph_tool" for GraphGT
    """

    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=4, depth=40, seed=seed)

    print(f"Generated a circuit with depth {c.depth()}")

    g = c.to_graph(backend=backend)

    print(f"Graph has {g.num_vertices()} vertices and {g.num_edges()} edges")

    zxdb = ZXdb(URI, AUTH[0], AUTH[1], graph_id=g.graph_id)
    try:
        zxdb.full_reduce()
    finally:
        zxdb.close()

    print(f"After full_reduce, graph has {g.num_vertices()} vertices and {g.num_edges()} edges")

    g.normalize()

    c_opt = zx.extract_circuit(g.clone())

    return zx.compare_tensors(c, c_opt)


def comparison_2(seed: int, b1: str | None = None, b2: str | None = None):
    """compares one backend to another"""
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=9, depth=70, seed=seed)

    g1 = c.to_graph(backend=b1)
    g2 = c.to_graph(backend=b2)

    zxdb = ZXdb(URI, AUTH[0], AUTH[1], graph_id=g1.graph_id)
    try:
        zxdb.full_reduce()
    finally:
        zxdb.close()

    zx.full_reduce(g2)

    g1.normalize()
    g2.normalize()
    
    print(f"memgraph nodes: {g1.num_vertices()}")
    print(f"simple nodes: {g2.num_vertices()}")

    c_opt1 = zx.extract_circuit(g1.clone())
    c_opt2 = zx.extract_circuit(g2.copy())

    return zx.compare_tensors(c_opt1, c_opt2)


###for q in range(1, 10):
    #for d in range(1, 100, 10):
       # for s in range(11):
         #   print("Memgraph:", comparison_1(s, "memgraph"))



#print("simple:", comparison_1(42))
# print("igraph:", comparison_1(42, "igraph")) doesn't work, doesn't contain all mandatory methods
#print("Multigraph:", comparison_1(42, "multigraph"))
# print("graph_tool", comparison_1(42, "graph_tool")) deprecated
# print("quizx-vec", comparison_1(42, "quizx-vec"))
#print("Memgraph-ZXdb:", comparison_1(42, "memgraph"))

print("Memgraph-ZXdb vs simple:", comparison_2(42, "memgraph", "simple"))