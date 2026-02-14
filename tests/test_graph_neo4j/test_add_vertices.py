# tests/test_graph_neo4j/test_add_vertices.py
import os
import unittest
import uuid

from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType


class _FakeTx:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return None


class _FakeSession:
    def __init__(self):
        self.tx = _FakeTx()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_write(self, fn):
        return fn(self.tx)


def _neo4j_env_present() -> bool:
    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"))


class TestGraphNeo4jAddVertices(unittest.TestCase):
    def setUp(self):
        self.graph_id = f"test_graph_{uuid.uuid4().hex}"

    def test_add_vertices_unit_creates_nodes_and_updates_vindex(self):
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession()
            g._get_session = lambda: fake_session  # patch instance method

            self.assertEqual(g.vindex(), 0)

            vs = g.add_vertices(3)
            self.assertEqual(vs, [0, 1, 2])
            self.assertEqual(g.vindex(), 3)

            self.assertEqual(len(fake_session.tx.calls), 1)
            query, params = fake_session.tx.calls[0]

            self.assertIn("CREATE", query)
            self.assertIn(":Node", query)

            self.assertEqual(params["graph_id"], g.graph_id)

            payload = params["vertices"]
            self.assertEqual([v["id"] for v in payload], [0, 1, 2])
            self.assertTrue(all(v["t"] == VertexType.BOUNDARY.value for v in payload))
            self.assertTrue(all(v["phase"] == "0" for v in payload))
            self.assertTrue(all(v["qubit"] == -1 for v in payload))
            self.assertTrue(all(v["row"] == -1 for v in payload))
        finally:
            g.close()

    def test_add_vertices_unit_zero_is_noop(self):
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession()
            g._get_session = lambda: fake_session

            vs = g.add_vertices(0)
            self.assertEqual(vs, [])
            self.assertEqual(g.vindex(), 0)
            self.assertEqual(len(fake_session.tx.calls), 0)
        finally:
            g.close()

    def test_add_vertices_e2e_creates_nodes_with_defaults(self):
        g = GraphNeo4j(
            uri=os.getenv("NEO4J_URI", ""),
            user=os.getenv("NEO4J_USER", ""),
            password=os.getenv("NEO4J_PASSWORD", ""),
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            # connectivity check; skip instead of failing hard
            try:
                with g._get_session() as session:
                    session.run("RETURN 1").single()
            except Exception as e:
                raise unittest.SkipTest(f"Neo4j not reachable: {e}")

            vs = g.add_vertices(4)
            self.assertEqual(vs, [0, 1, 2, 3])
            self.assertEqual(g.num_vertices(), 4)

            query = """
                MATCH (n:Node {graph_id: $gid})
                RETURN n.id AS id, n.t AS t, n.phase AS phase, n.qubit AS qubit, n.row AS row
                ORDER BY id
            """
            with g._get_session() as session:
                rows = session.run(query, gid=g.graph_id).data()

            self.assertEqual([r["id"] for r in rows], [0, 1, 2, 3])
            self.assertTrue(all(r["t"] == VertexType.BOUNDARY.value for r in rows))
            self.assertTrue(all(r["phase"] == "0" for r in rows))
            self.assertTrue(all(r["qubit"] == -1 for r in rows))
            self.assertTrue(all(r["row"] == -1 for r in rows))
        finally:
            # cleanup
            try:
                with g._get_session() as session:
                    session.execute_write(
                        lambda tx: tx.run(
                            "MATCH (n:Node {graph_id: $gid}) DETACH DELETE n",
                            gid=g.graph_id,
                        )
                    )
            finally:
                g.close()


if __name__ == "__main__":
    unittest.main()
