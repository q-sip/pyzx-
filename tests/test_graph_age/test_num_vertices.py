import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGENumVertices(unittest.TestCase):

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

	def test_num_vertices_empty_graph(self):
		"""Empty graph should report zero vertices."""
		self.assertEqual(self.g.num_vertices(), 0)

	def test_num_vertices_after_add_vertices(self):
		"""Adding vertices should increase num_vertices accordingly."""
		self.g.add_vertices(3)
		self.assertEqual(self.g.num_vertices(), 3)

		self.g.add_vertices(2)
		self.assertEqual(self.g.num_vertices(), 5)

	def test_num_vertices_after_remove_vertices(self):
		"""Removing vertices should decrease num_vertices accordingly."""
		v_ids = self.g.add_vertices(5)
		self.assertEqual(self.g.num_vertices(), 5)

		self.g.remove_vertices([v_ids[1], v_ids[3]])
		self.assertEqual(self.g.num_vertices(), 3)

	def test_num_vertices_after_remove_all_vertices(self):
		"""Removing all vertices should return count back to zero."""
		v_ids = self.g.add_vertices(4)
		self.assertEqual(self.g.num_vertices(), 4)

		self.g.remove_vertices(v_ids)
		self.assertEqual(self.g.num_vertices(), 0)


if __name__ == '__main__':
	unittest.main()
