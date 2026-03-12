import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEVertices(unittest.TestCase):

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

	def test_vertices_empty_graph(self):
		"""Empty graph should return empty list."""
		vertices = self.g.vertices()
		self.assertEqual(len(vertices), 0)
		self.assertIsInstance(vertices, list)

	def test_vertices_after_add_vertices(self):
		"""vertices() should return all vertex IDs after adding vertices."""
		v_ids = self.g.add_vertices(3)
		vertices = self.g.vertices()
		
		self.assertEqual(len(vertices), 3)
		self.assertEqual(set(vertices), set(v_ids))

	def test_vertices_returns_correct_ids(self):
		"""vertices() should return the exact IDs that were added."""
		v0 = self.g.add_vertices(1)[0]
		v1 = self.g.add_vertices(1)[0]
		v2 = self.g.add_vertices(1)[0]
		
		vertices = self.g.vertices()
		self.assertEqual(len(vertices), 3)
		self.assertIn(v0, vertices)
		self.assertIn(v1, vertices)
		self.assertIn(v2, vertices)

	def test_vertices_after_remove_vertices(self):
		"""vertices() should reflect removed vertices."""
		v_ids = self.g.add_vertices(5)
		self.assertEqual(len(self.g.vertices()), 5)
		
		# Remove some vertices
		self.g.remove_vertices([v_ids[1], v_ids[3]])
		vertices = self.g.vertices()
		
		self.assertEqual(len(vertices), 3)
		self.assertIn(v_ids[0], vertices)
		self.assertNotIn(v_ids[1], vertices)
		self.assertIn(v_ids[2], vertices)
		self.assertNotIn(v_ids[3], vertices)
		self.assertIn(v_ids[4], vertices)

	def test_vertices_after_remove_all(self):
		"""vertices() should return empty list after removing all vertices."""
		v_ids = self.g.add_vertices(4)
		self.assertEqual(len(self.g.vertices()), 4)
		
		self.g.remove_vertices(v_ids)
		vertices = self.g.vertices()
		
		self.assertEqual(len(vertices), 0)


if __name__ == '__main__':
	unittest.main()
