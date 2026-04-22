import unittest
import sys
from fractions import Fraction

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx_db_addon.graph_AGE import GraphAGE


class TestGraphAGEGrounds(unittest.TestCase):

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

    def test_grounds_empty_graph(self):
        """Empty graph should have no grounds."""
        self.assertEqual(self.g.grounds(), [])

    def test_grounds_returns_only_grounded_vertices(self):
        """Grounds should only return grounded vertices"""
        v0, v1, v2 = self.g.add_vertices(3)
        self.g.set_ground(v1, True)
        self.g.set_ground(v2, True)

        self.assertEqual(self.g.grounds(), [v1, v2])

    def test_grounds_update_after_unset(self):
        """Grounds should not return previously grounded vertices"""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)
        self.g.set_ground(v0, False)

        self.assertEqual(self.g.grounds(), [])

    def test_grounds_idempotent_marking(self):
        """Grounds should not return duplicates"""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)
        self.g.set_ground(v0, True)
        self.g.set_ground(v0, True)
        
        self.assertEqual(self.g.grounds(), [v0])

    def test_grounds_after_vertex_deletion(self):
        """Ground marking should be removed when vertex is deleted"""
        (v0,) = self.g.add_vertices(1)
        self.g.set_ground(v0, True)
        self.g.remove_vertex(v0)

        self.assertEqual(self.g.grounds(), [])

if __name__ == '__main__':
    unittest.main()
