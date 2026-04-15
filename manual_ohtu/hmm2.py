import pyzx as px
from pyzx import VertexType, EdgeType
from pyzx.graph.graph_memgraph import GraphMemgraph




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

def delete_all(g: GraphMemgraph):
    query = """MATCH (n) DETACH DELETE n;"""
    g.arb_quer_write(query=query)

def spider_simp(g: GraphMemgraph):
    query = """
MATCH (n:Node)-[r:Wire]->(m:Node)
  WHERE n.t = m.t AND r.t = 1
DELETE r

//Set the new phase
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase
SET n.phase = totalPhase
WITH *

//Find the original connections
OPTIONAL MATCH (m:Node)-[r4:Wire]->(other4:Node)
OPTIONAL MATCH (other5:Node)-[r5:Wire]->(m:Node)
WITH *

//Join the from our node to other relationships
FOREACH (_ IN CASE WHEN r4 IS NOT NULL THEN [1] ELSE [] END |
CREATE (n)-[kala4:Wire]->(other4)
set kala4 = r4
)
WITH *

//Join the from other to our node relationships
FOREACH (_ IN CASE WHEN r5 IS NOT NULL THEN [1] ELSE [] END |
CREATE (other5)-[kala5:Wire]->(n)
SET kala5 = r5
)

//Delete the second node
WITH *
DETACH DELETE m;
    """
    g.arb_quer_write(query=query,)

vertices_data = [
    {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 0},
    {"ty": VertexType.X, "qubit": 0, "row": 1},
    {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
    {"ty": VertexType.Z, "qubit": 0, "row": 1},
    {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 2},
    {"ty": VertexType.Z, "qubit": 0, "row": 2, 'phsae': 2},
    {"ty": VertexType.X, "qubit": 0, "row": 3, 'phase': 1},
    {'ty': VertexType.BOUNDARY, 'qubit': 0, 'row': 4},
]
edges_data = [
    ((0, 1), EdgeType.SIMPLE),
    ((1, 2), EdgeType.SIMPLE),
    ((1, 3), EdgeType.SIMPLE),
    ((3, 4), EdgeType.HADAMARD),
    ((3, 5), EdgeType.SIMPLE),
    ((5, 6), EdgeType.SIMPLE),
    ((6, 7), EdgeType.SIMPLE),
]

g = GraphMemgraph()
delete_all(g)
g.create_graph(vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[7])

s = g.copy(backend="simple")
orginal = g.copy(backend="simple")

tens1 = px.compare_tensors(s, g)
print(f"tens1: {tens1}", end='\n')
# px.draw(s, labels=True)
# px.draw(g, labels=True)
# input("ohi")
px.to_gh(s)
arb_write(g)
input("kala")
tens2 = px.compare_tensors(s, g)
print(f"tens2: {tens2}", end='\n')
# px.draw(s, labels=True)
# px.draw(g, labels=True)
# input("sad")
# g = s.copy(backend="memgraph")
# px.draw(g, labels=True)
# s2 = g.copy(backend="simple")
# px.draw(s2, labels=True)
# # px.draw(g, labels=True)
# g2 = s.clone().copy(backend="memgraph")


# px.draw(g2, labels=True)

#
# tens3 = px.compare_tensors(g, g2)
# print(f"tens3: {tens3}", end='\n')
#
# tens4 = px.compare_tensors(s, g2)
# print(f"tens4: {tens4}", end='\n')

# s.normalize()
# s_ext = px.extract_circuit(s.clone())
# g.normalize()
#
# g_ext = px.extract_circuit(g.clone())
#
# print(f'Comparing: {px.compare_tensors(g_ext, s_ext)}')