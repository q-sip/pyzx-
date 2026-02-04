import os
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from pyzx.symbolic import Poly
from fractions import Fraction
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pyzx.simplify import full_reduce

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
# For planning only
#full_reduce(g: BaseGraph[VT,ET], matchf: Optional[Callable[[Union[VT, ET]],bool]]=None, quiet:bool=True, stats:Optional[Stats]=None) -> None:
