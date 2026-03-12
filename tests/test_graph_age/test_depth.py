import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEDepth(unittest.TestCase):

	def _set_row(self, vertex_id, row_value):
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {vertex_id}}})
				SET n.row = {row_value}
				RETURN count(n)
			$$) AS (result agtype);
			"""
		)

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

	def test_depth_empty_graph(self):
		"""Empty graph should report depth -1."""
		self.assertEqual(self.g.depth(), -1)

	def test_depth_with_default_rows(self):
		"""Vertices created with default row=-1 should still report depth -1."""
		self.g.add_vertices(4)
		self.assertEqual(self.g.depth(), -1)

	def test_depth_with_non_negative_rows(self):
		"""Depth should be max non-negative row among nodes."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._set_row(v0, 0)
		self._set_row(v1, 5)
		self._set_row(v2, 2)

		self.assertEqual(self.g.depth(), 5)

	def test_depth_ignores_negative_rows(self):
		"""Depth should ignore negative rows when non-negative rows exist."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._set_row(v0, -3)
		self._set_row(v1, 4)
		self._set_row(v2, -1)

		self.assertEqual(self.g.depth(), 4)

	def test_depth_updates_after_vertex_removal(self):
		"""Depth should update after removing highest-row vertex."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._set_row(v0, 1)
		self._set_row(v1, 7)
		self._set_row(v2, 3)
		self.assertEqual(self.g.depth(), 7)

		self.g.remove_vertices([v1])
		self.assertEqual(self.g.depth(), 3)


if __name__ == '__main__':
	unittest.main()
