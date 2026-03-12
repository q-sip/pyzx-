# tests/test_graph_age/test_add_vertices.py
import unittest
import io

from pyzx.graph.graph_AGE import GraphAGE


stream = io.StringIO()

class TestGraphAGEAddVertices(unittest.TestCase):

    def test_correct_ids(self):
        g = GraphAGE()
        returns = g.add_vertices(3)
        expected =  [0, 1, 2]
        self.assertEqual(expected, returns)
    
    def test_zero_vertices(self):
        g = GraphAGE()
        returns = g.add_vertices(0)
        expected = []
        self.assertEqual(expected, returns)

    def test_negative_vertices(self):
        g = GraphAGE()
        with self.assertRaises(ValueError) as context:
            g.add_vertices(-1)
        expected = "Amount of vertices added must be >= 0"
        self.assertEqual(expected, str(context.exception))
    


