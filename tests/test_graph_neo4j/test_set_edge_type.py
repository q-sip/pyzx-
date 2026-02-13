# tests/test_graph_neo4j/test_set_edge_type.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase


class TestSetEdgeType(Neo4jE2ETestCase):
    def test_set_edge_type_HADAMARD(self):
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 1, "qubit": 1},
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0}
        ]
        edges_data=[
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.HADAMARD),
        ((2, 3), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges_data=edges_data)

        g.set_edge_type((0, 1), EdgeType.HADAMARD)
        self.assertEqual(g.edge_type((0, 1)), EdgeType.HADAMARD)

    def test_set_edge_type_SIMPLE(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
        ]


        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        g.set_edge_type((1, 2), EdgeType.SIMPLE)
        self.assertEqual(g.edge_type((1, 2)), EdgeType.SIMPLE)

    def test_edge_type_is_different_after_set_edge_type(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
        ]


        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        initial = g.edge_type((1, 2))
        g.set_edge_type((1, 2), EdgeType.SIMPLE)
        self.assertNotEqual(g.edge_type((1, 2)), initial)

        self.assertNotEqual(False)
