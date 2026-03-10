import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGEVindex(unittest.TestCase):

	def setUp(self):
		try:
			self.g = GraphAGE()
			self.g.delete_graph()
			self.g.close()
			self.g = GraphAGE()
		except Exception as e:
			self.skipTest(f"AGE database not available: {e}")

	def tearDown(self):
		try:
			if hasattr(self, 'g'):
				self.g.delete_graph()
				self.g.close()
		except Exception:
			pass

	def test_vindex_starts_at_zero(self):
		self.assertEqual(self.g.vindex(), 0)

	def test_vindex_after_add_vertices(self):
		self.g.add_vertices(3)
		self.assertEqual(self.g.vindex(), 3)

	def test_vindex_after_add_vertex(self):
		initial = self.g.vindex()
		self.g.add_vertex(VertexType.Z)
		self.assertEqual(self.g.vindex(), initial + 1)


if __name__ == '__main__':
	unittest.main()
