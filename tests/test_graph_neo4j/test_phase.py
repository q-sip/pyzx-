from pyzx.utils import VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase
from fractions import Fraction
from pyzx.symbolic import Poly, Term




class TestPhaseE2E(Neo4jE2ETestCase):
    def test_phase_empty(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])
        self.assertEqual(g.phase(3), 0)

    def test_phase_int(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0, 'phase': 4},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])

        self.assertEqual(g.phase(0), Fraction(0,1))

    def test_phase_fraction(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0, 'phase': Fraction(1, 5)},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])

        self.assertEqual(g.phase(0), Fraction(1, 5))

    def test_phase_poly(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0, 'phase': Poly([(2, Term([('x', 2)])), (3, Term([('y', 2)])), (1, Term([]))])},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])
 
        self.assertEqual(g.phase(0), Poly([(1, Term([('y', 2)])), (1, Term([]))]))
