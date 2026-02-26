# tests/test_graph_neo4j/test_set_outputs.py
import os
import unittest
import uuid
from typing import Any, Callable, Dict, List, Tuple

from pyzx.graph.graph_neo4j import GraphNeo4j
from typing_extensions import Literal


class _FakeTx:
    def __init__(self):
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def run(self, query: str, **params: Any) -> None:
        self.calls.append((query, dict(params)))
        return None


class _FakeSession:
    def __init__(self):
        self.tx: _FakeTx = _FakeTx()

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Literal[False]:
        return False

    def execute_write(self, fn: Callable[[_FakeTx], Any]) -> Any:
        return fn(self.tx)

    # For E2E connectivity smoke-check style; not used in unit tests.
    def run(self, query: str, **params: Any) -> Any:
        return self.tx.run(query, **params)


def _neo4j_env_present() -> bool:
    return all(os.getenv(k) for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"))


class TestGraphNeo4jSetOutputs(unittest.TestCase):
    def setUp(self) -> None:
        self.graph_id: str = f"test_graph_{uuid.uuid4().hex}"

    def test_set_outputs_unit_updates_tuple_and_writes_labels(self) -> None:
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession()
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            self.assertEqual(g._outputs, tuple())

            g.set_outputs((2, 5, 7))

            self.assertEqual(g._outputs, (2, 5, 7))

            # Expect 2 tx.run calls: clear then set
            self.assertEqual(len(fake_session.tx.calls), 2)

            q1, p1 = fake_session.tx.calls[0]
            self.assertIn("REMOVE n:Output", q1)
            self.assertEqual(p1["graph_id"], g.graph_id)

            q2, p2 = fake_session.tx.calls[1]
            self.assertIn("UNWIND $ids AS vid", q2)
            self.assertIn("SET n:Output", q2)
            self.assertEqual(p2["graph_id"], g.graph_id)
            self.assertEqual(p2["ids"], [2, 5, 7])
        finally:
            g.close()

    def test_set_outputs_unit_empty_clears_outputs(self) -> None:
        g = GraphNeo4j(
            uri="bolt://unit-test-does-not-connect",
            user="neo4j",
            password="password",
            graph_id=self.graph_id,
            database=os.getenv("NEO4J_DATABASE"),
        )
        try:
            fake_session = _FakeSession()
            g._get_session = lambda: fake_session  # type: ignore[method-assign]

            g._outputs = (1, 2)

            g.set_outputs(tuple())

            self.assertEqual(g._outputs, tuple())
            self.assertEqual(len(fake_session.tx.calls), 2)

            # still clears then sets with empty ids
            _, p2 = fake_session.tx.calls[1]
            self.assertEqual(p2["ids"], [])
        finally:
            g.close()

    @unittest.skipUnless(
        _neo4j_env_present(),
        "Neo4j env vars missing (NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD).",
    )
    def test_set_outputs_e2e_sets_and_clears_output_labels(self) -> None:
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

            # create some vertices
            g.add_vertices(4)  # ids: 0,1,2,3

            def _get_output_ids() -> List[int]:
                q = """
                    MATCH (n:Output {graph_id: $gid})
                    RETURN n.id AS id
                    ORDER BY id
                """
                with g._get_session() as session:
                    rows = session.run(q, gid=g.graph_id).data()
                return [int(r["id"]) for r in rows]

            g.set_outputs((1, 3))
            self.assertEqual(_get_output_ids(), [1, 3])

            # change outputs; previous labels should be cleared
            g.set_outputs((2,))
            self.assertEqual(_get_output_ids(), [2])

            # clear all outputs
            g.set_outputs(tuple())
            self.assertEqual(_get_output_ids(), [])
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
