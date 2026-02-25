from time import time
import os
import pyzx as zx
import pyzx.memgraph_simplify as mem
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

# This deletes all data before running the comparison tests
query = "MATCH(N) DETACH DELETE N"
# GraphDatabase.driver(
#     os.getenv("NEO4J_URI"), 
#     auth=(os.getenv("NEO4J_USER"), 
#     os.getenv("NEO4J_PASSWORD"))).session().execute_write(lambda tx: tx.run(query))
# ----
# print('deleted data')

def comparison_1(seed: int, backend: str | None = None):
    """compares neo4j-backend circuit reduction to itself
    backend = "neo4j" for neo4j
    backend = "igraph" for GraphIG
    backend = "simple" or None or leave parameter uninitialized for simple, default graph
    backend = "multigraph" for Multigraph
    backend = "graph_tool" for GraphGT
    """

    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=4, depth=40, seed=seed)

    g = c.to_graph(backend=backend)

    print(f'initial vertices: {g.num_vertices()}')
    zx.full_reduce(g)

    print(f'vertices after reduce: {g.num_vertices()}')
    g.normalize()
    print(f'vertices after normalize: {g.num_vertices()}')
    c_opt = zx.extract_circuit(g.clone())

    return zx.compare_tensors(c, c_opt)


def comparison_2(seed: int, b1: str | None = None, b2: str | None = None):
    """compares one backend to another"""
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=4, depth=40, seed=seed)

    g1 = c.to_graph(backend=b1)
    g2 = c.to_graph(backend=b2)

    zx.full_reduce(g1)
    zx.full_reduce(g2)

    g1.normalize()
    g2.normalize()

    c_opt1 = zx.extract_circuit(g1.copy())
    c_opt2 = zx.extract_circuit(g2.copy())

    return zx.compare_tensors(c_opt1, c_opt2)


# print("simple:", comparison_1(42))
# print("igraph:", comparison_1(42, "igraph")) doesn't work, doesn't contain all mandatory methods
# print("Multigraph:", comparison_1(42, "multigraph"))
# print("graph_tool", comparison_1(42, "graph_tool")) deprecated
# print("quizx-vec", comparison_1(42, "quizx-vec"))
print("Memgraph:", comparison_1(42, "memgraph"))

#print("Neo4j vs simple:", comparison_2(42, "simple", "neo4j"))
