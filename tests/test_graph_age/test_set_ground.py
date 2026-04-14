import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGESetGround(unittest.TestCase):

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

    def test_set_ground_marks_vertex(self):
        """set_ground should mark the vertex as ground and is_ground should return True."""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)
        self.assertEqual(self.g.is_ground(v0), True)

    def test_set_ground_unmark(self):
        """set_ground should mark the vertex as not ground and is_ground should return False."""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, False)
        self.assertEqual(self.g.is_ground(v0), False)

    def test_set_ground_default_false(self):
        """By default, vertices should not be ground."""
        (v0,) = self.g.add_vertices(1)
        self.assertEqual(self.g.is_ground(v0), False)

    def test_set_ground_overwrite(self):
        """set_ground should overwrite previous ground status."""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)
        self.assertEqual(self.g.is_ground(v0), True)

        self.g.set_ground(v0, False)
        self.assertEqual(self.g.is_ground(v0), False)

    def test_set_ground_json_roundtrip(self):
        """set_ground status should be preserved through JSON serialization."""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)

        json_data = self.g.to_json()
        g2 = GraphAGE.from_json(json_data)

        self.assertEqual(g2.is_ground(v0), True)

if __name__ == '__main__':
    unittest.main()
