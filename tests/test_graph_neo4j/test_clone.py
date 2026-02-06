from types import SimpleNamespace
from unittest.mock import patch

from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase


class _FakeTx:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return None


class _FakeSession:
    """Minimal fake Neo4j session for unit-testing clone().

    It supports:
      - context manager protocol
      - execute_read(tx_fn) where tx.run(...).data() is used
      - execute_write(tx_fn) where tx.run(...) is used
    """

    def __init__(self, *, nodes_rows, edges_rows):
        self.tx = _FakeTx()
        self._nodes_rows = nodes_rows
        self._edges_rows = edges_rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_write(self, fn):
        return fn(self.tx)

    def execute_read(self, fn):
        class _Tx:
            def __init__(self, nodes_rows, edges_rows):
                self._nodes_rows = nodes_rows
                self._edges_rows = edges_rows

            def run(self, query, **params):
                q = query or ""

                class _Result:
                    def __init__(self, rows):
                        self._rows = rows

                    def data(self):
                        return self._rows

                if "properties(n)" in q and "labels(n)" in q:
                    return _Result(self._nodes_rows)
                # The edge snapshot query in GraphNeo4j.clone() is directed:
                #   MATCH (...) -[r:Wire]-> (...) RETURN ... properties(r)
                if "properties(r)" in q and "-[r:Wire]" in q:
                    return _Result(self._edges_rows)
                return _Result([])

        return fn(_Tx(self._nodes_rows, self._edges_rows))


class TestCloneUnit(Neo4jUnitTestCase):
    def test_clone_unit_copies_nodes_edges_labels_and_state(self):
        g = self.g

        # Source in-memory IO ordering is preserved if present.
        g._inputs = (0,)
        g._outputs = (2,)
        g._vindex = 3
        g.scalar.power2 = 7

        nodes_rows = [
            {
                "id": 0,
                "props": {
                    "graph_id": g.graph_id,
                    "id": 0,
                    "t": VertexType.BOUNDARY.value,
                    "phase": "0",
                    "qubit": 0,
                    "row": 0,
                    "extra": "v0",
                },
                "labels": ["Node", "Input"],
            },
            {
                "id": 1,
                "props": {
                    "graph_id": g.graph_id,
                    "id": 1,
                    "t": VertexType.Z.value,
                    "phase": "1/2",
                    "qubit": 0,
                    "row": 1,
                    "extra": "v1",
                },
                "labels": ["Node"],
            },
            {
                "id": 2,
                "props": {
                    "graph_id": g.graph_id,
                    "id": 2,
                    "t": VertexType.BOUNDARY.value,
                    "phase": "0",
                    "qubit": 0,
                    "row": 2,
                    "extra": "v2",
                },
                "labels": ["Node", "Output"],
            },
        ]
        edges_rows = [
            {
                "s": 0,
                "t": 1,
                "props": {"t": EdgeType.SIMPLE.value, "id": 10, "extra": "e01"},
            },
            {
                "s": 1,
                "t": 2,
                "props": {"t": EdgeType.HADAMARD.value, "id": 11, "extra": "e12"},
            },
        ]

        fake_session = _FakeSession(nodes_rows=nodes_rows, edges_rows=edges_rows)
        g._get_session = lambda: fake_session

        with patch("uuid.uuid4", return_value=SimpleNamespace(hex="deadbeef")):
            cpy = g.clone()

        self.assertNotEqual(cpy.graph_id, g.graph_id)
        self.assertEqual(cpy.graph_id, f"{g.graph_id}_clone_deadbeef")
        self.assertEqual(cpy._vindex, 3)
        self.assertEqual(cpy._inputs, (0,))
        self.assertEqual(cpy._outputs, (2,))

        # Scalar must be copied, not aliased.
        self.assertEqual(cpy.scalar, g.scalar)
        self.assertIsNot(cpy.scalar, g.scalar)

        # Ensure writes were issued for nodes, edges, and IO labels.
        self.assertGreaterEqual(len(fake_session.tx.calls), 1)
        combined = "\n".join(q for (q, _) in fake_session.tx.calls)
        self.assertIn("CREATE (n:Node)", combined)
        self.assertIn("CREATE (s)-[r:Wire]->(t)", combined)
        self.assertIn("SET n:Input", combined)
        self.assertIn("SET n:Output", combined)

        # Check that the created nodes payload was rewritten to the new graph_id.
        create_nodes_params = None
        for q, params in fake_session.tx.calls:
            if "UNWIND $nodes AS p" in (q or ""):
                create_nodes_params = params
                break

        self.assertIsNotNone(create_nodes_params)
        self.assertIn("nodes", create_nodes_params)
        self.assertEqual(create_nodes_params["nodes"][0]["graph_id"], cpy.graph_id)
        self.assertEqual(create_nodes_params["nodes"][0]["extra"], "v0")


