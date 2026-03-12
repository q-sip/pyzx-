import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType, EdgeType


class TestGraphAGERemoveIsolatedVertices(unittest.TestCase):

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

	def test_remove_single_isolated_non_boundary_vertex(self):
		self.g.add_vertex(VertexType.Z)
		self.assertEqual(self.g.num_vertices(), 1)
		self.assertEqual(self.g.num_edges(), 0)

		self.g.remove_isolated_vertices()
		self.assertEqual(self.g.num_vertices(), 0)

	def test_isolated_boundary_vertex_raises(self):
		self.g.add_vertex(VertexType.BOUNDARY)
		self.assertEqual(self.g.num_vertices(), 1)

		with self.assertRaises(TypeError):
			self.g.remove_isolated_vertices()

		self.assertEqual(self.g.num_vertices(), 1)

	def test_remove_isolated_pair_degree1_each(self):
		v0 = self.g.add_vertex(VertexType.Z)
		v1 = self.g.add_vertex(VertexType.Z)
		self.g.add_edge((v0, v1), EdgeType.SIMPLE)

		self.assertEqual(self.g.num_vertices(), 2)
		self.assertEqual(self.g.num_edges(), 1)

		self.g.remove_isolated_vertices()
		self.assertEqual(self.g.num_vertices(), 0)
		self.assertEqual(self.g.num_edges(), 0)

	def test_does_not_remove_connected_component(self):
		v0 = self.g.add_vertex(VertexType.Z)
		v1 = self.g.add_vertex(VertexType.X)
		v2 = self.g.add_vertex(VertexType.Z)
		self.g.add_edge((v0, v1), EdgeType.SIMPLE)
		self.g.add_edge((v1, v2), EdgeType.SIMPLE)

		self.assertEqual(self.g.num_vertices(), 3)
		self.assertEqual(self.g.num_edges(), 2)

		self.g.remove_isolated_vertices()

		self.assertEqual(self.g.num_vertices(), 3)
		self.assertEqual(self.g.num_edges(), 2)


if __name__ == '__main__':
	unittest.main()
