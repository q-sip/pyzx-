import os
import unittest
from unittest.mock import patch
import pyzx
from pyzx.graph.graph_memgraph import GraphMemgraph

if GraphMemgraph().verify_db_connection():
    class TestAllPyZXWithMemgraph(unittest.TestCase):
        def test_run_all_pyzx_tests_on_memgraph(self):
            repo_root = os.path.dirname(os.path.dirname(pyzx.__file__))
            tests_path = os.path.join(repo_root, 'tests')
            with patch('pyzx.graph.graph', return_value=GraphMemgraph()):
                loader = unittest.TestLoader()
                suite = loader.discover(start_dir=tests_path)
                unittest.TextTestRunner().run(suite)
else:
    class TestSkipperMemgraph(unittest.TestCase):
        # @unittest.skip("Memgraph connection failed, skipping memgraph tests")
        def test_memgraph_skipped(self):
            assert False, "Memgraph connection failed, skipping memgraph tests"
