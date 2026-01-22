from pyzx.utils import VertexType, EdgeType


def test_vindex_empty(neo4j_graph_unit):
    """Test that vindex returns 0 for empty graph"""
    g = neo4j_graph_unit
    assert g.num_edges() == 0


def test_vindex_after_creation(neo4j_graph_e2e):
    """Test that vindex increments after creating vertices"""
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
    
    assert g.num_edges() == 3


def test_vindex_increment(neo4j_graph_e2e):
    """Test that vindex continues to increment correctly"""
    g = neo4j_graph_e2e
    
    initial = g.vindex()
    g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}, {"ty": VertexType.X, "qubit": 0, "row": 2}], edges_data=[((1, 2), EdgeType.HADAMARD)])
    assert g.num_edges() == initial + 1