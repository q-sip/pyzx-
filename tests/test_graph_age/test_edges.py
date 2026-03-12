import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEEdges(unittest.TestCase):

	def _create_edge(self, v0, v1):
		"""Helper to create an edge between two vertices using raw Cypher."""
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
				CREATE (a)-[:Wire]->(b)
				RETURN count(*)
			$$) AS (result agtype);
			"""
		)

	def setUp(self):
		"""Set up a fresh GraphAGE instance for each test."""
		try:
			self.g = GraphAGE()
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

	def test_edges_empty_graph(self):
		"""Empty graph should return empty list."""
		edges = self.g.edges()
		self.assertEqual(len(edges), 0)
		self.assertIsInstance(edges, list)

	def test_edges_after_adding_edges(self):
		"""edges() should return all edges after adding them."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v1, v2)
		
		edges = self.g.edges()
		self.assertEqual(len(edges), 2)
		
		# Edges should be canonicalized (min, max)
		edge_set = set(edges)
		self.assertIn((min(v0, v1), max(v0, v1)), edge_set)
		self.assertIn((min(v1, v2), max(v1, v2)), edge_set)

	def test_edges_with_specific_vertices(self):
		"""edges(s, t) should return edges only between given vertices."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v1, v2)
		
		# Query edges between v0 and v1
		edges_01 = self.g.edges(v0, v1)
		self.assertEqual(len(edges_01), 1)
		
		# Query edges between v1 and v2
		edges_12 = self.g.edges(v1, v2)
		self.assertEqual(len(edges_12), 1)
		
		# Query edges between v0 and v2 (should be empty)
		edges_02 = self.g.edges(v0, v2)
		self.assertEqual(len(edges_02), 0)

	def test_edges_no_duplicates(self):
		"""edges() should not return duplicate edges (undirected)."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		
		edges = self.g.edges()
		self.assertEqual(len(edges), 1)
		
		# The edge should be canonicalized with smaller ID first
		edge = edges[0]
		self.assertEqual(edge, (min(v0, v1), max(v0, v1)))

	def test_edges_after_remove_edges(self):
		"""edges() should reflect removed edges."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v1, v2)
		self._create_edge(v0, v2)
		
		self.assertEqual(len(self.g.edges()), 3)
		
		# Remove one edge
		self.g.remove_edges([(v0, v1)])
		edges = self.g.edges()
		
		self.assertEqual(len(edges), 2)
		edge_set = set(edges)
		self.assertNotIn((min(v0, v1), max(v0, v1)), edge_set)
		self.assertIn((min(v1, v2), max(v1, v2)), edge_set)
		self.assertIn((min(v0, v2), max(v0, v2)), edge_set)

	def test_edges_multiple_edges_same_vertices(self):
		"""edges(s, t) should handle multiple edges between same vertices."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self._create_edge(v0, v1)
		
		# Should return both edges
		edges_01 = self.g.edges(v0, v1)
		self.assertEqual(len(edges_01), 2)
		
		# All edges should return both as well
		all_edges = self.g.edges()
		self.assertEqual(len(all_edges), 2)


if __name__ == '__main__':
	unittest.main()
