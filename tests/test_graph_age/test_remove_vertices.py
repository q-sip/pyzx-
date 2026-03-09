
import unittest
import sys
import os

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType, VertexType


class TestGraphAGERemoveVertices(unittest.TestCase):

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

    def _count_nodes_by_ids(self, ids):
        if not ids:
            return 0
        ids_str = ", ".join(str(v) for v in ids)
        query = f"""
        SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
            MATCH (n:Node)
            WHERE n.id IN [{ids_str}]
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

    def test_remove_single_vertex(self):
        """Test removing a single vertex."""
        v_ids = self.g.add_vertices(3)
        self.assertEqual(self._count_all_nodes(), 3)
        
        # Remove one vertex
        self.g.remove_vertices([v_ids[0]])
        
        self.assertEqual(self._count_nodes_by_ids([v_ids[0]]), 0)
        self.assertEqual(self._count_all_nodes(), 2)

    def test_remove_multiple_vertices(self):
        """Test removing multiple vertices at once."""
        v_ids = self.g.add_vertices(5)
        self.assertEqual(self._count_all_nodes(), 5)
        
        # Remove multiple vertices
        self.g.remove_vertices([v_ids[0], v_ids[2], v_ids[4]])
        
        self.assertEqual(self._count_nodes_by_ids([v_ids[0], v_ids[2], v_ids[4]]), 0)
        self.assertEqual(self._count_all_nodes(), 2)

    def test_remove_vertices_empty_list(self):
        """Test removing vertices with an empty list (should not crash)."""
        self.g.add_vertices(3)
        self.assertEqual(self._count_all_nodes(), 3)
        
        # Remove with empty list should be a no-op
        self.g.remove_vertices([])
        
        self.assertEqual(self._count_all_nodes(), 3)

    def test_remove_vertices_with_edges(self):
        """Test removing vertices that have edges (should use DETACH DELETE)."""
        v0, v1, v2 = self.g.add_vertices(3)
        
        self.g.db_execute(
            f"""
            SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
                MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
                CREATE (a)-[:Wire]->(b)
                RETURN count(*)
            $$) AS (result agtype);
            """
        )
        self.g.db_execute(
            f"""
            SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
                MATCH (a:Node {{id: {v1}}}), (b:Node {{id: {v2}}})
                CREATE (a)-[:Wire]->(b)
                RETURN count(*)
            $$) AS (result agtype);
            """
        )
        self.assertEqual(self._count_all_edges(), 2)
        
        # Remove middle vertex (which has edges)
        self.g.remove_vertices([v1])
        
        self.assertEqual(self._count_nodes_by_ids([v1]), 0)
        self.assertEqual(self._count_all_nodes(), 2)
        self.assertEqual(self._count_all_edges(), 0)

    def test_remove_all_vertices(self):
        """Test removing all vertices from the graph."""
        v_ids = self.g.add_vertices(4)
        self.assertEqual(self._count_all_nodes(), 4)
        
        # Remove all vertices
        self.g.remove_vertices(v_ids)
        
        self.assertEqual(self._count_all_nodes(), 0)


if __name__ == '__main__':
    unittest.main()
