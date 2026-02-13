import os
from fractions import Fraction
from dotenv import load_dotenv
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.graph.graph_s import GraphS
from pyzx.utils import VertexType, EdgeType
import pyzx as zx
import random

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

def graph_step_by_step():
    """Testaa graafin luomista askel askeleelta"""
    i = g.add_vertex(0,0,0)
    v = g.add_vertex(1,0,1, Fraction(1,2))
    w = g.add_vertex(2,0,2, Fraction(-1,2))
    o = g.add_vertex(0,0,3)
    g.add_edges([(i,v), (v,w), (w,o)])

def large_graph():
    """Suurempi graafi"""
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
    # print(g.type(3))

# def graph_full_reduce():
#     """Neo4j graafin full reduce"""
#     graph = zx.generate.cliffordT(3,20, backend="neo4j")
#     zx.simplify.full_reduce(graph)
#     #graph.normalise()

# #graph_step_by_step()
# graph_full_reduce()

def iterable_graph_creation():
    num = 0
    choices = [VertexType.X, VertexType.Z]
    while True:
        g.add_vertex(VertexType.BOUNDARY, 0, 0)
        g.add_vertex(VertexType.BOUNDARY, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.X, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.X, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        g.add_vertex(VertexType.Z, 0, 0)
        for e in [(0, 2), (2, 3), (3, 4), (4, 1)]:
            g.add_edge(e)
        for x in range(num):
            g.add_vertex(random.choice(choices), 0, 0)
            g.add_vertex(random.choice(choices), 0, 0)
            g.add_edge((random.randint(2, g.num_vertices()-1), random.randint(2, g.num_vertices()-1)))
        zx.full_reduce(g)
        print(f'{num} succesful')
        num += 1


print(sorted([100, 101, 65, 102, 103, 30, 104, 105, 106, 107, 31, 108, 109, 110, 111, 112, 84, 113, 85, 114, 115, 116, 117, 118, 41, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 79, 148, 149, 86, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 87, 163, 164, 165, 29, 166, 76, 88, 89, 167, 168, 169, 77, 81, 61, 82, 170, 95, 171, 60, 172, 173, 96, 174, 175, 176, 69, 90, 48, 91, 97, 99, 92, 32, 62, 98, 177, 93, 83, 39, 36, 178, 74, 0, 1, 2, 94, 3, 44, 57, 55, 35, 4, 5, 45, 40, 28, 46, 42, 6, 7, 8, 9, 64, 10, 11, 37, 43, 73, 56, 12, 13, 66, 14, 15, 38, 16, 80, 17, 67, 51, 18, 50, 59, 47, 34, 68, 19, 78, 20, 21, 71, 54, 22, 49, 23, 24, 25, 72, 33, 70, 52, 26, 58, 75, 27, 63, 53]))
