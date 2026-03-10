import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEEData(unittest.TestCase):

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

	def test_edata_missing_key_returns_default(self):
		"""edata should return default when key is not present on edge."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.assertEqual(self.g.edata((v0, v1), 'custom', 'fallback'), 'fallback')

	def test_edata_string_value(self):
		"""edata should return stored string value."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (a:Node {{id: {v0}}})-[r:Wire]-(b:Node {{id: {v1}}})
				SET r.custom = 'hello'
				RETURN r
			$$) AS (r agtype);
			"""
		)
		self.assertEqual(self.g.edata((v0, v1), 'custom', 'fallback'), 'hello')

	def test_edata_numeric_value(self):
		"""edata should return stored numeric value."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (a:Node {{id: {v0}}})-[r:Wire]-(b:Node {{id: {v1}}})
				SET r.weight = 7
				RETURN r
			$$) AS (r agtype);
			"""
		)
		self.assertEqual(self.g.edata((v0, v1), 'weight', -1), 7)

	def test_edata_missing_edge_returns_default(self):
		"""edata should return default for non-existent edge."""
		v0, v1 = self.g.add_vertices(2)
		self.assertEqual(self.g.edata((v0, v1), 'custom', 'fallback'), 'fallback')


if __name__ == '__main__':
	unittest.main()
