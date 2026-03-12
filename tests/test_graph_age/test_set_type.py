import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGESetType(unittest.TestCase):

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

	def test_set_type_to_boundary(self):
		"""set_type should update a vertex type to BOUNDARY."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_type(v0, VertexType.BOUNDARY)
		self.assertEqual(self.g.type(v0), VertexType.BOUNDARY)

	def test_set_type_to_x(self):
		"""set_type should update a vertex type to X."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_type(v0, VertexType.X)
		self.assertEqual(self.g.type(v0), VertexType.X)

	def test_type_changes_after_set_type(self):
		"""type should change after set_type is called."""
		(v0,) = self.g.add_vertices(1)
		initial = self.g.type(v0)
		self.g.set_type(v0, VertexType.Z)
		self.assertNotEqual(self.g.type(v0), initial)
		self.assertEqual(self.g.type(v0), VertexType.Z)

	def test_set_type_missing_vertex_does_not_crash(self):
		"""set_type on a missing vertex should not raise."""
		self.g.set_type(999999, VertexType.X)


if __name__ == '__main__':
	unittest.main()
