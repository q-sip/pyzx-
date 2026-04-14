import unittest
import sys

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE


class TestGraphAGEGetVerticesGetEdges(unittest.TestCase):

    def setUp(self):
        try:
            self.g = GraphAGE()
            self.g.delete_graph()
            self.g.close()
            self.g = GraphAGE()
        except Exception as e:
            self.skipTest(f"AGE database not available: {e}")

    def tearDown(self):
        try:
            if hasattr(self, 'g'):
                self.g.delete_graph()
                self.g.close()
        except Exception:
            pass

    def test_get_vertices_empty_graph(self):
        self.assertEqual(self.g.get_vertices(), [])

    def test_get_vertices_after_add_vertices(self):
        vs = self.g.add_vertices(3)
        self.assertEqual(self.g.get_vertices(), vs)

    def test_get_edges_empty_graph(self):
        self.assertEqual(self.g.get_edges(), [])

    def test_get_edges_after_add_edges(self):
        v0, v1, v2 = self.g.add_vertices(3)
        self.g.add_edge((v0, v1))
        self.g.add_edge((v1, v2))

        edges = self.g.get_edges()
        self.assertEqual(set(edges), {(v0, v1), (v1, v2)})


if __name__ == '__main__':
    unittest.main()
