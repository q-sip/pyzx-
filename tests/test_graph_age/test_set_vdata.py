import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGESetVData(unittest.TestCase):

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

	def test_set_vdata_string(self):
		"""set_vdata should store string values retrievable via vdata."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_vdata(v0, 'label', 'hello')
		self.assertEqual(self.g.vdata(v0, 'label', 'fallback'), 'hello')

	def test_set_vdata_integer(self):
		"""set_vdata should store integer values retrievable via vdata."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_vdata(v0, 'weight', 7)
		self.assertEqual(self.g.vdata(v0, 'weight', -1), 7)

	def test_set_vdata_boolean(self):
		"""set_vdata should store boolean values retrievable via vdata."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_vdata(v0, 'flag', True)
		self.assertEqual(self.g.vdata(v0, 'flag', False), True)

	def test_set_vdata_overwrite(self):
		"""set_vdata called twice with same key should overwrite the value."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_vdata(v0, 'tag', 'first')
		self.g.set_vdata(v0, 'tag', 'second')
		self.assertEqual(self.g.vdata(v0, 'tag', 'fallback'), 'second')

	def test_set_vdata_missing_vertex_no_effect(self):
		"""set_vdata on a missing vertex should not create data and defaults should remain."""
		self.g.set_vdata(999999, 'ghost', 'value')
		self.assertEqual(self.g.vdata(999999, 'ghost', 'fallback'), 'fallback')


if __name__ == '__main__':
	unittest.main()
