import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType


class TestGraphAGEEdgeType(unittest.TestCase):

	def _create_edge(self, v0, v1, edge_type_value=None):
		"""Helper to create an edge between two vertices using raw Cypher."""
		if edge_type_value is None:
			self.g.db_execute(
				f"""
				SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
					MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
					CREATE (a)-[:Wire]->(b)
					RETURN count(*)
				$$) AS (result agtype);
				"""
			)
			return

		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
				CREATE (a)-[:Wire {{t: {edge_type_value}}}]->(b)
				RETURN count(*)
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

	def test_edge_type_missing_edge_raises_keyerror(self):
		"""edge_type should raise KeyError when edge does not exist."""
		v0, v1 = self.g.add_vertices(2)
		with self.assertRaises(KeyError):
			self.g.edge_type((v0, v1))

	def test_edge_type_default_simple_when_property_missing(self):
		"""Edge without t property should default to SIMPLE."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self.assertEqual(self.g.edge_type((v0, v1)), EdgeType.SIMPLE)

	def test_edge_type_hadamard(self):
		"""edge_type should return HADAMARD when t is set accordingly."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1, EdgeType.HADAMARD.value)
		self.assertEqual(self.g.edge_type((v0, v1)), EdgeType.HADAMARD)


if __name__ == '__main__':
	unittest.main()
