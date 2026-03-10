import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGEType(unittest.TestCase):

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

	def test_type_default_boundary(self):
		"""type should return BOUNDARY for vertices created by add_vertices."""
		(v0,) = self.g.add_vertices(1)
		self.assertEqual(self.g.type(v0), VertexType.BOUNDARY)

	def test_type_legacy_ty_string_fallback(self):
		"""type should fall back to legacy string field n.ty when n.t is absent."""
		(v0,) = self.g.add_vertices(1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.ty = 'X'
				REMOVE n.t
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.assertEqual(self.g.type(v0), VertexType.X)

	def test_type_missing_vertex_raises_keyerror(self):
		"""type should raise KeyError for a non-existent vertex."""
		with self.assertRaises(KeyError):
			self.g.type(999999)


if __name__ == '__main__':
	unittest.main()
