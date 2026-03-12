# tests/test_graph_neo4j/test_remove_isolated_vertices.py
from fractions import Fraction

from pyzx.utils import EdgeType, VertexType

from tests.test_graph_neo4j._base_unittest import Neo4jUnitTestCase

class TestRemoveIsolatedVertices(Neo4jUnitTestCase):
    def _count_nodes(self) -> int:
        g = self.g
        query = """
            MATCH (n:Node {graph_id: $gid})
            RETURN count(n) as count
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).single()
            return result["count"] if result else 0

    def _node_exists(self, vid: int) -> bool:
        g = self.g
        query = """
            MATCH (n:Node {graph_id: $gid, id: $vid})
            RETURN count(n) > 0 as exists
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id, vid=vid).single()
            return bool(result["exists"]) if result else False

    def _count_edges(self) -> int:
        g = self.g
        query = """
            MATCH (n:Node {graph_id: $gid})-[r:Wire]->(m:Node {graph_id: $gid})
            RETURN count(r) as count
        """
        with g._get_session() as session:
            result = session.run(query, gid=g.graph_id).single()
            return result["count"] if result else 0

    def test_remove_single_isolated_non_boundary_vertex(self):
        g = self.g

        nodes = [
            {"ty": VertexType.Z, "phase": Fraction(1, 2)},
        ]
        edges = []
        g.create_graph(nodes, edges)

        self.assertEqual(self._count_nodes(), 1)
        self.assertEqual(self._count_edges(), 0)

        g.remove_isolated_vertices()

        self.assertEqual(self._count_nodes(), 0)
        self.assertFalse(self._node_exists(0))

    def test_isolated_boundary_vertex_raises(self):
        g = self.g

        nodes = [
            {"ty": VertexType.BOUNDARY},
        ]
        g.create_graph(nodes, [])

        self.assertEqual(self._count_nodes(), 1)

        with self.assertRaises(TypeError):
            g.remove_isolated_vertices()

        # Should still exist (since method raised before deletion completes)
        self.assertTrue(self._node_exists(0))

    def test_remove_isolated_pair_degree1_each(self):
        g = self.g

        # Two non-boundary vertices connected only to each other
        nodes = [
            {"ty": VertexType.Z, "phase": Fraction(1, 4)},
            {"ty": VertexType.Z, "phase": Fraction(1, 4)},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)

        self.assertEqual(self._count_nodes(), 2)
        self.assertEqual(self._count_edges(), 1)

        g.remove_isolated_vertices()

        self.assertEqual(self._count_nodes(), 0)
        self.assertEqual(self._count_edges(), 0)
        self.assertFalse(self._node_exists(0))
        self.assertFalse(self._node_exists(1))

    def test_does_not_remove_connected_component(self):
        g = self.g

        # Chain of length 3: endpoints have degree 1 but middle has degree 2
        nodes = [
            {"ty": VertexType.Z},
            {"ty": VertexType.X},
            {"ty": VertexType.Z},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
            ((1, 2), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)

        self.assertEqual(self._count_nodes(), 3)
        self.assertEqual(self._count_edges(), 2)

        g.remove_isolated_vertices()

        # Nothing should be removed
        self.assertEqual(self._count_nodes(), 3)
        self.assertEqual(self._count_edges(), 2)
        self.assertTrue(self._node_exists(0))
        self.assertTrue(self._node_exists(1))
        self.assertTrue(self._node_exists(2))

    def test_ignores_boundary_degree1_vertices(self):
        g = self.g

        # Boundary connected to a Z; boundary shouldn't be removed by this method
        nodes = [
            {"ty": VertexType.BOUNDARY},
            {"ty": VertexType.Z},
        ]
        edges = [
            ((0, 1), EdgeType.SIMPLE),
        ]
        g.create_graph(nodes, edges)

        self.assertEqual(self._count_nodes(), 2)
        self.assertEqual(self._count_edges(), 1)

        g.remove_isolated_vertices()

        # Still connected; no isolated components
        self.assertEqual(self._count_nodes(), 2)
        self.assertEqual(self._count_edges(), 1)
        self.assertTrue(self._node_exists(0))
        self.assertTrue(self._node_exists(1))
