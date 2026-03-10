import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE

class TestGraphAGEConnected(unittest.TestCase):

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

	def test_connected_empty_graph(self):
		"""connected should return False for missing vertices in empty graph."""
		self.assertFalse(self.g.connected(0, 1))

	def test_connected_true_for_existing_edge(self):
		"""connected should return True when an edge exists between vertices."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.assertTrue(self.g.connected(v0, v1))
		self.assertTrue(self.g.connected(v1, v0))

	def test_connected_false_for_disconnected_vertices(self):
		"""connected should return False for vertices without an edge."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self.assertFalse(self.g.connected(v0, v2))
		self.assertFalse(self.g.connected(v1, v2))

	def test_connected_self_loop(self):
		"""connected(v, v) should return True when a self-loop exists."""
		(v0,) = self.g.add_vertices(1)
		self._create_edge(v0, v0)
		self.assertTrue(self.g.connected(v0, v0))

if __name__ == '__main__':
	unittest.main()
