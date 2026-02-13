from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase
from fractions import Fraction
from pyzx.symbolic import Poly, Term


class TestSetPhase(Neo4jE2ETestCase):
    def test_set_phase_int(self):
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

        g.set_phase(0, 5)
        self.assertEqual(g.phase(0), Fraction(5, 1))

    def test_set_phase_fraction(self):
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

        g.set_phase(0, Fraction(3, 2))
        self.assertEqual(g.phase(0), Fraction(3, 2))

    def test_set_phase_poly(self):
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

        g.set_phase(0, Poly([(2, Term([('x', 2)])), (3, Term([('y', 2)])), (1, Term([]))]))
        self.assertEqual(g.phase(0), Poly([(2, Term([('x', 2)])), (3, Term([('y', 2)])), (1, Term([]))]))

    def test_set_phase_increment(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0, 'phase': 0},
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

        initial = int(g.phase(0))
        g.set_phase(0, 1)
        self.assertEqual(int(g.phase(0)), initial + 1)
