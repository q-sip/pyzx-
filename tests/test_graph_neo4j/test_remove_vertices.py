# tests/test_graph_neo4j/test_remove_vertices.py
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


class TestRemoveVerticesUnit(Neo4jUnitTestCase):
    def test_remove_vertices_unit_updates_inputs_outputs(self):
        g = self.g

        g._inputs = (0, 1, 2, 3)
        g._outputs = (3, 4, 5)

        fake_session = _FakeSession()
        g._get_session = lambda: fake_session

        g.remove_vertices([1, 3])

        self.assertEqual(g._inputs, (0, 2))
        self.assertEqual(g._outputs, (4, 5))

        self.assertEqual(len(fake_session.tx.calls), 1)
        query, params = fake_session.tx.calls[0]
        self.assertIn("DETACH DELETE", query)
        self.assertEqual(params["vertex_ids"], [1, 3])
        self.assertEqual(params["graph_id"], g.graph_id)

    def test_remove_vertices_unit_with_empty_list(self):
        g = self.g
        fake_session = _FakeSession()
        g._get_session = lambda: fake_session

        g.remove_vertices([])

        self.assertEqual(len(fake_session.tx.calls), 0)


class TestRemoveVerticesE2E(Neo4jE2ETestCase):
    def test_remove_vertices_e2e_deletes_nodes_and_edges(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 2, "qubit": 0},
            {"ty": VertexType.Z, "row": 3, "qubit": 0},
            {"ty": VertexType.BOUNDARY, "row": 4, "qubit": 0},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
            ((3, 4), EdgeType.SIMPLE),
        ]

        v_ids = g.create_graph(
            vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[4]
        )

        self.assertEqual(g.num_vertices(), 5)

        g.remove_vertices([v_ids[1], v_ids[2]])

        self.assertEqual(g.num_vertices(), 3)

        with g._get_session() as session:
            result = session.run(
                "MATCH (n:Node {graph_id: $gid}) RETURN collect(n.id) AS ids",
                gid=g.graph_id,
            ).single()
            remaining_ids = result["ids"]

        self.assertIn(v_ids[0], remaining_ids)
        self.assertNotIn(v_ids[1], remaining_ids)
        self.assertNotIn(v_ids[2], remaining_ids)
        self.assertIn(v_ids[3], remaining_ids)
        self.assertIn(v_ids[4], remaining_ids)

    def test_remove_vertices_e2e_removes_connected_edges(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.Z, "row": 0, "qubit": 0},
            {"ty": VertexType.X, "row": 1, "qubit": 0},
            {"ty": VertexType.Z, "row": 2, "qubit": 0},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
        ]

        v_ids = g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        with g._get_session() as session:
            edge_count = session.run(
                "MATCH (:Node {graph_id: $gid})-[r:Wire]->() RETURN count(r) AS c",
                gid=g.graph_id,
            ).single()["c"]
        self.assertEqual(edge_count, 2)

        g.remove_vertices([v_ids[1]])

        with g._get_session() as session:
            edge_count = session.run(
                "MATCH (:Node {graph_id: $gid})-[r:Wire]->() RETURN count(r) AS c",
                gid=g.graph_id,
            ).single()["c"]
        self.assertEqual(edge_count, 0)

    def test_remove_vertices_e2e_updates_inputs_outputs(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.BOUNDARY, "row": 2, "qubit": 0},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
        ]

        v_ids = g.create_graph(
            vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[2]
        )

        self.assertEqual(g._inputs, (v_ids[0],))
        self.assertEqual(g._outputs, (v_ids[2],))

        g.remove_vertices([v_ids[0]])
        self.assertEqual(g._inputs, ())
        self.assertEqual(g._outputs, (v_ids[2],))

        g.remove_vertices([v_ids[2]])
        self.assertEqual(g._outputs, ())
