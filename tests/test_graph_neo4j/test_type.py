# tests/test_graph_neo4j/test_type.py
from pyzx.utils import VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase





class TestTypeE2E(Neo4jUnitTestCase):
    def test_type_empty(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])
        with self.assertRaises(KeyError):
            t = g.type(3)

    def test_type_X(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])

        self.assertEqual(g.type(2), 2)

    def test_type_BOUNDARY(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])

        self.assertEqual(g.type(0), 0)
