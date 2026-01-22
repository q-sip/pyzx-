# tests/test_graph_neo4j/test_remove_vertices.py
from pyzx.utils import EdgeType, VertexType


class _FakeTx:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return None


class _FakeSession:
    def __init__(self):
        self.tx = _FakeTx()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_write(self, fn):
        return fn(self.tx)


def test_remove_vertices_unit_updates_inputs_outputs(monkeypatch, neo4j_graph_unit):
    """Test that remove_vertices updates internal _inputs and _outputs tuples"""
    g = neo4j_graph_unit

    # Set up initial state
    g._inputs = (0, 1, 2, 3)
    g._outputs = (3, 4, 5)

    fake_session = _FakeSession()
    monkeypatch.setattr(g, "_get_session", lambda: fake_session)

    # Remove vertices 1 and 3
    g.remove_vertices([1, 3])

    # Check that inputs and outputs were updated
    assert g._inputs == (0, 2)
    assert g._outputs == (4, 5)

    # Verify Cypher was called
    assert len(fake_session.tx.calls) == 1
    query, params = fake_session.tx.calls[0]
    assert "DETACH DELETE" in query
    assert params["vertex_ids"] == [1, 3]
    assert params["graph_id"] == g.graph_id


def test_remove_vertices_unit_with_empty_list(monkeypatch, neo4j_graph_unit):
    """Test that remove_vertices handles empty list gracefully"""
    g = neo4j_graph_unit

    fake_session = _FakeSession()
    monkeypatch.setattr(g, "_get_session", lambda: fake_session)

    # Remove no vertices
    g.remove_vertices([])

    # No Cypher should have been executed
    assert len(fake_session.tx.calls) == 0


def test_remove_vertices_e2e_deletes_nodes_and_edges(neo4j_graph_e2e):
    """End-to-end test that remove_vertices actually deletes nodes and edges from Neo4j"""
    g = neo4j_graph_e2e

    # Create a simple graph
    vertices_data = [
        {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
        {"ty": VertexType.Z, "row": 1, "qubit": 0},
        {"ty": VertexType.X, "row": 2, "qubit": 0},
        {"ty": VertexType.Z, "row": 3, "qubit": 0},
        {"ty": VertexType.BOUNDARY, "row": 4, "qubit": 0},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.HADAMARD),
        ((2, 3), EdgeType.SIMPLE),
        ((3, 4), EdgeType.SIMPLE),
    ]

    v_ids = g.create_graph(
        vertices_data=vertices_data,
        edges_data=edges_data,
        inputs=[0],
        outputs=[4]
    )

    # Verify initial state
    assert g.num_vertices() == 5

    # Remove middle vertices (1 and 2)
    g.remove_vertices([v_ids[1], v_ids[2]])

    # Check that vertices were removed
    assert g.num_vertices() == 3

    # Verify in database
    with g._get_session() as session:
        result = session.run(
            "MATCH (n:Node {graph_id: $gid}) RETURN collect(n.id) AS ids",
            gid=g.graph_id,
        ).single()
        remaining_ids = result["ids"]
        
        assert v_ids[0] in remaining_ids
        assert v_ids[1] not in remaining_ids
        assert v_ids[2] not in remaining_ids
        assert v_ids[3] in remaining_ids
        assert v_ids[4] in remaining_ids


def test_remove_vertices_e2e_removes_connected_edges(neo4j_graph_e2e):
    """Test that removing vertices also removes all connected edges"""
    g = neo4j_graph_e2e

    vertices_data = [
        {"ty": VertexType.Z, "row": 0, "qubit": 0},
        {"ty": VertexType.X, "row": 1, "qubit": 0},
        {"ty": VertexType.Z, "row": 2, "qubit": 0},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.HADAMARD),
    ]

    v_ids = g.create_graph(
        vertices_data=vertices_data,
        edges_data=edges_data
    )

    # Verify edges exist
    with g._get_session() as session:
        edge_count = session.run(
            "MATCH (:Node {graph_id: $gid})-[r:Wire]->() RETURN count(r) AS c",
            gid=g.graph_id,
        ).single()["c"]
        assert edge_count == 2

    # Remove the middle vertex
    g.remove_vertices([v_ids[1]])

    # Verify edges were removed
    with g._get_session() as session:
        edge_count = session.run(
            "MATCH (:Node {graph_id: $gid})-[r:Wire]->() RETURN count(r) AS c",
            gid=g.graph_id,
        ).single()["c"]
        assert edge_count == 0  # Both edges should be gone


def test_remove_vertices_e2e_updates_inputs_outputs(neo4j_graph_e2e):
    """Test that removing input/output vertices updates the internal tuples"""
    g = neo4j_graph_e2e

    vertices_data = [
        {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
        {"ty": VertexType.Z, "row": 1, "qubit": 0},
        {"ty": VertexType.BOUNDARY, "row": 2, "qubit": 0},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.SIMPLE),
    ]

    v_ids = g.create_graph(
        vertices_data=vertices_data,
        edges_data=edges_data,
        inputs=[0],
        outputs=[2]
    )

    assert g._inputs == (v_ids[0],)
    assert g._outputs == (v_ids[2],)

    # Remove the input vertex
    g.remove_vertices([v_ids[0]])

    # Check that inputs were updated
    assert g._inputs == ()
    assert g._outputs == (v_ids[2],)

    # Remove the output vertex
    g.remove_vertices([v_ids[2]])

    # Check that outputs were updated
    assert g._outputs == ()
