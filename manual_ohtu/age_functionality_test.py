#Scelaton
from pyzx.graph.graph_AGE import GraphAGE

from pyzx.utils import VertexType, EdgeType
#from tests.test_graph_age import test_add_vertices
import networkx as nx
import matplotlib.pyplot as plt
from fractions import Fraction

# connect to AGE database
g = GraphAGE()
 
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

g.add_vertices(3)
print("vertices added")
g.delete_graph()

g = GraphAGE()
i = None
v = None
w = None
o = None

def manually_constructing():
    i = g.add_vertex(0,0,0)
    v = g.add_vertex(1,0,1, Fraction(1,2))
    w = g.add_vertex(2,0,2, Fraction(-1,2))
    o = g.add_vertex(0,0,3)
    g.add_edges([(i,v),(v,w),(w,o)])
    print(v, w)

def _create_edge(v0, v1):
        """Helper to create an edge between two vertices."""
        g.db_execute(
            f"""
            SELECT * FROM ag_catalog.cypher('{g.graph_id}', $$
                MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
                CREATE (a)-[:Wire]->(b)
                RETURN count(*)
            $$) AS (result agtype);
            """
        )

def use_add_vertices():
    i, v, w = g.add_vertices(3)
    _create_edge(i, v)
    _create_edge(v, w)
    return [i, v, w]

def plt_graph(G):
    G_nx = nx_from_age(G)
    plt.figure()
    pos = nx.spring_layout(G_nx)
    nx.draw(G_nx, pos, with_labels=True, node_color='skyblue', node_size=600, font_size=12, edge_color='gray')
    plt.savefig(os.path.abspath("AGE_graphs/graph.png"))
    print("Graph saved to folder pyzx/AGE_graphs.")

def nx_from_age(g):
    G_nx = nx.Graph()
    for v in g.vertices():    # call the method
        G_nx.add_node(v)
    for u, v in g.edges():    # call the method
        G_nx.add_edge(u, v)
    return G_nx
    
##plt_graph(g)

def fetch_graph():
    query = f"""
    SELECT * FROM cypher('{g.graph_id}', $$
        MATCH (n)-[r]->(m)
        RETURN n, r, m
    $$) AS (n agtype, r agtype, m agtype);
    """
    graph = g._fetchall(query)
    i = 1
    for row in graph:
        print("row", i)
        for item in row:
            print(item)
        i+=1
def fetch_graph2(g):
    query = f"""
    SELECT *
    FROM cypher('{g.graph_id}', $$
        MATCH (n)-[r]->(m)
        RETURN
            id(n) AS n_id,
            n AS n,
            id(r) AS r_id,
            r AS r,
            id(m) AS m_id,
            m AS m
    $$) AS (
        n_id agtype,
        n agtype,
        r_id agtype,
        r agtype,
        m_id agtype,
        m agtype
    );
    """
    rows = g._fetchall(query)

    graph_data = {
        "graph_id": g.graph_id,
        "nodes": {},
        "edges": []
    }

    for row in rows:
        n_id, n, r_id, r, m_id, m = row

        # Store nodes uniquely
        graph_data["nodes"][n_id] = n
        graph_data["nodes"][m_id] = m

        # Store edge
        graph_data["edges"].append({
            "id": r_id,
            "source": n_id,
            "target": m_id,
            "data": r
        })

    return graph_data

def fetch_graph3(g):
    # Fetch all nodes (including isolated ones)
    node_query = f"""
    SELECT *
    FROM cypher('{g.graph_id}', $$
        MATCH (n)
        RETURN id(n) AS n_id, n
    $$) AS (
        n_id agtype,
        n agtype
    );
    """
    # Fetch all edges
    edge_query = f"""
    SELECT *
    FROM cypher('{g.graph_id}', $$
        MATCH (n)-[r]->(m)
        RETURN
            id(r) AS r_id,
            id(n) AS source,
            id(m) AS target,
            r
    $$) AS (
        r_id agtype,
        source agtype,
        target agtype,
        r agtype
    );
    """
    node_rows = g._fetchall(node_query)
    edge_rows = g._fetchall(edge_query)

    graph_data = {
        "graph_id": g.graph_id,
        "nodes": {},
        "edges": []
    }
    # Process nodes (includes nodes created via UNWIND/CREATE)
    for n_id, n in node_rows:
        graph_data["nodes"][n_id] = n

    # Process edges
    for r_id, source, target, r in edge_rows:
        graph_data["edges"].append({
            "id": r_id,
            "source": source,
            "target": target,
            "data": r
        })

    return graph_data

#manually_constructing()
nodes = use_add_vertices()
i = nodes[0]
v = nodes[1]
w = nodes [2]

graph_data = fetch_graph3(g)

print(graph_data)
print(v, w)
g.remove_edges([(v, w)])
new_graph_data = fetch_graph3(g)

print(new_graph_data)

g.delete_graph()