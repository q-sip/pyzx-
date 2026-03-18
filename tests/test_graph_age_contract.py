import os
import unittest
from unittest.mock import patch

from pyzx.graph.graph_AGE import GraphAGE
from tests.test_graph import TestGraphBasicMethods, TestGraphCircuitMethods, TestPhaseGadget, TestGraphSaveLoad

if "age" in os.getenv("BACKEND_NAME", ""):
    import uuid
    
    class TestGraphBasicMethodsAge(TestGraphBasicMethods):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphAGE)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            # Clean up AGE graph and close connection
            if hasattr(self, 'graph') and isinstance(self.graph, GraphAGE):
                try:
                    self.graph.delete_graph()
                    self.graph.close()
                except Exception:
                    pass
            self.patcher.stop()


    class TestGraphCircuitMethodsAge(TestGraphCircuitMethods):

        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphAGE)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            # Clean up AGE graph and close connection
            if hasattr(self, 'graph') and isinstance(self.graph, GraphAGE):
                try:
                    self.graph.delete_graph()
                    self.graph.close()
                except Exception:
                    pass
            self.patcher.stop()


    class TestGraphSaveLoadAge(TestGraphSaveLoad):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphAGE)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            # Clean up AGE graph and close connection
            if hasattr(self, 'graph') and isinstance(self.graph, GraphAGE):
                try:
                    self.graph.delete_graph()
                    self.graph.close()
                except Exception:
                    pass
            self.patcher.stop()


    class TestPhaseGadgetAge(TestPhaseGadget):
        def setUp(self):
            self.patcher = patch('tests.test_graph.Graph', GraphAGE)
            self.patcher.start()
            super().setUp()

        def tearDown(self):
            super().tearDown()
            # Clean up AGE graph and close connection
            if hasattr(self, 'graph') and isinstance(self.graph, GraphAGE):
                try:
                    self.graph.delete_graph()
                    self.graph.close()
                except Exception:
                    pass
            self.patcher.stop()

if __name__ == '__main__':
    unittest.main()
