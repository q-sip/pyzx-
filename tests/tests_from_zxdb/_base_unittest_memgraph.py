# tests/tests_from_zxdb/_base_unittest.py
import os
import unittest
import uuid
from dotenv import load_dotenv
from pyzx.graph.graph_memgraph import GraphMemgraph
load_dotenv()


def _env_present() -> bool:
    return all(os.getenv(k) for k in ("MEMGRAPH_AUTH", "MEMGRAPH_URI"))


class MemgraphUnitTestCase(unittest.TestCase):
    """
    Base class for end-to-end tests: requires reachable Neo4j.
    Creates a unique graph_id per test and cleans up nodes for that graph_id.
    """

    def setUp(self):
        if not _env_present():
            raise unittest.SkipTest(
                "Memgraph env vars missing (MEMGRAPH_AUTH, MEMGRAPH_URI)."
            )

        self.graph_id = f"test_graph_{uuid.uuid4().hex}"

        self.backend_name = "memgraph"
        self.g = GraphMemgraph(
            uri=os.getenv("MEMGRAPH_URI"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database="memgraph",
            graph_id=self.graph_id,
        )

        # sanity-check connection
        try:
            self.g.driver.verify_connectivity()
        except Exception as e:
            try:
                self.g.close()
            finally:
                raise unittest.SkipTest(f"Memgraph not reachable: {e}")


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
