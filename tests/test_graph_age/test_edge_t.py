import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEEdgeT(unittest.TestCase):

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

	def test_edge_t_returns_second_element(self):
		"""edge_t should return the second element of the edge tuple."""
		v0, v1 = self.g.add_vertices(2)
		edge = (v0, v1)
		
		result = self.g.edge_t(edge)
		self.assertEqual(result, v1)

	def test_edge_t_with_canonicalized_edge(self):
		"""edge_t should work with edges from edge() method."""
		v0, v1 = self.g.add_vertices(2)
		
		# Get canonicalized edge
		canonical_edge = self.g.edge(v0, v1)
		result = self.g.edge_t(canonical_edge)
		
		# Should return the larger ID (second element)
		self.assertEqual(result, max(v0, v1))

	def test_edge_t_with_reverse_edge(self):
		"""edge_t should return second element regardless of order."""
		v0, v1 = self.g.add_vertices(2)
		
		edge1 = (v0, v1)
		edge2 = (v1, v0)
		
		self.assertEqual(self.g.edge_t(edge1), v1)
		self.assertEqual(self.g.edge_t(edge2), v0)

	def test_edge_t_with_self_loop(self):
		"""edge_t should handle self-loop edges."""
		v = self.g.add_vertices(1)[0]
		edge = (v, v)
		
		result = self.g.edge_t(edge)
		self.assertEqual(result, v)

	def test_edge_t_consistency(self):
		"""edge_t should be consistent with edge_st."""
		v0, v1, v2 = self.g.add_vertices(3)
		
		edges = [
			self.g.edge(v0, v1),
			self.g.edge(v1, v2),
			self.g.edge(v0, v2)
		]
		
		for edge in edges:
			t = self.g.edge_t(edge)
			st = self.g.edge_st(edge)
			self.assertEqual(t, st[1])

	def test_edge_s_and_edge_t_together(self):
		"""edge_s and edge_t should reconstruct the edge."""
		v0, v1, v2 = self.g.add_vertices(3)
		
		edges = [
			(v0, v1),
			(v1, v2),
			(v2, v0)
		]
		
		for edge in edges:
			s = self.g.edge_s(edge)
			t = self.g.edge_t(edge)
			reconstructed = (s, t)
			self.assertEqual(reconstructed, edge)


if __name__ == '__main__':
	unittest.main()
