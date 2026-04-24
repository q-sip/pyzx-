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

def bonus_nodet(g: GraphMemgraph):
    query = """
    CREATE (n:Node)
    SET n.kala = 1
    with *
    MATCH (m:Input)
    CREATE (n) -[r:Wire]->(m)
    SET r.kala = 1;
    """
    g.arb_quer_write(query=query)

def bonus_nodet_end(g: GraphMemgraph):
    query = """
    CREATE (n2:Node)
    SET n2.kala = 1
    with *
    MATCH (m2:Output)
    CREATE (m2)-[r2:Wire]->(n2)
    SET r2.kala = 1;
    """
    g.arb_quer_write(query=query)




vertices_data2 = [
    {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
    # {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 2},
    {"ty": VertexType.Z, "qubit": 0, "row": 2},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    # {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
]

edges_data2 = [
    ((0, 1), EdgeType.HADAMARD),
    ((1, 2), EdgeType.HADAMARD),
    ((2, 3), EdgeType.HADAMARD),
    ((3, 4), EdgeType.HADAMARD),
    ((4, 9), EdgeType.HADAMARD),


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
g.create_graph(vertices_data=vertices_data2, edges_data=edges_data2, inputs=[0], outputs=[9])
g.add_to_phase(7, fractions.Fraction(1, 2))
g.add_to_phase(8, fractions.Fraction(1, 4))

# eka = g.add_vertex(ty=VertexType.Z, qubit=0, row=0)
# toka = g.add_vertex(ty=VertexType.Z, qubit=0, row=0)
# g.add_to_phase(0, 10)
# g.add_to_phase(1, 10)
# g.add_to_phase(9, 11)
# g.add_to_phase(9, 11)


def add_isolated(g):
    g.add_edge((0, 10), EdgeType.HADAMARD)
    g.add_edge((1, 10), EdgeType.HADAMARD)
    g.add_edge((9, 11), EdgeType.HADAMARD)
    g.add_edge((4, 11), EdgeType.HADAMARD)
    g.remove_edge((4, 9))
    g.remove_edge((0, 1))

    g.add_vertex(ty=VertexType.Z, qubit=10, row=2)

    island1 = g.add_vertex(ty=VertexType.Z, qubit=10, row=4)
    island2 = g.add_vertex(ty=VertexType.Z, qubit=10, row=4)
    g.add_edge((island1, island2), EdgeType.HADAMARD)

    island3 = g.add_vertex(ty=VertexType.Z, qubit=10, row=4)
    island4 = g.add_vertex(ty=VertexType.Z, qubit=10, row=4)
    g.add_edge((island3, island4), EdgeType.SIMPLE)
    g.add_edge((island3, island4), EdgeType.SIMPLE)
    g.add_edge((island3, island4), EdgeType.SIMPLE)


# add_isolated(g)

# big_island1 = g.add_vertex(ty=VertexType.Z, qubit=10, row=5)
# big_island2 = g.add_vertex(ty=VertexType.Z, qubit=10, row=5)
# big_island3 = g.add_vertex(ty=VertexType.Z, qubit=10, row=5)
# big_island4 = g.add_vertex(ty=VertexType.Z, qubit=10, row=5)
#
# g.add_edge((big_island1, big_island2), EdgeType.SIMPLE)
# g.add_edge((big_island1, big_island3), EdgeType.SIMPLE)
# g.add_edge((big_island3, big_island4), EdgeType.SIMPLE)

# px.simplify.remove_isolated_vertices(g)
# for internal in range(0, 30):
#     # g.remove_isolated_vertices()
#     px.simplify.id_simp(g)

# px.to_graph_like(g)
# input("kala")
# px.simplify.gadget_simp(g)
# simple = g.copy(backend="simple")
# px.simplify.pivot_gadget_simp(simple)
# g = simple.copy(backend="memgraph")
# breakpoint()
# px.full_reduce(g)
# px.simplify.to_graph_like(g)

# simple = g.copy(backend="simple")
# px.draw(simple)


# bonus_nodet(g)
# bonus_nodet_end(g)