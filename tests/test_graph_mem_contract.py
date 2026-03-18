import os
import unittest
from unittest.mock import patch

from pyzx.graph.graph_memgraph import GraphMemgraph
from tests.test_graph import TestGraphBasicMethods, TestGraphCircuitMethods, TestPhaseGadget, TestGraphSaveLoad

if "mem" in os.getenv("BACKEND_NAME", ""):
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

if __name__ == '__main__':
    unittest.main()
