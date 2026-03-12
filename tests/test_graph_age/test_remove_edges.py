
import unittest
import sys
import os

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType, VertexType


class TestGraphAGERemoveEdges(unittest.TestCase):

    def _count_all_nodes(self):
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
            MATCH (n:Node)
            RETURN count(n)
        $$) AS (count agtype);
        """
        with self.g.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.g.conn.commit()
        return int(str(row[0]).split("::", 1)[0].strip('"'))

    def _count_all_edges(self):
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
            MATCH ()-[e]->()
            RETURN count(e)
        $$) AS (count agtype);
        """
        with self.g.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.g.conn.commit()
        return int(str(row[0]).split("::", 1)[0].strip('"'))

    def _create_edge(self, v0, v1):
        """Helper to create an edge between two vertices."""
        self.g.db_execute(
            f"""
            SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
                MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
                CREATE (a)-[:Wire]->(b)
                RETURN count(*)
            $$) AS (result agtype);
            """
        )

    def _edge_exists(self, v0, v1):
        """Check if an edge exists between two vertices (bidirectional)."""
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
            MATCH (a:Node {{id: {v0}}})-[e:Wire]-(b:Node {{id: {v1}}})
            RETURN count(e)
        $$) AS (count agtype);
        """
        with self.g.conn.cursor() as cur:
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, public;")
            cur.execute(query)
            row = cur.fetchone()
            self.g.conn.commit()
        return int(str(row[0]).split("::", 1)[0].strip('"')) > 0

    def setUp(self):
        """Set up a fresh GraphAGE instance for each test."""
        try:
            self.g = GraphAGE()
            # Clear any existing data
            self.g.delete_graph()
            self.g.close()
            self.g = GraphAGE()
        except Exception as e:
            self.skipTest(f"AGE database not available: {e}")

    def tearDown(self):
        """Clean up after each test."""
        try:
            if hasattr(self, 'g'):
                self.g.delete_graph()
                self.g.close()
        except Exception:
            pass

    def test_remove_single_edge(self):
        """Test removing a single edge."""
        v0, v1, v2 = self.g.add_vertices(3)
        
        # Create edges
        self._create_edge(v0, v1)
        self._create_edge(v1, v2)
        self.assertEqual(self._count_all_edges(), 2)
        
        # Remove one edge
        self.g.remove_edges([(v0, v1)])
        
        self.assertFalse(self._edge_exists(v0, v1))
        self.assertTrue(self._edge_exists(v1, v2))
        self.assertEqual(self._count_all_edges(), 1)

    def test_remove_multiple_edges(self):
        """Test removing multiple edges at once."""
        v0, v1, v2, v3 = self.g.add_vertices(4)
        
        # Create edges
        self._create_edge(v0, v1)
        self._create_edge(v1, v2)
        self._create_edge(v2, v3)
        self.assertEqual(self._count_all_edges(), 3)
        
        # Remove multiple edges
        self.g.remove_edges([(v0, v1), (v2, v3)])
        
        self.assertFalse(self._edge_exists(v0, v1))
        self.assertTrue(self._edge_exists(v1, v2))
        self.assertFalse(self._edge_exists(v2, v3))
        self.assertEqual(self._count_all_edges(), 1)

    def test_remove_edges_empty_list(self):
        """Test removing edges with an empty list (should not crash)."""
        v0, v1 = self.g.add_vertices(2)
        self._create_edge(v0, v1)
        self.assertEqual(self._count_all_edges(), 1)
        
        # Remove with empty list should be a no-op
        self.g.remove_edges([])
        
        self.assertEqual(self._count_all_edges(), 1)
        self.assertTrue(self._edge_exists(v0, v1))

    def test_remove_all_edges(self):
        """Test removing all edges from the graph."""
        v0, v1, v2, v3 = self.g.add_vertices(4)
        
        # Create edges
        self._create_edge(v0, v1)
        self._create_edge(v1, v2)
        self._create_edge(v2, v3)
        self.assertEqual(self._count_all_edges(), 3)
        
        # Remove all edges
        self.g.remove_edges([(v0, v1), (v1, v2), (v2, v3)])
        
        self.assertEqual(self._count_all_edges(), 0)
        # Vertices should still exist
        self.assertEqual(self._count_all_nodes(), 4)

    def test_remove_edges_bidirectional(self):
        """Test that remove_edges works with edge pairs in either direction."""
        v0, v1 = self.g.add_vertices(2)
        self._create_edge(v0, v1)
        self.assertEqual(self._count_all_edges(), 1)
        
        # Try removing with reversed pair
        self.g.remove_edges([(v1, v0)])
        
        self.assertFalse(self._edge_exists(v0, v1))
        self.assertEqual(self._count_all_edges(), 0)


if __name__ == '__main__':
    unittest.main()
