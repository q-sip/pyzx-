# tests/test_graph_neo4j/test_inputs.py
import os
import unittest
import uuid
from typing import Any, Callable, Dict, List, Tuple

from pyzx.graph.graph_neo4j import GraphNeo4j
from typing_extensions import Literal


class _FakeTx:
    def __init__(self, input_rows: List[Dict[str, Any]]):
        self.calls: List[Tuple[str, Dict[str, Any]]] = []
        self._input_rows: List[Dict[str, Any]] = input_rows

    def run(self, query: str, **params: Any) -> Any:
        self.calls.append((query, dict(params)))

        class _R:
            def __init__(self, rows: List[Dict[str, Any]]):
                self._rows = rows

            def data(self) -> List[Dict[str, Any]]:
                return self._rows

        # inputs() reads MATCH (n:Input ...) ... data()
        if "MATCH (n:Input" in query and "RETURN n.id AS id" in query:
            return _R(self._input_rows)

        return _R([])


class _FakeSession:
    def __init__(self, input_rows: List[Dict[str, Any]]):
        self.tx: _FakeTx = _FakeTx(input_rows=input_rows)

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Literal[False]:
        return False

    def execute_read(self, fn: Callable[[_FakeTx], Any]) -> Any:
        return fn(self.tx)

    # For completeness
    def execute_write(self, fn: Callable[[_FakeTx], Any]) -> Any:
        return fn(self.tx)

    def run(self, query: str, **params: Any) -> Any:
        return self.tx.run(query, **params)


def _neo4j_env_present() -> bool:
    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"))


class TestGraphNeo4jInputs(unittest.TestCase):
    def setUp(self) -> None:
        self.graph_id: str = f"test_graph_{uuid.uuid4().hex}"

    def test_inputs_unit_returns_cached_tuple_without_db_read(self) -> None:
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession(input_rows=[{"id": 9}])
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            g._inputs = (0, 3)

            ins = g.inputs()
            self.assertEqual(ins, (0, 3))

            # Should not query DB if cached inputs exist
            self.assertEqual(len(fake_session.tx.calls), 0)
        finally:
            g.close()

    def test_inputs_unit_reads_from_db_when_not_cached_and_caches_result(self) -> None:
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession(input_rows=[{"id": 0}, {"id": 4}])
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            g._inputs = tuple()  # not cached

            ins = g.inputs()
            self.assertEqual(ins, (0, 4))
            self.assertEqual(g._inputs, (0, 4))

            self.assertEqual(len(fake_session.tx.calls), 1)
            q1, p1 = fake_session.tx.calls[0]
            self.assertIn("MATCH (n:Input", q1)
            self.assertIn("RETURN n.id AS id", q1)
            self.assertEqual(p1["graph_id"], g.graph_id)
        finally:
            g.close()

    def test_inputs_e2e_reflects_set_inputs_and_persists_via_labels(self) -> None:
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

            g.add_vertices(5)  # ids 0..4
            g.set_inputs((4, 1))

            # clear cache and force DB read path
            g._inputs = tuple()

            ins = g.inputs()
            self.assertEqual(ins, (1, 4))

            # also check that a fresh Python object reads labels
            g2 = GraphNeo4j(
                uri=os.getenv("NEO4J_URI", ""),
                user=os.getenv("NEO4J_USER", ""),
                password=os.getenv("NEO4J_PASSWORD", ""),
                graph_id=self.graph_id,
                database=os.getenv("NEO4J_DATABASE"),
            )
            try:
                ins2 = g2.inputs()
                self.assertEqual(ins2, (1, 4))
            finally:
                g2.close()
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
