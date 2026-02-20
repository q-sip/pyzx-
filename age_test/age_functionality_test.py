#Scelaton
from pyzx.graph.graph_AGE import GraphAGE  # or the class name you made
from pyzx.utils import VertexType, EdgeType

# connect to AGE database
g = GraphAGE(
    host="age",
    port=5432,
    database="age_db",
    user="postgres",
    password="salasana",
    graph_id="test_graph"
)

# Add a vertex
v0 = g.add_vertex(VertexType.BOUNDARY, 0, 0)
v1 = g.add_vertex(VertexType.Z, 0, 1)
v2 = g.add_vertex(VertexType.X, 0, 2)

# Add edges
g.add_edge(v0, v1, EdgeType.SIMPLE)
g.add_edge(v1, v2, EdgeType.SIMPLE)

print("Vertices and edges added!")

graph = g.graph_id  # e.g., 'test_graph'

# Fetch vertices
with g.conn.cursor() as cur:
    cur.execute(f"SELECT * FROM cypher('{graph}', $$ MATCH (n) RETURN n $$) AS (n agtype);")
    vertices = cur.fetchall()
    print("Vertices in the graph:")
    for v in vertices:
        print(v[0])

# Fetch edges
with g.conn.cursor() as cur:
    cur.execute(f"SELECT * FROM cypher('{graph}', $$ MATCH ()-[e]->() RETURN e $$) AS (e agtype);")
    edges = cur.fetchall()
    print("\nEdges in the graph:")
    for e in edges:
        print(e[0])