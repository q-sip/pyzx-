import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGENumEdges(unittest.TestCase):

	def _create_edge(self, v0, v1):
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

	def test_num_edges_empty_graph(self):
		"""Empty graph should report zero edges."""
		self.assertEqual(self.g.num_edges(), 0)

	def test_num_edges_after_adding_edges(self):
		"""Adding edges should increase num_edges accordingly."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v1, v2)

		self.assertEqual(self.g.num_edges(), 2)

	def test_num_edges_between_vertices(self):
		"""num_edges(s, t) should count edges only between given vertices."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v1, v2)

		self.assertEqual(self.g.num_edges(v0, v1), 1)
		self.assertEqual(self.g.num_edges(v1, v2), 1)
		self.assertEqual(self.g.num_edges(v0, v2), 0)

	def test_num_edges_after_remove_edges(self):
		"""Removing edges should decrease num_edges accordingly."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v1, v2)
		self.assertEqual(self.g.num_edges(), 2)

		self.g.remove_edges([(v0, v1)])
		self.assertEqual(self.g.num_edges(), 1)
		self.assertEqual(self.g.num_edges(v0, v1), 0)
		self.assertEqual(self.g.num_edges(v1, v2), 1)


if __name__ == '__main__':
	unittest.main()