class TestCloneE2E(Neo4jE2ETestCase):
    def test_clone_e2e_duplicates_graph_without_relabeling(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0, "phase": 0},
            {"ty": VertexType.X, "row": 2, "qubit": 0, "phase": 1},
            {"ty": VertexType.BOUNDARY, "row": 3, "qubit": 0},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
        ]

        g.create_graph(
            vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[3]
        )

        # Add custom properties to ensure clone preserves arbitrary vdata/edata.
        g.set_vdata(2, "tag", "hello")
        g.set_edata((1, 2), "weight", 42)

        cpy = g.clone()
        self.assertNotEqual(cpy.graph_id, g.graph_id)
        self.assertEqual(cpy._inputs, g._inputs)
        self.assertEqual(cpy._outputs, g._outputs)

        with g._get_session() as session:
            n1 = session.run(
                "MATCH (n:Node {graph_id: $gid}) RETURN count(n) AS c",
                gid=g.graph_id,
            ).single()["c"]
            n2 = session.run(
                "MATCH (n:Node {graph_id: $gid}) RETURN count(n) AS c",
                gid=cpy.graph_id,
            ).single()["c"]
            self.assertEqual(n1, n2)

            e1 = session.run(
                "MATCH (:Node {graph_id: $gid})-[r:Wire]->(:Node {graph_id: $gid}) RETURN count(r) AS c",
                gid=g.graph_id,
            ).single()["c"]
            e2 = session.run(
                "MATCH (:Node {graph_id: $gid})-[r:Wire]->(:Node {graph_id: $gid}) RETURN count(r) AS c",
                gid=cpy.graph_id,
            ).single()["c"]
            self.assertEqual(e1, e2)

            ids1 = session.run(
                "MATCH (n:Node {graph_id: $gid}) RETURN n.id AS id ORDER BY id",
                gid=g.graph_id,
            ).data()
            ids2 = session.run(
                "MATCH (n:Node {graph_id: $gid}) RETURN n.id AS id ORDER BY id",
                gid=cpy.graph_id,
            ).data()
            self.assertEqual([r["id"] for r in ids1], [r["id"] for r in ids2])

            # Check that custom vertex property survived.
            tag1 = session.run(
                "MATCH (n:Node {graph_id: $gid, id: 2}) RETURN n.tag AS tag",
                gid=g.graph_id,
            ).single()["tag"]
            tag2 = session.run(
                "MATCH (n:Node {graph_id: $gid, id: 2}) RETURN n.tag AS tag",
                gid=cpy.graph_id,
            ).single()["tag"]
            self.assertEqual(tag1, tag2)

            # Check that custom edge property survived for the directed wire (1)->(2).
            w1 = session.run(
                "MATCH (a:Node {graph_id: $gid, id: 1})-[r:Wire]->(b:Node {graph_id: $gid, id: 2}) RETURN r.weight AS w",
                gid=g.graph_id,
            ).single()["w"]
            w2 = session.run(
                "MATCH (a:Node {graph_id: $gid, id: 1})-[r:Wire]->(b:Node {graph_id: $gid, id: 2}) RETURN r.weight AS w",
                gid=cpy.graph_id,
            ).single()["w"]
            self.assertEqual(w1, w2)

            in1 = session.run(
                "MATCH (n:Node:Input {graph_id: $gid}) RETURN count(n) AS c",
                gid=g.graph_id,
            ).single()["c"]
            in2 = session.run(
                "MATCH (n:Node:Input {graph_id: $gid}) RETURN count(n) AS c",
                gid=cpy.graph_id,
            ).single()["c"]
            self.assertEqual(in1, in2)

            out1 = session.run(
                "MATCH (n:Node:Output {graph_id: $gid}) RETURN count(n) AS c",
                gid=g.graph_id,
            ).single()["c"]
            out2 = session.run(
                "MATCH (n:Node:Output {graph_id: $gid}) RETURN count(n) AS c",
                gid=cpy.graph_id,
            ).single()["c"]
            self.assertEqual(out1, out2)
