# tests/test_graph_neo4j/test_type.py
from pyzx.utils import VertexType, EdgeType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase





class TestEdgeTypeE2E(Neo4jE2ETestCase):
    def test_edge_type_empty(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])
        with self.assertRaises(KeyError):
            t = g.edge_type((1, 2))

    def test_edge_type_SIMPLE(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE)
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        self.assertEqual(g.edge_type((0, 1)), 1)

    def test_type_HADAMARD(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        edges_data = [
            ((1, 2), EdgeType.HADAMARD)
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        self.assertEqual(g.edge_type((1, 2)), 2)
