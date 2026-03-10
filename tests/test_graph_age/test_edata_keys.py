import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType


class TestGraphAGEEDataKeys(unittest.TestCase):

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

	def test_edata_keys_contains_default_fields(self):
		"""edata_keys should include built-in edge properties like t when present."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edge_type((v0, v1), EdgeType.HADAMARD)
		keys = set(self.g.edata_keys((v0, v1)))
		self.assertIn('t', keys)

	def test_edata_keys_contains_custom_field(self):
		"""edata_keys should include custom fields set via set_edata."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edata((v0, v1), 'custom_key', 'value')
		keys = set(self.g.edata_keys((v0, v1)))
		self.assertIn('custom_key', keys)

	def test_edata_keys_missing_edge_returns_empty(self):
		"""edata_keys should return empty list for non-existent edge."""
		v0, v1 = self.g.add_vertices(2)
		self.assertEqual(list(self.g.edata_keys((v0, v1))), [])


if __name__ == '__main__':
	unittest.main()
