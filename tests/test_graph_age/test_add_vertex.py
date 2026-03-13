import unittest
import sys

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType


class TestGraphAGEAddVertex(unittest.TestCase):

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

    def test_add_vertex_with_enum_type(self):
        v = self.g.add_vertex(VertexType.Z, qubit=1, row=2)
        self.assertEqual(v, 0)
        self.assertEqual(self.g.type(v), VertexType.Z)
        self.assertEqual(self.g.qubit(v), 1)
        self.assertEqual(self.g.row(v), 2)

    def test_add_vertex_accepts_int_type_positional(self):
        v = self.g.add_vertex(0, 1, 2)
        self.assertEqual(v, 0)
        self.assertEqual(self.g.type(v), VertexType.BOUNDARY)
        self.assertEqual(self.g.qubit(v), 1)
        self.assertEqual(self.g.row(v), 2)

    def test_add_vertex_invalid_int_type_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            self.g.add_vertex(999, 1, 2)
        self.assertEqual(str(context.exception), "Invalid vertex type: 999")


if __name__ == '__main__':
    unittest.main()
