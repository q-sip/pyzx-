import unittest
import sys

if __name__ == '__main__':
	sys.path.append('../..')
	sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGESetRow(unittest.TestCase):

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

	def test_set_row_basic(self):
		"""set_row should store the value and row() should return it."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_row(v0, 2)
		self.assertEqual(self.g.row(v0), 2)

	def test_set_row_zero(self):
		"""set_row with 0 should store 0."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_row(v0, 0)
		self.assertEqual(self.g.row(v0), 0)

	def test_set_row_float(self):
		"""set_row with a float should store and return the float."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_row(v0, 1.5)
		self.assertEqual(self.g.row(v0), 1.5)

	def test_set_row_overwrite(self):
		"""set_row called twice should overwrite the previous value."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_row(v0, 3)
		self.g.set_row(v0, 7)
		self.assertEqual(self.g.row(v0), 7)

	def test_set_row_negative(self):
		"""set_row with -1 should store -1."""
		(v0,) = self.g.add_vertices(1)
		self.g.set_row(v0, 4)
		self.g.set_row(v0, -1)
		self.assertEqual(self.g.row(v0), -1)


if __name__ == '__main__':
	unittest.main()
