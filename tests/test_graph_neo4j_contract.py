import unittest
from unittest.mock import patch

from pyzx.graph.graph_neo4j import GraphNeo4j
from tests.test_graph import TestGraphBasicMethods, TestGraphCircuitMethods, TestPhaseGadget, TestGraphSaveLoad

if GraphNeo4j().verify_db_connection():
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
else:
    class TestSkipperNeo4j(unittest.TestCase):
        @unittest.skip("Neo4j connection failed, skipping Neo4j tests")
        def test_neo4j_skipped(self):
            pass

if __name__ == '__main__':
    unittest.main()
