# tests/test_graph_neo4j/_base_unittest.py
import os
import unittest
import uuid

from pyzx.graph.graph_neo4j import GraphNeo4j


def _neo4j_env_present() -> bool:
    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"))


def _ensure_phase_to_str_exists() -> None:
    # Safety patch for older forks/branches.
    if not hasattr(GraphNeo4j, "_phase_to_str"):

        def _phase_to_str(self, phase):
            return "0" if phase is None else str(phase)

        setattr(GraphNeo4j, "_phase_to_str", _phase_to_str)


class Neo4jUnitTestCase(unittest.TestCase):
    """
    Base class for unit tests: creates a GraphNeo4j instance that should never
    actually connect. Tests must patch g._get_session per-test.
    """

    def setUp(self):
        _ensure_phase_to_str_exists()
        self.graph_id = f"test_graph_{uuid.uuid4().hex}"
        self.g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )

    def tearDown(self):
        try:
            self.g.close()
        except Exception:
            pass


class Neo4jE2ETestCase(unittest.TestCase):
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
        self.g = GraphNeo4j(
            uri=os.getenv("NEO4J_URI", ""),
            user=os.getenv("NEO4J_USER", ""),
            password=os.getenv("NEO4J_PASSWORD", ""),
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )

        # sanity-check connection
        try:
            with self.g._get_session() as session:
                session.run("RETURN 1").single()
        except Exception as e:
            try:
                self.g.close()
            finally:
                raise unittest.SkipTest(f"Neo4j not reachable: {e}")

    def tearDown(self):
        # cleanup graph data for this graph_id
        try:
            with self.g._get_session() as session:
                session.execute_write(
                    lambda tx: tx.run(
                        "MATCH (n:Node {graph_id: $gid}) DETACH DELETE n",
                        gid=self.g.graph_id,
                    )
                )
        except Exception:
            pass

        try:
            self.g.close()
        except Exception:
            pass
