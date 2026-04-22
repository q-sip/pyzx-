import unittest
import sys

if __name__ == '__main__':
    sys.path.append('../..')
    sys.path.append('.')

from pyzx_db_addon.graph_AGE import GraphAGE


class TestGraphAGEBatching(unittest.TestCase):

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

    def test_begin_batch_increments_depth(self):
        self.assertEqual(self.g._batch_depth, 0)
        self.g.begin_batch()
        self.assertEqual(self.g._batch_depth, 1)

    def test_end_batch_noop_when_not_batched(self):
        self.assertEqual(self.g._batch_depth, 0)
        self.g.end_batch()
        self.assertEqual(self.g._batch_depth, 0)

    def test_end_batch_reduces_nested_depth(self):
        self.g.begin_batch()
        self.g.begin_batch()
        self.assertEqual(self.g._batch_depth, 2)

        self.g.end_batch()
        self.assertEqual(self.g._batch_depth, 1)

        self.g.end_batch()
        self.assertEqual(self.g._batch_depth, 0)

    def test_rollback_batch_discards_batched_writes_and_resets_depth(self):
        self.assertEqual(self.g.num_vertices(), 0)

        self.g.begin_batch()
        self.g.add_vertices(2)
        self.assertEqual(self.g._batch_depth, 1)

        self.g.rollback_batch()

        self.assertEqual(self.g._batch_depth, 0)
        self.assertEqual(self.g.num_vertices(), 0)


if __name__ == '__main__':
    unittest.main()
