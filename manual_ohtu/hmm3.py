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


g = GraphMemgraph()
delete_all(g)

circ = px.Circuit(5)
circ.add_gate("TOF", 0, 1, 4)
circ.add_gate("TOF", 2, 4, 3)
circ.add_gate("TOF", 0, 1, 4)
px.draw(circ)

circ = circ.to_graph(backend="memgraph")
# px.to_graph_like(circ)
# px.draw(circ)
px.to_graph_like(circ)
kala = px.is_graph_like(circ)
print(f"is graph like: {kala}", end='\n')

# px.draw(circ, labels=True)

px.simplify.interior_clifford_simp(circ)
# px.draw(circ, labels=True)
kala = px.is_graph_like(circ)
print(f"is graph like: {kala}", end='\n')