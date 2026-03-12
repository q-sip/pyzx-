import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType, EdgeType


class TestGraphAGEIOAndClone(unittest.TestCase):

	def setUp(self):
		try:
			self.g = GraphAGE()
			self.g.delete_graph()
			self.g.close()
			self.g = GraphAGE()
		except Exception as e:
			self.skipTest(f"AGE database not available: {e}")
		self.clone_graph = None

	def tearDown(self):
		try:
			if self.clone_graph is not None:
				self.clone_graph.delete_graph()
				self.clone_graph.close()
			if hasattr(self, 'g'):
				self.g.delete_graph()
				self.g.close()
		except Exception:
			pass

	def test_set_get_inputs_outputs(self):
		v0 = self.g.add_vertex(VertexType.BOUNDARY)
		v1 = self.g.add_vertex(VertexType.Z)
		v2 = self.g.add_vertex(VertexType.BOUNDARY)
		self.g.add_edge((v0, v1), EdgeType.SIMPLE)
		self.g.add_edge((v1, v2), EdgeType.SIMPLE)

		self.g.set_inputs((v0,))
		self.g.set_outputs((v2,))

		self.assertEqual(self.g.inputs(), (v0,))
		self.assertEqual(self.g.outputs(), (v2,))

	def test_clone_preserves_structure_and_io(self):
		v0 = self.g.add_vertex(VertexType.BOUNDARY)
		v1 = self.g.add_vertex(VertexType.Z)
		v2 = self.g.add_vertex(VertexType.X)
		self.g.add_edge((v0, v1), EdgeType.SIMPLE)
		self.g.add_edge((v1, v2), EdgeType.HADAMARD)
		self.g.set_vdata(v1, 'label', 'mid')
		self.g.set_edata((v1, v2), 'weight', 7)
		self.g.set_inputs((v0,))
		self.g.set_outputs((v2,))

		self.clone_graph = self.g.clone()
		c = self.clone_graph

		self.assertEqual(set(c.vertices()), set(self.g.vertices()))
		self.assertEqual(set(c.edges()), set(self.g.edges()))
		self.assertEqual(c.type(v1), self.g.type(v1))
		self.assertEqual(c.edge_type((v1, v2)), self.g.edge_type((v1, v2)))
		self.assertEqual(c.vdata(v1, 'label'), 'mid')
		self.assertEqual(c.edata((v1, v2), 'weight'), 7)
		self.assertEqual(c.inputs(), (v0,))
		self.assertEqual(c.outputs(), (v2,))


if __name__ == '__main__':
	unittest.main()
