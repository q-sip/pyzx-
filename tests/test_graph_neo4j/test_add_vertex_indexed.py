# tests/test_graph_neo4j/test_add_vertex_indexed.py
import os
import unittest
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType
from typing_extensions import Literal


class _FakeResult:
    def __init__(self, single_value: Optional[Dict[str, Any]] = None):
        self._single_value: Optional[Dict[str, Any]] = single_value

    def single(self) -> Optional[Dict[str, Any]]:
        return self._single_value


class _FakeTx:
    def __init__(self, exists_count: int = 0):
        self.calls: List[Tuple[str, Dict[str, Any]]] = []
        self.exists_count: int = exists_count

    def run(self, query: str, **params: Any) -> _FakeResult:
        self.calls.append((query, dict(params)))
        # add_vertex_indexed does one read query: "RETURN count(n) AS c"
        if "RETURN count(n) AS c" in query:
            return _FakeResult({"c": self.exists_count})
        return _FakeResult(None)


class _FakeSession:
    def __init__(self, exists_count: int = 0):
        self.tx: _FakeTx = _FakeTx(exists_count=exists_count)

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Literal[False]:
        return False

    def execute_read(self, fn: Callable[[_FakeTx], Any]) -> Any:
        return fn(self.tx)

    def execute_write(self, fn: Callable[[_FakeTx], Any]) -> Any:
        return fn(self.tx)

    # For E2E connectivity smoke-check in other tests; not used in unit tests.
    def run(self, query: str, **params: Any) -> _FakeResult:
        return self.tx.run(query, **params)


def _neo4j_env_present() -> bool:
    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"))


class TestGraphNeo4jAddVertexIndexed(unittest.TestCase):
    def setUp(self) -> None:
        self.graph_id: str = f"test_graph_{uuid.uuid4().hex}"

    def test_add_vertex_indexed_unit_creates_node_with_defaults_and_updates_vindex(
        self,
    ) -> None:
        g = GraphNeo4j(
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession(exists_count=0)
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            self.assertEqual(g.vindex(), 0)

            g.add_vertex_indexed(5)

            # vindex should become v+1 when v >= current vindex
            self.assertEqual(g.vindex(), 6)

            # Should have 2 tx.run calls: existence check + create
            self.assertEqual(len(fake_session.tx.calls), 2)

            # 1) existence query
            q1, p1 = fake_session.tx.calls[0]
            self.assertIn("RETURN count(n) AS c", q1)
            self.assertEqual(p1["graph_id"], g.graph_id)
            self.assertEqual(p1["id"], 5)

            # 2) create query
            q2, p2 = fake_session.tx.calls[1]
            self.assertIn("CREATE", q2)
            self.assertIn(":Node", q2)
            self.assertEqual(p2["graph_id"], g.graph_id)
            self.assertEqual(p2["id"], 5)
            self.assertEqual(p2["t"], VertexType.BOUNDARY.value)
            self.assertEqual(p2["phase"], "0")
            self.assertEqual(p2["qubit"], -1)
            self.assertEqual(p2["row"], -1)
        finally:
            g.close()

    def test_add_vertex_indexed_unit_does_not_update_vindex_if_lower(self) -> None:
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession(exists_count=0)
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            g._vindex = 10
            g.add_vertex_indexed(3)

            # vindex should remain unchanged if v < current vindex
            self.assertEqual(g.vindex(), 10)

            # existence check + create
            self.assertEqual(len(fake_session.tx.calls), 2)
        finally:
            g.close()

    def test_add_vertex_indexed_unit_raises_if_taken(self) -> None:
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession(exists_count=1)  # simulate "id already exists"
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            with self.assertRaises(ValueError):
                g.add_vertex_indexed(2)

            # Only the existence check should run; no create
            self.assertEqual(len(fake_session.tx.calls), 1)
            q1, _ = fake_session.tx.calls[0]
            self.assertIn("RETURN count(n) AS c", q1)
        finally:
            g.close()

    def test_add_vertex_indexed_e2e_creates_node_and_enforces_uniqueness(self) -> None:
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

            self.assertEqual(g.vindex(), 0)

            g.add_vertex_indexed(5)
            self.assertEqual(g.vindex(), 6)

            # Add a smaller index; vindex should not change
            g.add_vertex_indexed(2)
            self.assertEqual(g.vindex(), 6)

            # Adding the same index again should raise
            with self.assertRaises(ValueError):
                g.add_vertex_indexed(5)

            # Verify defaults in DB
            query = """
                MATCH (n:Node {graph_id: $gid})
                RETURN n.id AS id, n.t AS t, n.phase AS phase, n.qubit AS qubit, n.row AS row
                ORDER BY id
            """
            with g._get_session() as session:
                rows = session.run(query, gid=g.graph_id).data()

            self.assertEqual([r["id"] for r in rows], [2, 5])
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
