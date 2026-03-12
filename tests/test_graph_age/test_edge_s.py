import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEEdgeS(unittest.TestCase):

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

	def test_edge_s_returns_first_element(self):
		"""edge_s should return the first element of the edge tuple."""
		v0, v1 = self.g.add_vertices(2)
		edge = (v0, v1)
		
		result = self.g.edge_s(edge)
		self.assertEqual(result, v0)

	def test_edge_s_with_canonicalized_edge(self):
		"""edge_s should work with edges from edge() method."""
		v0, v1 = self.g.add_vertices(2)
		
		# Get canonicalized edge
		canonical_edge = self.g.edge(v0, v1)
		result = self.g.edge_s(canonical_edge)
		
		# Should return the smaller ID (first element)
		self.assertEqual(result, min(v0, v1))

	def test_edge_s_with_reverse_edge(self):
		"""edge_s should return first element regardless of order."""
		v0, v1 = self.g.add_vertices(2)
		
		edge1 = (v0, v1)
		edge2 = (v1, v0)
		
		self.assertEqual(self.g.edge_s(edge1), v0)
		self.assertEqual(self.g.edge_s(edge2), v1)

	def test_edge_s_with_self_loop(self):
		"""edge_s should handle self-loop edges."""
		v = self.g.add_vertices(1)[0]
		edge = (v, v)
		
		result = self.g.edge_s(edge)
		self.assertEqual(result, v)

	def test_edge_s_consistency(self):
		"""edge_s should be consistent with edge_st."""
		v0, v1, v2 = self.g.add_vertices(3)
		
		edges = [
			self.g.edge(v0, v1),
			self.g.edge(v1, v2),
			self.g.edge(v0, v2)
		]
		
		for edge in edges:
			s = self.g.edge_s(edge)
			st = self.g.edge_st(edge)
			self.assertEqual(s, st[0])


if __name__ == '__main__':
	unittest.main()
