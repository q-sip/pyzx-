from dotenv import load_dotenv

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.graph.graph_memgraph import GraphMemgraph
from pyzx.graph.graph_neo4j import GraphNeo4j

load_dotenv()

koira = input("what?")

if koira == "1":
    # # Mem
    g = GraphMemgraph()
    kala = g.verify_db_connection()
    print(kala)

elif koira == "2":
    # Age
    g2 = GraphAGE()
    kala2 = g2.verify_db_connection()
    print(kala2)

elif koira == "3":
    # # Neo4j
    g3 = GraphNeo4j()
    kala3 = g3.verify_db_connection()
    print(kala3)