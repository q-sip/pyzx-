import os
import unittest
from unittest.mock import patch

from pyzx.graph.graph_neo4j import GraphNeo4j
from tests.test_graph import TestGraphBasicMethods, TestGraphCircuitMethods, TestPhaseGadget, TestGraphSaveLoad

if "mem" in os.getenv("neo4j", "") or True:
    class TestGraphBasicMethodsNeo4j(TestGraphBasicMethods):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphNeo4j)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()


    class TestGraphCircuitMethodsNeo4j(TestGraphCircuitMethods):

        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphNeo4j)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()


    class TestGraphSaveLoadNeo4j(TestGraphSaveLoad):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphNeo4j)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()


    class TestPhaseGadgetNeo4j(TestPhaseGadget):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphNeo4j)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            self.patcher.stop()

if __name__ == '__main__':
    unittest.main()
