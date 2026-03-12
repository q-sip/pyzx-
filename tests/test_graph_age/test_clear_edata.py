import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType


class TestGraphAGEClearEData(unittest.TestCase):

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

	def test_clear_edata_removes_custom_properties(self):
		"""clear_edata should remove edge custom properties."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edata((v0, v1), 'label', 'hello')
		self.assertEqual(self.g.edata((v0, v1), 'label', 'fallback'), 'hello')

		self.g.clear_edata((v0, v1))
		self.assertEqual(self.g.edata((v0, v1), 'label', 'fallback'), 'fallback')

	def test_clear_edata_preserves_edge_type(self):
		"""clear_edata should preserve edge type t."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.g.set_edge_type((v0, v1), EdgeType.HADAMARD)
		self.g.set_edata((v0, v1), 'label', 'hello')

		self.g.clear_edata((v0, v1))
		self.assertEqual(self.g.edge_type((v0, v1)), EdgeType.HADAMARD)
		self.assertNotIn('label', set(self.g.edata_keys((v0, v1))))

	def test_clear_edata_missing_edge_does_not_crash(self):
		"""clear_edata on a missing edge should not raise."""
		v0, v1 = self.g.add_vertices(2)
		self.g.clear_edata((v0, v1))
		self.assertEqual(self.g.edata((v0, v1), 'label', 'fallback'), 'fallback')


if __name__ == '__main__':
	unittest.main()
