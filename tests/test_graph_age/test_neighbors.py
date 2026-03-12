import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGENeighbors(unittest.TestCase):

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

	def test_neighbors_empty_graph(self):
		"""neighbors should return empty list in an empty graph."""
		self.assertEqual(self.g.neighbors(0), [])

	def test_neighbors_single_neighbor(self):
		"""neighbors should return one adjacent vertex."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)

		neighbors_v0 = self.g.neighbors(v0)
		neighbors_v1 = self.g.neighbors(v1)

		self.assertEqual(set(neighbors_v0), {v1})
		self.assertEqual(set(neighbors_v1), {v0})

	def test_neighbors_multiple_neighbors(self):
		"""neighbors should return all adjacent vertices."""
		v0, v1, v2, v3 = self.g.add_vertices(4)
		self._create_edge(v0, v1)
		self._create_edge(v0, v2)
		self._create_edge(v0, v3)

		neighbors_v0 = self.g.neighbors(v0)
		self.assertEqual(set(neighbors_v0), {v1, v2, v3})

	def test_neighbors_no_duplicates(self):
		"""neighbors should not contain duplicates even with parallel edges."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self._create_edge(v0, v1)

		neighbors_v0 = self.g.neighbors(v0)
		self.assertEqual(set(neighbors_v0), {v1})
		self.assertEqual(len(neighbors_v0), 1)

	def test_neighbors_after_remove_edges(self):
		"""neighbors should update after removing edges."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v0, v2)
		self.assertEqual(set(self.g.neighbors(v0)), {v1, v2})

		self.g.remove_edges([(v0, v1)])
		self.assertEqual(set(self.g.neighbors(v0)), {v2})


if __name__ == '__main__':
	unittest.main()
