# tests/test_graph_neo4j/test_vindex.py
from pyzx.utils import VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase


class TestVindexUnit(Neo4jUnitTestCase):
    def test_vindex_empty(self):
        g = self.g
        self.assertEqual(g.vindex(), 0)


class TestVindexE2E(Neo4jE2ETestCase):
    def test_vindex_after_creation(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])

        self.assertEqual(g.vindex(), 3)

    def test_vindex_increment(self):
        g = self.g

        initial = g.vindex()
        g.create_graph(
            vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[]
        )
        self.assertEqual(g.vindex(), initial + 1)
