import os
import sys
import unittest
from unittest.mock import patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
PYZX_GRAPH_ROOT = os.path.join(REPO_ROOT, "pyzx", "graph")
for p in (REPO_ROOT, PYZX_GRAPH_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from zxdb_age.zxdb_age import ZXdbAge


class TestLocalComplementation(unittest.TestCase):
    def setUp(self):
        self.zxdb = ZXdbAge(graph_id="test_graph")

    def tearDown(self):
        self.zxdb.close()

    def test_local_complementation_runs_until_no_pattern(self):
        execute_results = [
            [(2,)],
            [(1,)],
            [(0,)],
        ]
        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", side_effect=execute_results
        ) as mock_exec:
            out = self.zxdb.local_complementation_rule()
            self.assertEqual(out, 3)
            self.assertEqual(mock_exec.call_count, 3)
            self.assertEqual(
                [c.args[0] for c in mock_exec.call_args_list],
                ["Local complementation age", "Local complementation age", "Local complementation age"],
            )
            self.assertEqual(
                [c.kwargs.get("return_signature") for c in mock_exec.call_args_list],
                ["rewritten agtype", "rewritten agtype", "rewritten agtype"],
            )

    def test_local_complementation_stops_immediately_when_no_pattern(self):
        with patch.object(self.zxdb, "_get_named_query", side_effect=lambda t: t), patch.object(
            self.zxdb, "_execute_cypher", return_value=[(0,)]
        ) as mock_exec:
            out = self.zxdb.local_complementation_rule()
            self.assertEqual(out, 0)
            mock_exec.assert_called_once_with("Local complementation age", return_signature="rewritten agtype")

if __name__ == "__main__":
    unittest.main()
