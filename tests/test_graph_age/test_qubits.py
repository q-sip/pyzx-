import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEQubits(unittest.TestCase):

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

	def test_qubits_empty_graph(self):
		"""qubits should return an empty mapping for an empty graph."""
		self.assertEqual(self.g.qubits(), {})

	def test_qubits_default_is_minus_one(self):
		"""qubits should return -1 for all freshly added vertices."""
		v0, v1 = self.g.add_vertices(2)
		result = self.g.qubits()
		self.assertEqual(result[v0], -1)
		self.assertEqual(result[v1], -1)

	def test_qubits_contains_all_vertices(self):
		"""qubits should contain an entry for every vertex in the graph."""
		vertices = self.g.add_vertices(3)
		result = self.g.qubits()
		self.assertEqual(set(result.keys()), set(vertices))

	def test_qubits_reflects_stored_values(self):
		"""qubits should return the correct value for vertices with assigned qubits."""
		(v0, v1) = self.g.add_vertices(2)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.qubit = 2
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v1}}})
				SET n.qubit = 5
				RETURN n
			$$) AS (n agtype);
			"""
		)
		result = self.g.qubits()
		self.assertEqual(result[v0], 2)
		self.assertEqual(result[v1], 5)


if __name__ == '__main__':
	unittest.main()
