#Scelaton
from pyzx.graph.graph_AGE import GraphAGE

from pyzx.utils import VertexType, EdgeType
from tests.test_graph_age import test_add_vertices
import networkx as nx
import matplotlib.pyplot as plt
from fractions import Fraction

# connect to AGE database
<<<<<<< HEAD
g = GraphAGE()

=======

 
>>>>>>> dev
print("Successfully connected to AGE database")

# Minimal Cypher smoke test to verify AGE functionality
def is_there_smoke():
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

    print("\nYes there is SMOKE")

def delete_graph():
    with g.conn.cursor() as cur:
        cur.execute("LOAD 'age';")
        cur.execute("SET search_path = ag_catalog, public;")
        cur.execute(
            "SELECT drop_graph(%s, %s);",
            (g.graph_id, True)
        )
    g.conn.commit()

    print("\nGraph deleted")

#is_there_smoke()
<<<<<<< HEAD
g.add_vertices(3)
print("vertices added")
g.delete_graph()
=======
g = GraphAGE()
#vertices = g.add_vertices(3)
def manually_constructing():
    i = g.add_vertex(0,0,0)
    v = g.add_vertex(1,0,1, Fraction(1,2))
    w = g.add_vertex(2,0,2, Fraction(-1,2))
    o = g.add_verte(0,0,3)
    g.add_edges([(i,v), (v,w),(w,o)])


g.delete_graph()
>>>>>>> dev
