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

g = GraphMemgraph(
    database="memgraph",
    graph_id="test_graph",
)

qubits = 10
depth = 20

g_mem = zx.generate.cliffordT(qubits, depth, backend="memgraph", seed=10)
g_s = zx.generate.cliffordT(qubits, depth,backend="memgraph", seed=10)
print("before")
print(g_mem)
g_mem.compose(g_s)

print(g_mem)
print("after")
