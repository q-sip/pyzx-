from pyzx.utils import VertexType, EdgeType
from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase


class TestEdgesE2E(Neo4jE2ETestCase):
    def test_edges_empty(self):
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])
        self.assertEqual(g.edges(), [])

    def test_edges_after_creation(self):
        """Test that edges increments after creating edges"""
        g = self.g
        
        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2}
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 0), EdgeType.SIMPLE)
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)
        edges = sorted(g.edges(), key=lambda x: (x[0], x[1]))
        self.assertEqual(edges, sorted([(0, 1), (1, 2), (0, 2)], key=lambda x: (x[0], x[1])))

    def test_edges_singular(self):
        """Test that edges returns correct edges between 2 vertices"""
        g = self.g
        
        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3}
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
            ((0, 3), EdgeType.SIMPLE),
            ((3, 0), EdgeType.HADAMARD)
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)
        
        edges = sorted(g.edges(0, 3))
        self.assertEqual(edges, [(0, 3), (3, 0)])


    def test_edges_increment(self):
        """Test that edges continues to increment correctly"""
        g = self.g

        initial = len(g.edges())
        g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}, {"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[((0, 1), EdgeType.HADAMARD)])
        self.assertEqual(len(g.edges()), initial + 1)
