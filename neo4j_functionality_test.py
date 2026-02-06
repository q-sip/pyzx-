import os
from time import time
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from pyzx.symbolic import Poly
from fractions import Fraction
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pyzx.simplify import full_reduce
import pyzx as zx

load_dotenv()


URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

# with GraphDatabase.driver(URI, auth=AUTH) as driver:
#     driver.verify_connectivity()
#     g = zx.Graph(backend='neo4j')
#     print("Putsataan vanhaa graafia")
#     query =""" MATCH (N) DETACH DELETE N"""
#     g.clear_graph(query)
    

#     print("Luodaan graafi")

#     try: 
#         g = zx.generate.cliffordT(3, 20, backend='neo4j')

#     except ImportError:
#         print("Neo4j backend ei saatavilla")
#         raise
#     except Exception as e:
#         print(f"Virhe graafin luonnissa {e}")
#         raise  
    
#     print("-"*30)
#     print(f"Alkuperäisessä graafissa: {g.num_vertices()} nodea, {g.num_edges()} kaarta")

#     try:
#         full_reduce(g)
#     except Exception as e:
#         print(f"full_reduce hajos: {e}")
#         raise

#     print("-" * 30)
#     print(f"Lopullisessa graafissa: {g.num_vertices()} nodea, {g.num_edges()} kaarta")
                                        





#MANUAALINEN GRAAFI TESTAUKSEEN!

g = GraphNeo4j(
    uri=URI,
    user=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    database="neo4j",
    graph_id="test_graph",
)


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
    outputs=[3],
)
print(g.type(3))



    
