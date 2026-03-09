import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEEdge(unittest.TestCase):

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

	def test_edge_returns_canonicalized_tuple(self):
		"""edge(s, t) should return tuple with smaller ID first."""
		v0, v1 = self.g.add_vertices(2)
		
		# Regardless of order, should return (min, max)
		edge1 = self.g.edge(v0, v1)
		edge2 = self.g.edge(v1, v0)
		
		self.assertEqual(edge1, edge2)
		self.assertEqual(edge1, (min(v0, v1), max(v0, v1)))

	def test_edge_with_ascending_ids(self):
		"""edge(s, t) where s < t should return (s, t)."""
		v0, v1 = self.g.add_vertices(2)
		s, t = min(v0, v1), max(v0, v1)
		
		edge = self.g.edge(s, t)
		self.assertEqual(edge, (s, t))

	def test_edge_with_descending_ids(self):
		"""edge(s, t) where s > t should return (t, s)."""
		v0, v1 = self.g.add_vertices(2)
		s, t = max(v0, v1), min(v0, v1)
		
		edge = self.g.edge(s, t)
		self.assertEqual(edge, (t, s))

	def test_edge_same_vertex(self):
		"""edge(v, v) should return (v, v)."""
		v = self.g.add_vertices(1)[0]
		edge = self.g.edge(v, v)
		self.assertEqual(edge, (v, v))

	def test_edge_consistency_with_edges_method(self):
		"""edge(s, t) should match format returned by edges() method."""
		v0, v1, v2 = self.g.add_vertices(3)
		
		# The edge method should return canonicalized tuples
		# in the same format as edges() uses
		edge_01 = self.g.edge(v0, v1)
		edge_12 = self.g.edge(v1, v2)
		edge_02 = self.g.edge(v0, v2)
		
		# All should be tuples with smaller ID first
		self.assertEqual(edge_01[0], min(v0, v1))
		self.assertEqual(edge_01[1], max(v0, v1))
		self.assertEqual(edge_12[0], min(v1, v2))
		self.assertEqual(edge_12[1], max(v1, v2))
		self.assertEqual(edge_02[0], min(v0, v2))
		self.assertEqual(edge_02[1], max(v0, v2))


if __name__ == '__main__':
	unittest.main()
