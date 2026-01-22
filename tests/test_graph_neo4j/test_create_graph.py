# tests/test_graph_neo4j/test_create_graph.py
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


def test_create_graph_unit_updates_indices_and_marks_inputs_outputs(
    monkeypatch, neo4j_graph_unit
):
    g = neo4j_graph_unit

    fake_session = _FakeSession()
    monkeypatch.setattr(g, "_get_session", lambda: fake_session)

    vertices_data = [
        {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
        {"ty": VertexType.Z, "row": 3, "qubit": 0, "phase": 0},
        {"ty": VertexType.X, "row": 2, "qubit": 1, "phase": 1},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.SIMPLE),
    ]

    v = g.create_graph(
        vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[2]
    )

    assert v == [0, 1, 2]
    assert g._vindex == 3
    assert g._inputs == (0,)
    assert g._outputs == (2,)

    # It should have executed cypher
    assert len(fake_session.tx.calls) >= 1
    combined = "\n".join(q for (q, _) in fake_session.tx.calls)
    assert "CREATE" in combined
    assert ":Node" in combined


def test_create_graph_e2e_creates_nodes_edges_and_labels(neo4j_graph_e2e):
    g = neo4j_graph_e2e

    vertices_data = [
        {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
        {"ty": VertexType.Z, "row": 1, "qubit": 0, "phase": 0},
        {"ty": VertexType.X, "row": 2, "qubit": 0, "phase": 1},
        {"ty": VertexType.BOUNDARY, "row": 3, "qubit": 0},
    ]
    edges_data = [
        ((0, 1), EdgeType.SIMPLE),
        ((1, 2), EdgeType.SIMPLE),
        ((2, 3), EdgeType.SIMPLE),
    ]

    g.create_graph(
        vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[3]
    )

    with g._get_session() as session:
        n = session.run(
            "MATCH (n:Node {graph_id: $gid}) RETURN count(n) AS c",
            gid=g.graph_id,
        ).single()["c"]
        assert n == 4

        e = session.run(
            "MATCH (:Node {graph_id: $gid})-[r:Wire]->(:Node {graph_id: $gid}) RETURN count(r) AS c",
            gid=g.graph_id,
        ).single()["c"]
        assert e == 3

        in_count = session.run(
            "MATCH (n:Node:Input {graph_id: $gid}) RETURN count(n) AS c",
            gid=g.graph_id,
        ).single()["c"]
        assert in_count == 1

        out_count = session.run(
            "MATCH (n:Node:Output {graph_id: $gid}) RETURN count(n) AS c",
            gid=g.graph_id,
        ).single()["c"]
        assert out_count == 1
