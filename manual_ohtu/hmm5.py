import fractions

import pyzx as px
from pyzx import VertexType, EdgeType
from pyzx.graph.graph_memgraph import GraphMemgraph


def delete_all(g: GraphMemgraph):
    query = """MATCH (n) DETACH DELETE n;"""
    g.arb_quer_write(query=query)

def arb_write(g: GraphMemgraph):
    query = """
    MATCH (n:Node)-[r:Wire]-(m:Node) 
    WHERE n.t = 2 
    AND n.graph_id = "graph_test_zxdb"
    SET n.t = 1
    WITH r AS wire
    SET wire.t = CASE WHEN wire.t = 1 THEN 2 ELSE 1 END
    RETURN wire;
    """
    g.arb_quer_write(query=query, kala="koira", kissa="mieto")



vertices_data2 = [
    {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 2},
    {"ty": VertexType.Z, "qubit": 0, "row": 2},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
]

edges_data2 = [
    ((0, 1), EdgeType.SIMPLE),
    ((1, 2), EdgeType.SIMPLE),
    ((2, 3), EdgeType.SIMPLE),
    ((3, 4), EdgeType.SIMPLE),
    ((4, 9), EdgeType.SIMPLE),


    ((5, 1), EdgeType.HADAMARD),
    ((5, 2), EdgeType.HADAMARD),
    ((5, 3), EdgeType.HADAMARD),
    ((5, 4), EdgeType.HADAMARD),

    ((6, 1), EdgeType.HADAMARD),
    ((6, 2), EdgeType.HADAMARD),
    ((6, 3), EdgeType.HADAMARD),
    ((6, 4), EdgeType.HADAMARD),


    ((5, 7), EdgeType.HADAMARD),
    ((6, 8), EdgeType.HADAMARD),
]

g = GraphMemgraph()
delete_all(g)
g.create_graph(vertices_data=vertices_data2, edges_data=edges_data2, inputs=[0], outputs=[11])
g.add_to_phase(7, fractions.Fraction(1, 2))
g.add_to_phase(8, fractions.Fraction(1, 4))
# px.to_graph_like(g)
input("kala")
px.simplify.gadget_simp(g)
# simple = g.copy(backend="simple")
# px.simplify.pivot_gadget_simp(simple)
# g = simple.copy(backend="memgraph")
# px.full_reduce(g)
# px.simplify.to_graph_like(g)

# simple = g.copy(backend="simple")
# px.draw(simple)