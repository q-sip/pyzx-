# tests/test_graph_neo4j/test_depth.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase


class _FakeRecord(dict):
    pass


class _FakeSessionRead:
    def __init__(self, maxr):
        self._maxr = maxr

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_read(self, fn):
        maxr = self._maxr

        class _Tx:
            def run(self, q, **params):
                class _Result:
                    def single(self_inner):
                        return _FakeRecord({"maxr": maxr})

                return _Result()

        return fn(_Tx())


class TestDepthUnit(Neo4jUnitTestCase):
    def test_depth_unit_returns_max_row(self):
        g = self.g
        g._get_session = lambda: _FakeSessionRead(maxr=7)

        self.assertEqual(g.depth(), 7)
        self.assertEqual(g._maxr, 7)


class TestDepthE2E(Neo4jE2ETestCase):
    def test_depth_e2e_from_created_rows(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "row": -1, "qubit": 0},
            {"ty": VertexType.Z, "row": 0, "qubit": 0, "phase": 0},
            {"ty": VertexType.X, "row": 5, "qubit": 0, "phase": 1},
            {"ty": VertexType.BOUNDARY, "row": 2, "qubit": 0},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
            ((2, 3), EdgeType.SIMPLE),
        ]

        g.create_graph(
            vertices_data=vertices_data, edges_data=edges_data, inputs=[1], outputs=[3]
        )

        self.assertEqual(g.depth(), 5)
