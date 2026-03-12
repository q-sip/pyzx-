# tests/test_graph_neo4j/test_num_edges_increment.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase


class _FakeSessionEdgesCount:
    def __init__(self, count):
        self._count = count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_read(self, fn):
        count = self._count

        class _Tx:
            def run(self, q, **params):
                class _Result:
                    def single(self_inner):
                        return {"count": count}

                return _Result()

        return fn(_Tx())


class TestNumEdgesUnit(Neo4jUnitTestCase):
    def test_num_edges_empty_returns_0(self):
        g = self.g
        g._get_session = lambda: _FakeSessionEdgesCount(count=0)
        self.assertEqual(g.num_edges(), 0)


class TestNumEdgesE2E(Neo4jUnitTestCase):
    def test_num_edges_increases_after_creation(self):
        g = self.g

        before = g.num_edges()

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

        after = g.num_edges()
        self.assertEqual(after, before + 3)

    def test_num_edges_increment(self):
        g = self.g

        before = g.num_edges()

        g.create_graph(
            vertices_data=[
                {"ty": VertexType.Z, "qubit": 0, "row": 1},
                {"ty": VertexType.X, "qubit": 0, "row": 2},
            ],
            edges_data=[((0, 1), EdgeType.HADAMARD)],
        )

        after = g.num_edges()
        self.assertEqual(after, before + 1)
