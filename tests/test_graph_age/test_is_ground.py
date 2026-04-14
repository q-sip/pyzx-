import unittest
import sys

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEIsGround(unittest.TestCase):

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

    def test_is_ground_default_false(self):
        """New vertex ground should be false"""
        (v0,) = self.g.add_vertices(1)

        self.assertEqual(self.g.is_ground(v0), False)

    def test_is_ground_true_after_set_ground_true(self):
        """Is_ground should return true when vertex is grounded """
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)

        self.assertEqual(self.g.is_ground(v0), True)

    def test_is_ground_false_after_unset(self):
        """Is_ground should return false when vertex is unset """
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)
        self.g.set_ground(v0, False)

        self.assertEqual(self.g.is_ground(v0), False)

    def test_is_ground_independent_per_vertex(self):
        """Ground state should be independent per vertex."""
        v0, v1 = self.g.add_vertices(2)
        self.g.set_ground(v0, True)

        self.assertEqual(self.g.is_ground(v0), True)
        self.assertEqual(self.g.is_ground(v1), False)

    def test_is_ground_consistent_with_grounds_query(self):
        """Is_ground result should be consistent with grounds"""
        v0, v1 = self.g.add_vertices(2)
        self.g.set_ground(v0, True)
        self.g.set_ground(v1, False)

        grounded = self.g.grounds()
        self.assertEqual(self.g.is_ground(v0), True)
        self.assertEqual(self.g.is_ground(v1), False)
        self.assertIn(v0, grounded)
        self.assertNotIn(v1, grounded)

if __name__ == '__main__':
    unittest.main()
