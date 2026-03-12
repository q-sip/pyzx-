import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEPhases(unittest.TestCase):

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

	def test_phases_empty_graph(self):
		"""phases should return an empty mapping for an empty graph."""
		self.assertEqual(self.g.phases(), {})

	def test_phases_default_is_zero(self):
		"""phases should return Fraction(0) for all freshly added vertices."""
		v0, v1, v2 = self.g.add_vertices(3)
		result = self.g.phases()
		self.assertEqual(result[v0], Fraction(0))
		self.assertEqual(result[v1], Fraction(0))
		self.assertEqual(result[v2], Fraction(0))

	def test_phases_contains_all_vertices(self):
		"""phases should contain an entry for every vertex in the graph."""
		vertices = self.g.add_vertices(4)
		result = self.g.phases()
		self.assertEqual(set(result.keys()), set(vertices))

	def test_phases_reflects_stored_values(self):
		"""phases should return the correct Fraction for vertices with set phases."""
		(v0, v1) = self.g.add_vertices(2)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.phase = '1/4'
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v1}}})
				SET n.phase = '3/2'
				RETURN n
			$$) AS (n agtype);
			"""
		)
		result = self.g.phases()
		self.assertEqual(result[v0], Fraction(1, 4))
		self.assertEqual(result[v1], Fraction(3, 2))


if __name__ == '__main__':
	unittest.main()
