import unittest
from unittest.mock import patch

from pyzx.graph.graph_memgraph import GraphMemgraph
from tests.test_graph import TestGraphBasicMethods, TestGraphCircuitMethods, TestPhaseGadget, TestGraphSaveLoad


if GraphMemgraph().verify_db_connection():
    class TestGraphBasicMethodsMemgraph(TestGraphBasicMethods):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphMemgraph)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()


    class TestGraphCircuitMethodsMemgraph(TestGraphCircuitMethods):

        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphMemgraph)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()


    class TestGraphSaveLoadMemgraph(TestGraphSaveLoad):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphMemgraph)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()


    class TestPhaseGadgetMemgraph(TestPhaseGadget):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphMemgraph)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()
else:
    class TestSkipperMemgraph(unittest.TestCase):
        @unittest.skip("Memgraph connection failed, skipping memgraph tests")
        def test_memgraph_skipped(self):
            pass

if __name__ == '__main__':
    unittest.main()
