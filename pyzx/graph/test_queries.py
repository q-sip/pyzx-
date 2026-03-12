from dotenv import load_dotenv
load_dotenv(".env.pyzx")
load_dotenv(".env.neo4j")
from pyzx.graph import Graph
from pyzx.utils import VertexType, EdgeType

g = Graph(backend="neo4j")


     # Add vertices (returns vertex IDs)
v0 = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)   # input
v1 = g.add_vertex(VertexType.Z, qubit=0, row=1, phase=0)
v2 = g.add_vertex(VertexType.Z, qubit=0, row=2, phase=0)
v3 = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)   # output

# Add edges: (from_id, to_id), optional EdgeType (default SIMPLE)
g.add_edge((v0, v1), EdgeType.SIMPLE)
g.add_edge((v1, v2), EdgeType.HADAMARD)
g.add_edge((v2, v3), EdgeType.SIMPLE)

# Mark inputs and outputs (by vertex ID)
g.set_inputs((v0,))
g.set_outputs((v3,))