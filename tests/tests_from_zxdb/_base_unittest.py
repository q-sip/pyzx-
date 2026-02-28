# tests/tests_from_zxdb/_base_unittest.py
import os
import unittest
import uuid
from dotenv import load_dotenv
from pyzx.graph.graph_neo4j import GraphNeo4j
load_dotenv()


def _neo4j_env_present() -> bool:
    return all(os.getenv(k) for k in ("DB_URI", "DB_USER", "DB_PASSWORD"))


def _ensure_phase_to_str_exists() -> None:
    # Safety patch for older forks/branches.
    if not hasattr(GraphNeo4j, "_phase_to_str"):

        def _phase_to_str(_, phase):
            return "0" if phase is None else str(phase)

        setattr(GraphNeo4j, "_phase_to_str", _phase_to_str)

class Neo4jUnitTestCase(unittest.TestCase):
    """
    Base class for end-to-end tests: requires reachable Neo4j.
    Creates a unique graph_id per test and cleans up nodes for that graph_id.
    """

    def setUp(self):
        _ensure_phase_to_str_exists()


        if not _neo4j_env_present():
            raise unittest.SkipTest(
                "Neo4j env vars missing (NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD)."
            )

        self.graph_id = f"test_graph_{uuid.uuid4().hex}"

        self.backend_name = "neo4j"
        self.g = GraphNeo4j(
            uri=os.getenv("DB_URI", ""),
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )

        # sanity-check connection
        try:
            self.g.driver.verify_connectivity()
        except Exception as e:
            try:
                self.g.close()
            finally:
                raise unittest.SkipTest(f"Neo4j not reachable: {e}")


    def tearDown(self):
        try:
            with self.g._get_session() as session:
                session.run(
                    "MATCH (n) DETACH DELETE n"
                )
        except Exception:
            pass

        try:
            self.g.close()
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
