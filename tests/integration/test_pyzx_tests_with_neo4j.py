import os
import unittest
from unittest.mock import patch
import pyzx
from pyzx_db_addon.graph_neo4j import GraphNeo4j


TEST_DIRS = (
    "test_graph_age",
    "test_graph_neo4j",
    "test_simple_backend",
    "tests_from_zxdb",
)


if GraphNeo4j().verify_db_connection():
    class TestAllPyZXWithNeo4j(unittest.TestCase):
        def test_run_all_pyzx_tests_on_neo4j(self):
            repo_root = os.path.dirname(os.path.dirname(pyzx.__file__))
            tests_path = os.path.join(repo_root, "tests")
            with patch("pyzx.graph.graph", return_value=GraphNeo4j()):
                loader = unittest.TestLoader()
                suite = unittest.TestSuite()
                for test_dir in TEST_DIRS:
                    suite.addTests(loader.discover(start_dir=os.path.join(tests_path, test_dir)))
                unittest.TextTestRunner().run(suite)
else:
    class TestSkipperNeo4j(unittest.TestCase):
        # @unittest.skip("Neo4j connection failed, skipping Neo4j tests")
        def test_neo4j_skipped(self):
            assert False, "Neo4j connection failed, skipping Neo4j tests"
