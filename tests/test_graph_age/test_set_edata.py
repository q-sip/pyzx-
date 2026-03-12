import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGESetEData(unittest.TestCase):

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

	def test_set_edata_string(self):
		"""set_edata should store string values retrievable via edata."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edata((v0, v1), 'label', 'hello')
		self.assertEqual(self.g.edata((v0, v1), 'label', 'fallback'), 'hello')

	def test_set_edata_integer(self):
		"""set_edata should store integer values retrievable via edata."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edata((v0, v1), 'weight', 7)
		self.assertEqual(self.g.edata((v0, v1), 'weight', -1), 7)

	def test_set_edata_boolean(self):
		"""set_edata should store boolean values retrievable via edata."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edata((v0, v1), 'flag', True)
		self.assertEqual(self.g.edata((v0, v1), 'flag', False), True)

	def test_set_edata_overwrite(self):
		"""set_edata called twice with same key should overwrite the value."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edata((v0, v1), 'tag', 'first')
		self.g.set_edata((v0, v1), 'tag', 'second')
		self.assertEqual(self.g.edata((v0, v1), 'tag', 'fallback'), 'second')

	def test_set_edata_missing_edge_no_effect(self):
		"""set_edata on a missing edge should not create data and defaults should remain."""
		v0, v1 = self.g.add_vertices(2)
		self.g.set_edata((v0, v1), 'ghost', 'value')
		self.assertEqual(self.g.edata((v0, v1), 'ghost', 'fallback'), 'fallback')


if __name__ == '__main__':
	unittest.main()
