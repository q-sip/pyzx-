from pyzx.utils import VertexType, EdgeType


def test_add_edge_first(neo4j_graph_e2e):
    """Test that add_edge returns 0 for the first edge added"""
    g = neo4j_graph_e2e
    nodes = [
            {"id": 0, "ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"id": 1, "ty": VertexType.Z, "row": 1, "qubit": 0},
            {"id": 2, "ty": VertexType.X, "row": 1, "qubit": 1},
        ]
    g.create_graph(nodes, [])
    assert g.add_edge((0, 1), EdgeType.SIMPLE) == 0


def test_add_edge_secong(neo4j_graph_e2e):
    """Test that add_edge increments after creating vertices"""
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
        ((2, 3), EdgeType.SIMPLE)
    ]
    g.create_graph(vertices_data=vertices_data, edges_data=edges_data)
    
    # test without second parameter
    assert g.add_edge((3, 0)) == 3


def test_correct_number_of_edges(neo4j_graph_e2e):
    """Test that the graph has the correct amount of edges"""
    g = neo4j_graph_e2e
    
    initial = g.num_edges()
    g.create_graph(vertices_data=[{"ty": VertexType.Z, "qubit": 0, "row": 1}, {"ty": VertexType.X, "qubit": 0, "row": 2}], edges_data=[])
    g.add_edge((0, 1))

    query = """
        MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
        RETURN n.id as src, m.id as tgt, r.t as type
        """

    with g._get_session() as session:
        result = session.run(query, gid=g.graph_id).data()

    assert len(result) == initial + 1