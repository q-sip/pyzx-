import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGESetPhase(unittest.TestCase):

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

	def test_set_phase_basic(self):
		"""set_phase should store the phase and phase() should return it."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_phase(v0, Fraction(1, 2))
		self.assertEqual(self.g.phase(v0), Fraction(1, 2))

	def test_set_phase_normalises_mod_2(self):
		"""set_phase should normalise the phase modulo 2."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_phase(v0, Fraction(5, 2))
		self.assertEqual(self.g.phase(v0), Fraction(1, 2))

	def test_set_phase_zero(self):
		"""set_phase with 0 should store Fraction(0)."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_phase(v0, Fraction(0))
		self.assertEqual(self.g.phase(v0), Fraction(0))

	def test_set_phase_integer(self):
		"""set_phase with integer 1 should normalise to 1 % 2 == 1."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_phase(v0, 1)
		self.assertEqual(self.g.phase(v0), Fraction(1))

	def test_set_phase_overwrite(self):
		"""set_phase called twice should overwrite the previous value."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_phase(v0, Fraction(3, 4))
		self.g.set_phase(v0, Fraction(1, 4))
		self.assertEqual(self.g.phase(v0), Fraction(1, 4))


if __name__ == '__main__':
	unittest.main()
