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
        {"ty": VertexType.X, "qubit": 0, "row": 3},
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 4},
    ],
    edges_data=[
        ((0, 1), EdgeType.SIMPLE),
        ((0, 1), EdgeType.HADAMARD),
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.HADAMARD),
        ((1, 2), EdgeType.SIMPLE),
        ((2, 3), EdgeType.HADAMARD),
        ((3, 4), EdgeType.SIMPLE),
    ],
    inputs=[0],
    outputs=[3],
)
print(g.type(3))


def graph_step_by_step():
    i = g.add_vertex(0,0,0)
    v = g.add_vertex(1,0,1, Fraction(1,2))
    w = g.add_vertex(2,0,2, Fraction(-1,2))
    o = g.add_vertex(0,0,3)
    g.add_edges([(i,v), (v,w), (w,o)])

def large_graph():
    v_ids = g.create_graph(
        vertices_data=[
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.Z, "qubit": 0, "row": 2},
            {"ty": VertexType.X, "qubit": 0, "row": 3},
            {"ty": VertexType.X, "qubit": 0, "row": 4},
            {"ty": VertexType.Z, "qubit": 0, "row": 5},
            {"ty": VertexType.X, "qubit": 0, "row": 6},
            {"ty": VertexType.Z, "qubit": 0, "row": 7},
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 8},
        ],
        edges_data=[
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),      # Z-Z spider fusion candidate
            ((2, 3), EdgeType.HADAMARD),    # Hadamard edge
            ((3, 4), EdgeType.SIMPLE),      # X-X spider fusion candidate
            ((4, 5), EdgeType.HADAMARD),    # Hadamard edge
            ((5, 6), EdgeType.SIMPLE),
            ((6, 7), EdgeType.SIMPLE),
            ((7, 8), EdgeType.SIMPLE),
        ],
        inputs=[0],
        outputs=[8],
    )
    print(g.type(3))

def graph_full_reduce():
    graph = zx.generate.cliffordT(3,20, backend="neo4j")
    zx.simplify.full_reduce(graph)
    #graph.normalise()

#graph_step_by_step()
graph_full_reduce()



    
