# tests/test_graph_neo4j/test_add_edge.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase


class TestAddEdge(Neo4jE2ETestCase):
    def test_add_edge_returns_ET(self):
        """
        Test that add_edge returns the vertex pair
        """
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 1, "qubit": 1},
        ]
        g.create_graph(nodes, [])

        self.assertEqual(g.add_edge((0, 1), EdgeType.SIMPLE), (0, 1))

    def test_add_edge_id_increments_after_create_graph(self):
        """
        After create_graph adds N edges, add_edge should return previous num_edges() + N
        """
        g = self.g

        vertices_data = [
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 0},
            {"ty": VertexType.Z, "qubit": 0, "row": 1},
            {"ty": VertexType.X, "qubit": 0, "row": 2},
            {"ty": VertexType.BOUNDARY, "qubit": 0, "row": 3},
        ]
        edges_data = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
        ]

        g.create_graph(vertices_data=vertices_data, edges_data=edges_data)
        before = g.num_edges()
        g.add_edge((0, 3))

        self.assertEqual(g.num_edges(), before + 1)

    def test_correct_number_of_edges_in_this_graph(self):
        """
        Verify that adding an edge creates exactly one relationship for this graph_id.
        (We query by graph_id to avoid coupling to global num_edges() implementation.)
        """
        g = self.g

        g.create_graph(
            vertices_data=[
                {"ty": VertexType.Z, "qubit": 0, "row": 1},
                {"ty": VertexType.X, "qubit": 0, "row": 2},
            ],
            edges_data=[],
        )
        g.add_edge((0, 1))

        query = """
            MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
            RETURN n.id as src, m.id as tgt, r.t as type
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).data()

        self.assertEqual(len(result), 1)
