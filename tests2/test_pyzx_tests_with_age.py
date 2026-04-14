import os
import unittest
from unittest.mock import patch
import pyzx
from pyzx.graph.graph_AGE import GraphAGE

if GraphAGE().verify_db_connection():
    class TestAllPyZXWithAge(unittest.TestCase):
        def test_run_all_pyzx_tests_on_age(self):
            repo_root = os.path.dirname(os.path.dirname(pyzx.__file__))
            tests_path = os.path.join(repo_root, 'tests')
            with patch('pyzx.graph.graph', return_value=GraphAGE()):
                loader = unittest.TestLoader()
                suite = loader.discover(start_dir=tests_path)
                unittest.TextTestRunner().run(suite)
else:
    class TestSkipperMemgraph(unittest.TestCase):
        # @unittest.skip("Age connection failed, skipping age tests")
        def test_age_skipped(self):
            assert False, "Age connection failed, skipping age tests"
