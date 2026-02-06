# tests/test_graph_neo4j/test_create_graph.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase


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

    def execute_read(self, fn):
        class _Tx:
            def run(self, query, **params):
                class _Result:
                    def single(self):
                        return {"count": 0}

                return _Result()

        return fn(_Tx())


class TestCreateGraphUnit(Neo4jUnitTestCase):
    def test_create_graph_unit_updates_indices_and_marks_inputs_outputs(self):
        g = self.g
        fake_session = _FakeSession()
        g._get_session = lambda: fake_session

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 3, "qubit": 0, "phase": 0},
            {"ty": VertexType.X, "row": 2, "qubit": 1, "phase": 1},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
        ]

        v = g.create_graph(
            vertices_data=vertices_data,
            edges_data=edges_data,
            inputs=[0],
            outputs=[2],
        )

        self.assertEqual(v, [0, 1, 2])
        self.assertEqual(g._vindex, 3)
        self.assertEqual(g._inputs, (0,))
        self.assertEqual(g._outputs, (2,))

        self.assertGreaterEqual(len(fake_session.tx.calls), 1)
        combined = "\n".join(q for (q, _) in fake_session.tx.calls)
        self.assertIn("CREATE", combined)
        self.assertIn(":Node", combined)


class TestCreateGraphE2E(Neo4jE2ETestCase):
    def test_create_graph_e2e_creates_nodes_edges_and_labels(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0, "phase": 0},
            {"ty": VertexType.X, "row": 2, "qubit": 0, "phase": 1},
            {"ty": VertexType.BOUNDARY, "row": 3, "qubit": 0},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
            ((2, 3), EdgeType.SIMPLE),
        ]

        g.create_graph(
            vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[3]
        )

        with g._get_session() as session:
            n = session.run(
                "MATCH (n:Node {graph_id: $gid}) RETURN count(n) AS c",
                gid=g.graph_id,
            ).single()["c"]
            self.assertEqual(n, 4)

            e = session.run(
                "MATCH (:Node {graph_id: $gid})-[r:Wire]->(:Node {graph_id: $gid}) RETURN count(r) AS c",
                gid=g.graph_id,
            ).single()["c"]
            self.assertEqual(e, 3)

            in_count = session.run(
                "MATCH (n:Node:Input {graph_id: $gid}) RETURN count(n) AS c",
                gid=g.graph_id,
            ).single()["c"]
            self.assertEqual(in_count, 1)

            out_count = session.run(
                "MATCH (n:Node:Output {graph_id: $gid}) RETURN count(n) AS c",
                gid=g.graph_id,
            ).single()["c"]
            self.assertEqual(out_count, 1)
