import os
import unittest
from unittest.mock import patch
import pyzx
from pyzx_db_addon.graph_AGE import GraphAGE


TEST_DIRS = (
    "test_graph_age",
    "test_graph_neo4j",
    "test_simple_backend",
    "tests_from_zxdb",
)


if GraphAGE().verify_db_connection():
    class TestAllPyZXWithAge(unittest.TestCase):
        def test_run_all_pyzx_tests_on_age(self):
            repo_root = os.path.dirname(os.path.dirname(pyzx.__file__))
            tests_path = os.path.join(repo_root, "tests")
            with patch("pyzx.graph.graph", return_value=GraphAGE()):
                loader = unittest.TestLoader()
                suite = unittest.TestSuite()
                for test_dir in TEST_DIRS:
                    suite.addTests(loader.discover(start_dir=os.path.join(tests_path, test_dir)))
                unittest.TextTestRunner().run(suite)
else:
    class TestSkipperMemgraph(unittest.TestCase):
        # @unittest.skip("Age connection failed, skipping age tests")
        def test_age_skipped(self):
            assert False, "Age connection failed, skipping age tests"
