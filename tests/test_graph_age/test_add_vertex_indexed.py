import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGEAddVertexIndexed(unittest.TestCase):

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

	def test_add_vertex_indexed_creates_with_defaults(self):
		self.g.add_vertex_indexed(5)

		self.assertIn(5, set(self.g.vertices()))
		self.assertEqual(self.g.type(5), VertexType.BOUNDARY)
		self.assertEqual(self.g.phase(5), Fraction(0))
		self.assertEqual(self.g.qubit(5), -1)
		self.assertEqual(self.g.row(5), -1)

	def test_add_vertex_indexed_updates_vindex(self):
		self.assertEqual(self.g.vindex(), 0)
		self.g.add_vertex_indexed(5)
		self.assertEqual(self.g.vindex(), 6)

		self.g.add_vertex_indexed(2)
		self.assertEqual(self.g.vindex(), 6)

	def test_add_vertex_indexed_raises_if_taken(self):
		self.g.add_vertex_indexed(3)
		with self.assertRaises(ValueError):
			self.g.add_vertex_indexed(3)


if __name__ == '__main__':
	unittest.main()
