import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEIncidentEdges(unittest.TestCase):

	def _create_edge(self, v0, v1):
		"""Helper to create an edge between two vertices using raw Cypher."""
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (a:Node {{id: {v0}}}), (b:Node {{id: {v1}}})
				CREATE (a)-[:Wire]->(b)
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

	def test_incident_edges_empty_graph(self):
		"""incident_edges should return empty list when vertex has no edges."""
		edges = self.g.incident_edges(0)
		self.assertEqual(len(edges), 0)
		self.assertIsInstance(edges, list)

	def test_incident_edges_isolated_vertex(self):
		"""Isolated vertex should return empty list."""
		v = self.g.add_vertices(1)[0]
		edges = self.g.incident_edges(v)
		self.assertEqual(len(edges), 0)

	def test_incident_edges_single_edge(self):
		"""incident_edges should return the edge for endpoint."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		
		edges_v0 = self.g.incident_edges(v0)
		edges_v1 = self.g.incident_edges(v1)
		
		self.assertEqual(len(edges_v0), 1)
		self.assertEqual(len(edges_v1), 1)
		
		# Each edge should be a tuple with both vertex IDs
		self.assertIn(v1, edges_v0[0])
		self.assertIn(v0, edges_v0[0])
		self.assertIn(v0, edges_v1[0])
		self.assertIn(v1, edges_v1[0])

	def test_incident_edges_multiple_edges(self):
		"""incident_edges should return all incident edges."""
		v0, v1, v2, v3 = self.g.add_vertices(4)
		self._create_edge(v0, v1)
		self._create_edge(v0, v2)
		self._create_edge(v0, v3)
		
		edges = self.g.incident_edges(v0)
		self.assertEqual(len(edges), 3)
		
		# All edges should contain v0
		for edge in edges:
			self.assertIn(v0, edge)

	def test_incident_edges_parallel_edges(self):
		"""incident_edges should return all parallel edges separately."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		self._create_edge(v0, v1)
		
		edges_v0 = self.g.incident_edges(v0)
		edges_v1 = self.g.incident_edges(v1)
		
		# Both should have 2 incident edges
		self.assertEqual(len(edges_v0), 2)
		self.assertEqual(len(edges_v1), 2)

	def test_incident_edges_after_remove(self):
		"""incident_edges should update after removing edges."""
		v0, v1, v2 = self.g.add_vertices(3)
		self._create_edge(v0, v1)
		self._create_edge(v0, v2)
		
		self.assertEqual(len(self.g.incident_edges(v0)), 2)
		
		self.g.remove_edges([(v0, v1)])
		edges = self.g.incident_edges(v0)
		
		self.assertEqual(len(edges), 1)
		self.assertIn(v2, edges[0])

	def test_incident_edges_returns_tuples(self):
		"""incident_edges should return list of tuples."""
		v0, v1 = self.g.add_vertices(2)
		self._create_edge(v0, v1)
		
		edges = self.g.incident_edges(v0)
		self.assertIsInstance(edges, list)
		self.assertIsInstance(edges[0], tuple)
		self.assertEqual(len(edges[0]), 2)


if __name__ == '__main__':
	unittest.main()
