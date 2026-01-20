import os
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))


# Runnataan virtual environmentissa. Kun ollaan venvissä, voidaan: python3 neo4j_functionality_test.py.

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()


g = GraphNeo4j(uri=URI, user=os.getenv("NEO4J_USER"), password=os.getenv("NEO4J_PASSWORD"), database="neo4j", graph_id="test_graph")

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
count = g.vindex()
print(f'count = {count}')