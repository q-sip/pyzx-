import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEPhase(unittest.TestCase):

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

	def test_phase_default_is_zero(self):
		"""phase should return Fraction(0) for a freshly added vertex."""
		(v0,) = self.g.add_vertices(1)
		self.assertEqual(self.g.phase(v0), Fraction(0))

	def test_phase_stored_as_fraction_string(self):
		"""phase should return the correct Fraction when stored as a fraction string."""
		(v0,) = self.g.add_vertices(1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.phase = '1/2'
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.assertEqual(self.g.phase(v0), Fraction(1, 2))

	def test_phase_stored_as_integer_string(self):
		"""phase should return Fraction(1) when stored as integer string '1'."""
		(v0,) = self.g.add_vertices(1)
		self.g.db_execute(
			f"""
			SELECT * FROM ag_catalog.cypher('{self.g.graph_id}', $$
				MATCH (n:Node {{id: {v0}}})
				SET n.phase = '1'
				RETURN n
			$$) AS (n agtype);
			"""
		)
		self.assertEqual(self.g.phase(v0), Fraction(1))

	def test_phase_missing_vertex_returns_zero(self):
		"""phase should return Fraction(0) for a non-existent vertex."""
		result = self.g.phase(999999)
		self.assertEqual(result, Fraction(0))


if __name__ == '__main__':
	unittest.main()
