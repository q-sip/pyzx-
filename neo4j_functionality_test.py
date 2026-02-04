import os
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from pyzx.symbolic import Poly
from fractions import Fraction
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pyzx.simplify import full_reduce
from pyzx.generate import cliffordT
from pyzx.drawing import draw

load_dotenv()


URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()


g = GraphNeo4j(
    uri=URI,
    user=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    database="neo4j",
    graph_id="test_graph",
)

# Älkää välittäkö näistä, helpotusta varten väsäsin että pysyy perässä sen graafin kanssa
# query =""" MATCH (N) DETACH DELETE N"""
# g.clear_graph(query)

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

def manually_construc_diagram():
    g = GraphNeo4j
    i = g.add_vertex(0,0,0)
    v = g.add_vertex(1,0,1, Fraction(1,2))
    w = g.add_vertex(2,0,2, Fraction(-1,2))
    o = g.add_vertex(0,0,3)
    g.add_edges([(i,v), (v,w),(w,o)])
    #display(draw(g)) -> Neo4j call


def generate_and_simplify_circuit():
    g=cliffordT(3,20)
    #display(draw(g)) -> Neo4j call
    full_reduce(g)
    #g.normalise()
    draw(g)

# For planning only
#full_reduce(g: BaseGraph[VT,ET], matchf: Optional[Callable[[Union[VT, ET]],bool]]=None, quiet:bool=True, stats:Optional[Stats]=None) -> None:
