# tests/test_graph_neo4j/conftest.py
import os
import uuid
from dotenv import load_dotenv
from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase
from pyzx.graph.graph_neo4j import GraphNeo4j


class ConfigurationTest(Neo4jUnitTestCase):
    def _neo4j_env_present(self):
        self.assertEqual(all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")), True)

class Neo4j_graph_e2e(Neo4jUnitTestCase):

    def __init__(self):
        self.unique_graph_id = f"test_graph_{uuid.uuid4().hex}"
        self.g = GraphNeo4j(
            uri=os.getenv("NEO4J_URI", ""),
            user=os.getenv("NEO4J_USER", ""),
            password=os.getenv("NEO4J_PASSWORD", ""),
            graph_id=self.unique_graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )

    def sanityCheckConn(self):
        # sanity-check connection
        with self.g._get_session() as session:
            self.assertEqual(session.run("RETURN 1").single(), 1)

    def _cleanup(self):
        # cleanup
        with self.g._get_session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    "MATCH (n:Node {graph_id: $gid}) DETACH DELETE n",
                    gid=self.g.graph_id,
                )
            )

        self.g.close()
