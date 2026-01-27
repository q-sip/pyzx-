from pyzx.utils import VertexType, EdgeType


def test_edges_empty(neo4j_graph_unit):
    """Test that edges returns an empty list for empty graph"""
    g = neo4j_graph_unit
    assert g.edges() == []


def test_edges_after_creation(neo4j_graph_e2e):
    """Test that edges increments after creating edges"""
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
    
    assert g.edges() == [(0, 1), (1, 2), (2, 0)]

def test_edges_singular(neo4j_graph_e2e):
    """Test that edges returns correct edges between 2 vertices"""
    g = neo4j_graph_e2e
    
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
    
    assert g.edges(0, 3) == [(3, 0), (0, 3)]


def test_edges_increment(neo4j_graph_e2e):
    """Test that edges continues to increment correctly"""
    g = neo4j_graph_e2e

    initial = len(g.edges())
    g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}], edges_data=[((1, 2), EdgeType.HADAMARD)])
    assert len(g.edges()) == initial + 1

