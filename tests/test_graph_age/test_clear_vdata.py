import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx_db_addon.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGEClearVData(unittest.TestCase):

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

	def test_clear_vdata_removes_custom_properties(self):
		"""clear_vdata should remove vertex custom properties."""
		v = self.g.add_vertex(VertexType.Z)
		self.g.set_vdata(v, 'label', 'hello')
		self.assertEqual(self.g.vdata(v, 'label', 'fallback'), 'hello')

		self.g.clear_vdata(v)
		self.assertEqual(self.g.vdata(v, 'label', 'fallback'), 'fallback')

	def test_clear_vdata_preserves_vertex_type(self):
		"""clear_vdata should preserve vertex type t."""
		v = self.g.add_vertex(VertexType.H_BOX)
		self.g.set_vdata(v, 'label', 'hello')
		self.g.set_vdata(v, 'color', 'blue')

		self.g.clear_vdata(v)
		self.assertEqual(self.g.type(v), VertexType.H_BOX)
		self.assertNotIn('label', set(self.g.vdata_keys(v)))
		self.assertNotIn('color', set(self.g.vdata_keys(v)))

	def test_clear_vdata_preserves_core_node_fields(self):
		"""clear_vdata should preserve phase/qubit/row values used by compose and tensor semantics."""
		v = self.g.add_vertex(VertexType.Z, qubit=2, row=3, phase=Fraction(1, 2))
		self.g.set_vdata(v, 'label', 'hello')
		self.g.set_vdata(v, 'color', 'blue')

		self.g.clear_vdata(v)

		self.assertEqual(self.g.type(v), VertexType.Z)
		self.assertEqual(self.g.phase(v), Fraction(1, 2))
		self.assertEqual(self.g.qubit(v), 2)
		self.assertEqual(self.g.row(v), 3)
		self.assertNotIn('label', set(self.g.vdata_keys(v)))
		self.assertNotIn('color', set(self.g.vdata_keys(v)))

	def test_clear_vdata_missing_vertex_does_not_crash(self):
		"""clear_vdata on a missing vertex should not raise."""
		self.g.clear_vdata(999)
		self.assertEqual(self.g.vdata(999, 'label', 'fallback'), 'fallback')



if __name__ == '__main__':
	unittest.main()
