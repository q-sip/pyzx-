import os
import unittest
from unittest.mock import patch
import pyzx
from pyzx.graph.graph_neo4j import GraphNeo4j

if GraphNeo4j().verify_db_connection():
    class TestAllPyZXWithNeo4j(unittest.TestCase):
        def test_run_all_pyzx_tests_on_neo4j(self):
            repo_root = os.path.dirname(os.path.dirname(pyzx.__file__))
            tests_path = os.path.join(repo_root, 'tests')
            with patch('pyzx.graph.graph', return_value=GraphNeo4j()):
                loader = unittest.TestLoader()
                suite = loader.discover(start_dir=tests_path)
                unittest.TextTestRunner().run(suite)
else:
    class TestSkipperNeo4j(unittest.TestCase):
        # @unittest.skip("Neo4j connection failed, skipping Neo4j tests")
        def test_neo4j_skipped(self):
            assert False, "Neo4j connection failed, skipping Neo4j tests"
