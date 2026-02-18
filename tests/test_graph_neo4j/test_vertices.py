# tests/test_graph_neo4j/test_vertices.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase


class _FakeSessionVerticesEmpty:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_read(self, fn):
        class _Tx:
            def run(self, q, **params):
                class _Result:
                    def data(self_inner):
                        return []

                return _Result()

        return fn(_Tx())


class TestVerticesUnit(Neo4jUnitTestCase):
    def test_vertices_empty(self):
        g = self.g
        g._get_session = lambda: _FakeSessionVerticesEmpty()
        self.assertEqual(g.vertices(), [])


class TestVerticesE2E(Neo4jUnitTestCase):
    def test_vertices_after_creation(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 0), EdgeType.SIMPLE),
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        # Neo4j query ordering is not guaranteed unless ORDER BY is used.
        self.assertEqual(sorted(g.vertices()), [0, 1, 2])

    def test_vertices_increment(self):
        g = self.g

        initial = len(g.vertices())
        g.create_graph(
            vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[]
        )
        self.assertEqual(len(g.vertices()), initial + 1)
