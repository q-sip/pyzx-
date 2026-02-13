from pyzx.utils import VertexType, EdgeType
from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase, Neo4jUnitTestCase


class TestIncidentEdgesE2E(Neo4jE2ETestCase):
    def test_incident_edges_empty(self):
        g = self.g

        vertices_data=[
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 2},
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=[])
        self.assertEqual(g.incident_edges(1), [])

    def test_incident_edges_after_creation(self):
        """Test that incident_edges increments after creating edges"""
        g = self.g
        
        vertices_data=[
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 2},
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        ]
        edges_data=[
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
            ((3, 4), EdgeType.SIMPLE),
            ((4, 2), EdgeType.SIMPLE),
            ((1, 4), EdgeType.SIMPLE),
            ((5, 0), EdgeType.SIMPLE),
            ((4, 5), EdgeType.SIMPLE),
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)

        
        #Sama homma täällä, että edget lisätään vain yhteen suuntaan, pienemmästä id:stä suurempaan. Siksi incident_edges(2) palauttaa vain edget (1,2), (2,3) ja (2,4), ei (4,2)
        # Eikä testatessa (2,1) toimi.
        self.assertEqual(sorted(g.incident_edges(2)), [(2, 1), (2, 3), (2, 4)])

    def test_incident_edges_more_edges(self):
        """Testing for more incident_edges"""
        g = self.g
        
        vertices_data=[
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 2},
        {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        ]
        edges_data=[
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
            ((3, 4), EdgeType.SIMPLE),
            ((4, 2), EdgeType.SIMPLE),
            ((1, 4), EdgeType.SIMPLE),
            ((5, 0), EdgeType.SIMPLE),
            ((4, 5), EdgeType.SIMPLE),
        ]
        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)
        #Ja sama tässä
        self.assertCountEqual(sorted(g.incident_edges(4)), [(4, 1), (4, 2), (4, 3), (4, 5)])


    def test_incident_edges_increment(self):
        """Test that edges continues to increment correctly"""
        g = self.g

        initial = len(g.incident_edges(0))
        g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}, {"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[((0, 1), EdgeType.HADAMARD)])
        self.assertEqual(len(g.incident_edges(0)), initial + 1)
