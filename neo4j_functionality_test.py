import os
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from pyzx.symbolic import Poly
from fractions import Fraction
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()



URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()


g = GraphNeo4j(
    uri=URI, user=os.getenv("NEO4J_USER"), password=os.getenv("NEO4J_PASSWORD"),
    database="neo4j", 
    graph_id="test_graph"
)


query =""" MATCH (N) DETACH DELETE N"""

g.clear_graph(query)

v_ids = g.create_graph(
    vertices_data=[
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 2},
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
    ],
    edges_data=[
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.HADAMARD),
        ((2, 3), EdgeType.SIMPLE),
    ],
    inputs=[0],
    outputs=[3]
)
print("vdata_keys for vertex 1:", g.vdata_keys(1))

print("vdata for vertex 2:", g.vdata(2, "row"))

#print(f"Clearing vdata for vertex 3"), g.clear_vdata(3)

print(f"Set vdata for vertex 1: qubit=5"), g.set_vdata(1, "qubit", 5)

print(f"Clear all edata for edge (1,2)"), g.clear_edata((1,2))

print(f"Print edata keys for edge (0,1): {g.edata_keys((0,1))}")

print(f"Set edata for edge (2,3:) {g.set_edata((2,3), "t", 2)}")

print(f"Print edata for edge (2,3)): {g.edata((2,3), "t")}")

