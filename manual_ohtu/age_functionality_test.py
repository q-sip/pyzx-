#Scelaton
from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType, EdgeType

# connect to AGE database
g = GraphAGE()
 
print("Successfully connected to AGE database")

# Add a vertex
#try:
#    v0 = g.add_vertex(VertexType.BOUNDARY, 0, 0)
#    v1 = g.add_vertex(VertexType.Z, 0, 1)
#    v2 = g.add_vertex(VertexType.X, 0, 2)
##    print("Vertices created successfully")
#except Exception as e:
#    print(f"Error creating vertices: {type(e).__name__}: {e}")
#    v0 = v1 = v2 = None

# Add edges
#try:
#    if v0 and v1 and v2:
#        g.add_edge(v0, v1, EdgeType.SIMPLE)
#        g.add_edge(v1, v2, EdgeType.SIMPLE)
#        print("Vertices and edges added!")
#except Exception as e:
#    print(f"Error adding edges: {type(e).__name__}: {e}")

#graph = g.graph_id  # e.g., 'test_graph'

# Fetch vertices
##try:
#    with g.conn.cursor() as cur:
#        cur.execute(f"SELECT * FROM cypher('{graph}', $$ MATCH (n) RETURN n $$) AS (n agtype);")
#        vertices = cur.fetchall()
#        print("Vertices in the graph:")
#        for v in vertices:
#            print(v[0])
#except Exception as e:
#    print(f"Error fetching vertices: {type(e).__name__}: {e}")

# Fetch edges
#try:
#    with g.conn.cursor() as cur:
#        cur.execute(f"SELECT * FROM cypher('{graph}', $$ MATCH ()-[e]->() RETURN e $$) AS (e agtype);")
#        edges = cur.fetchall()
#        print("\nEdges in the graph:")
#        for e in edges:
#            print(e[0])
#except Exception as e:
#    print(f"Error fetching edges: {type(e).__name__}: {e}")

# Minimal Cypher smoke test to verify AGE functionality
try:
    with g.conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM ag_catalog.cypher('{g.graph_id}', $$ "
            "CREATE (n:Smoke {k: 1}) RETURN n $$) AS (n ag_catalog.agtype);"
        )
        created = cur.fetchone()
        cur.execute(
            f"SELECT * FROM ag_catalog.cypher('{g.graph_id}', $$ "
            "MATCH (n:Smoke {k: 1}) RETURN n $$) AS (n ag_catalog.agtype);"
        )
        matched = cur.fetchall()
        g.conn.commit()
    print("\nCypher smoke test:")
    print(f"Created: {created[0] if created else None}")
    print(f"Matched count: {len(matched)}")
except Exception as e:
    print(f"Cypher smoke test failed: {type(e).__name__}: {e}")
    g.conn.rollback()

print("\nTest completed!")