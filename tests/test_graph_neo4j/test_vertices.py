from pyzx.utils import VertexType, EdgeType


def test_vertices_empty(neo4j_graph_unit):
    """Test that vertices returns an empty list for empty graph"""
    g = neo4j_graph_unit
    assert g.vertices() == []


def test_vertices_after_creation(neo4j_graph_e2e):
    """Test that vertices increments after creating vertices"""
    g = neo4j_graph_e2e
    
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
    
    assert g.vertices() == [0, 1, 2]


def test_vertices_increment(neo4j_graph_e2e):
    """Test that vertices continues to increment correctly"""
    g = neo4j_graph_e2e
    
    initial = len(g.vertices())
    g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[((1, 2), EdgeType.HADAMARD)])
    assert len(g.vertices()) == initial + 1