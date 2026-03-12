import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEEdgeSt(unittest.TestCase):

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

	def test_edge_st_returns_edge_unchanged(self):
		"""edge_st(edge) should return the edge tuple unchanged."""
		v0, v1 = self.g.add_vertices(2)
		edge = (v0, v1)
		
		result = self.g.edge_st(edge)
		self.assertEqual(result, edge)

	def test_edge_st_with_canonicalized_edge(self):
		"""edge_st should work with canonicalized edges from edge() method."""
		v0, v1 = self.g.add_vertices(2)
		
		# Get canonicalized edge from edge() method
		canonical_edge = self.g.edge(v0, v1)
		result = self.g.edge_st(canonical_edge)
		
		self.assertEqual(result, canonical_edge)
		self.assertEqual(result, (min(v0, v1), max(v0, v1)))

	def test_edge_st_with_reverse_order(self):
		"""edge_st should return tuple as-is regardless of vertex order."""
		v0, v1 = self.g.add_vertices(2)
		
		# Test with both orderings
		edge1 = (v0, v1)
		edge2 = (v1, v0)
		
		result1 = self.g.edge_st(edge1)
		result2 = self.g.edge_st(edge2)
		
		self.assertEqual(result1, edge1)
		self.assertEqual(result2, edge2)
		# They should be different unless v0 == v1
		if v0 != v1:
			self.assertNotEqual(result1, result2)

	def test_edge_st_consistency_with_edges_method(self):
		"""edge_st should work correctly with edges returned by edges() method."""
		v0, v1, v2 = self.g.add_vertices(3)
		
		# Create some edges (we'll just use the edge() method to get canonical form)
		edge1 = self.g.edge(v0, v1)
		edge2 = self.g.edge(v1, v2)
		
		# edge_st should return them unchanged
		self.assertEqual(self.g.edge_st(edge1), edge1)
		self.assertEqual(self.g.edge_st(edge2), edge2)

	def test_edge_st_returns_tuple(self):
		"""edge_st should return a tuple."""
		v0, v1 = self.g.add_vertices(2)
		edge = (v0, v1)
		
		result = self.g.edge_st(edge)
		self.assertIsInstance(result, tuple)
		self.assertEqual(len(result), 2)

	def test_edge_st_with_same_vertex(self):
		"""edge_st should handle self-loop edges."""
		v = self.g.add_vertices(1)[0]
		edge = (v, v)
		
		result = self.g.edge_st(edge)
		self.assertEqual(result, (v, v))


if __name__ == '__main__':
	unittest.main()
