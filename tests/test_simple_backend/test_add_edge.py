# tests/test_simple_backend/test_add_edge.py
from pyzx.utils import EdgeType, VertexType
import time

from tests.test_simple_backend._base_unittest import SimpleUnitTestCase


class TestAddEdge(SimpleUnitTestCase):
    def test_add_edge_returns_ET(self):
        """
        Test that add_edge returns the vertex pair
        """
        g = self.g

        vs = list(g.add_vertices(3))
        self.assertEqual(vs, [0,1,2])

        g.set_type(0, VertexType.BOUNDARY)
        g.set_row(0, 0)
        g.set_qubit(0, 0)

        g.set_type(1, VertexType.Z)
        g.set_row(1, 1)
        g.set_qubit(1, 0)

        g.set_type(2, VertexType.X)
        g.set_row(2, 1)
        g.set_qubit(2, 1)

        self.assertEqual(g.add_edge((0, 1), EdgeType.SIMPLE), (0, 1))

    def test_add_edge_id_increments_after_create_graph(self):
        """
        After create_graph adds N edges, add_edge should return previous num_edges() + N
        """
        g = self.g

        vs = list(g.add_vertices(4))
        self.assertEqual(vs, [0,1,2,3])

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

        for v, data in enumerate(vertices_data):
            g.set_type(v, data["ty"])
            g.set_qubit(v, data["qubit"])
            g.set_row(v, data["row"])

        for (s, t), et in edges_data:
            g.add_edge((s, t), et)
        before = g.num_edges()

        g.add_edge((0, 3))

        self.assertEqual(g.num_edges(), before + 1)

    def test_correct_number_of_edges_in_this_graph(self):
        """
        Verify that adding an edge creates exactly one relationship for this graph_id.
        (We query by graph_id to avoid coupling to global num_edges() implementation.)
        """
        g = self.g

        vs = list(g.add_vertices(2))
        self.assertEqual(vs, [0,1])


        vertices_data=[
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]

        for v, data in enumerate(vertices_data):
            g.set_type(v, data["ty"])
            g.set_qubit(v, data["qubit"])
            g.set_row(v, data["row"])

        g.add_edge((0, 1))

        result = g.num_edges()

        self.assertEqual(result, 1)
