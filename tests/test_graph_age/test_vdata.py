import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEVData(unittest.TestCase):

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

	def test_vdata_missing_key_returns_default(self):
		"""vdata should return default when key is not present."""
		(v0,) = self.g.add_vertices(1)
		self.assertEqual(self.g.vdata(v0, 'custom', 'fallback'), 'fallback')

	def test_vdata_string_value(self):
		"""vdata should return stored string value."""
		(v0,) = self.g.add_vertices(1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.custom = 'hello'
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.assertEqual(self.g.vdata(v0, 'custom', 'fallback'), 'hello')

	def test_vdata_numeric_value(self):
		"""vdata should return stored numeric value."""
		(v0,) = self.g.add_vertices(1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.custom = 7
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.assertEqual(self.g.vdata(v0, 'custom', -1), 7)

	def test_vdata_missing_vertex_returns_default(self):
		"""vdata should return default for a non-existent vertex."""
		self.assertEqual(self.g.vdata(999999, 'custom', 'fallback'), 'fallback')


if __name__ == '__main__':
	unittest.main()
