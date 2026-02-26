import os
from pyzx.utils import VertexType, EdgeType
from pyzx.graph.graph_memgraph import GraphMemgraph
import pyzx as zx
URI = os.getenv("DB_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
def large_graph():
    """Suurempi graafi"""
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=2, depth=20, seed=50)
    print('Generating graph...')
    g = c.to_graph(backend='memgraph')
    #i = input('Graph generated')

    print('Full reducing...')
    zx.full_reduce(g)

    print('Normalizing...')
    g.normalize()
    
    print('Full reduce successful!')


large_graph()