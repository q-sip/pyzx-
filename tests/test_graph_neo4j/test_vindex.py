import unittest
from pyzx.utils import VertexType
from pyzx.graph.graph_neo4j import GraphNeo4j

def test_vindex_empty():
    g = GraphNeo4j(graph_id="test_empty")
    assert g.vindex() == 0
    g.close()

def test_vindex_after_creation():
    g = GraphNeo4j(graph_id="test_creation")
    
    vertices_data = [{"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
        {"ty": VertexType.Z, "qubit": 0, "row": 1},
        {"ty": VertexType.X, "qubit": 0, "row": 2}]
    g.create_graph(vertices_data=vertices_data, edges_data=[])
    
    assert g.vindex() == 3
    g.close()


class TestNeo4jVindex(unittest.TestCase):
    def setUp(self):
        self.g = GraphNeo4j(graph_id="test_increment")

    def tearDown(self):
        self.g.close()

    def test_vindex_increment(self):
        initial = self.g.vindex()
        self.g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[])
        self.assertEqual(self.g.vindex(), initial + 1)