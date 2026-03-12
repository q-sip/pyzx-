import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGETypes(unittest.TestCase):

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

	def test_types_empty_graph(self):
		"""types should return empty mapping for empty graph."""
		self.assertEqual(self.g.types(), {})

	def test_types_default_boundary(self):
		"""types should map added vertices to BOUNDARY by default."""
		v0, v1, v2 = self.g.add_vertices(3)
		types_map = self.g.types()
		self.assertEqual(types_map[v0], VertexType.BOUNDARY)
		self.assertEqual(types_map[v1], VertexType.BOUNDARY)
		self.assertEqual(types_map[v2], VertexType.BOUNDARY)

	def test_types_legacy_ty_string_fallback(self):
		"""types should support legacy n.ty string when n.t is absent."""
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
		types_map = self.g.types()
		self.assertEqual(types_map[v0], VertexType.X)


if __name__ == '__main__':
	unittest.main()
