import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEVDataKeys(unittest.TestCase):

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

	def test_vdata_keys_contains_default_fields(self):
		"""vdata_keys should include built-in node properties."""
		(v0,) = self.g.add_vertices(1)
		keys = set(self.g.vdata_keys(v0))
		self.assertTrue({'id', 't', 'phase', 'qubit', 'row'}.issubset(keys))

	def test_vdata_keys_contains_custom_field(self):
		"""vdata_keys should include custom fields set via set_vdata."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_vdata(v0, 'custom_key', 'value')
		keys = set(self.g.vdata_keys(v0))
		self.assertIn('custom_key', keys)

	def test_vdata_keys_missing_vertex_returns_empty(self):
		"""vdata_keys should return empty list for non-existent vertex."""
		self.assertEqual(list(self.g.vdata_keys(999999)), [])


if __name__ == '__main__':
	unittest.main()
