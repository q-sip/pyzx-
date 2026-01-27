# tests/test_graph_neo4j/test_remove_edges.py
from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jE2ETestCase


class TestRemoveEdges(Neo4jE2ETestCase):
    def _count_edges(self) -> int:
        g = self.g
        query = """
            MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
            RETURN count(r) as count
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).single()
            return result["count"] if result else 0

    def _edge_exists(self, src: int, tgt: int) -> bool:
        g = self.g
        query = """
            MATCH (n:Node {graph_id: $gid, id: $src})-[r:Wire]-(m:Node {graph_id: $gid, id: $tgt})
            RETURN count(r) > 0 as exists
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id, src=src, tgt=tgt).single()
            return bool(result["exists"]) if result else False

    def test_remove_single_edge(self):
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
            {"ty": VertexType.Z, "row": 1, "qubit": 0},
            {"ty": VertexType.X, "row": 2, "qubit": 0},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)

        self.assertEqual(self._count_edges(), 2)

        g.remove_edges([(0, 1)])

        self.assertEqual(self._count_edges(), 1)
        self.assertFalse(self._edge_exists(0, 1))
        self.assertTrue(self._edge_exists(1, 2))

    def test_remove_multiple_edges(self):
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY},
            {"ty": VertexType.Z},
            {"ty": VertexType.X},
            {"ty": VertexType.BOUNDARY},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.HADAMARD),
            ((2, 3), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)

        self.assertEqual(self._count_edges(), 3)

        g.remove_edges([(0, 1), (2, 3)])

        self.assertEqual(self._count_edges(), 1)
        self.assertFalse(self._edge_exists(0, 1))
        self.assertTrue(self._edge_exists(1, 2))
        self.assertFalse(self._edge_exists(2, 3))

    def test_remove_edges_empty_list(self):
        g = self.g

        g.create_graph(
            [{"ty": VertexType.Z}, {"ty": VertexType.X}], [((0, 1), EdgeType.SIMPLE)]
        )
        initial = self._count_edges()

        g.remove_edges([])

        self.assertEqual(self._count_edges(), initial)

    def test_remove_nonexistent_edge(self):
        g = self.g

        nodes = [
            {"ty": VertexType.Z},
            {"ty": VertexType.X},
            {"ty": VertexType.BOUNDARY},
        ]
        edges = [((1, 2), EdgeType.SIMPLE)]
        g.create_graph(nodes, edges)

        initial = self._count_edges()

        g.remove_edges([(0, 1)])

        self.assertEqual(self._count_edges(), initial)
        self.assertTrue(self._edge_exists(1, 2))

    def test_remove_edges_bidirectional(self):
        g = self.g

        g.create_graph(
            [{"ty": VertexType.Z}, {"ty": VertexType.X}], [((0, 1), EdgeType.SIMPLE)]
        )

        self.assertTrue(self._edge_exists(0, 1))

        g.remove_edges([(1, 0)])

        self.assertFalse(self._edge_exists(0, 1))
        self.assertFalse(self._edge_exists(1, 0))

    def test_remove_hadamard_edge(self):
        g = self.g

        g.create_graph(
            [{"ty": VertexType.Z}, {"ty": VertexType.Z}], [((0, 1), EdgeType.HADAMARD)]
        )

        self.assertEqual(self._count_edges(), 1)

        g.remove_edges([(0, 1)])

        self.assertEqual(self._count_edges(), 0)
