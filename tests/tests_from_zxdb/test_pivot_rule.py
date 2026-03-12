import pyzx as zx

from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase
from tests.tests_from_zxdb.helpers import (
    load_simple_graph,
    run_rule_on_backends,
    validate_structural_rule_results,
    _count_processed_records,
)
from pyzx.graph.memgraph_queries import ZXQueryStore


PIVOT_JSON = {
    "version": 2,
    "backend": "multigraph",
    "variable_types": {},
    "scalar": {"power2": 0, "phase": "0"},
    "inputs": [],
    "outputs": [],
    "edata": {},
    "auto_simplify": False,
    "vertices": [
        {"id": 0, "t": 0, "pos": [0.75, -2.5]},
        {"id": 1, "t": 1, "pos": [0.75, -1.5], "phase": "π/6"},
        {"id": 2, "t": 1, "pos": [4.0, -4.0], "phase": "7π/6"},
        {"id": 3, "t": 0, "pos": [-4.25, -4.5]},
        {"id": 4, "t": 0, "pos": [-4.25, -3.5]},
        {"id": 5, "t": 1, "pos": [-2.75, -3.5], "phase": "π/2"},
        {"id": 6, "t": 0, "pos": [5.0, -5.0]},
        {"id": 7, "t": 0, "pos": [0.75, 0.5]},
        {"id": 8, "t": 1, "pos": [-2.75, -5.5], "phase": "π/5"},
        {"id": 9, "t": 1, "pos": [-2.75, -4.5], "phase": "π/4"},
        {"id": 10, "t": 0, "pos": [0.75, -1.0]},
        {"id": 11, "t": 1, "pos": [4.0, -5.0], "phase": "π/2"},
        {"id": 12, "t": 1, "pos": [2.25, -4.5], "phase": "π"},
        {"id": 13, "t": 1, "pos": [0.75, -3.0], "phase": "π/2"},
        {"id": 14, "t": 1, "pos": [-0.75, -4.5], "phase": "π"},
        {"id": 15, "t": 0, "pos": [-4.25, -5.5]},
        {"id": 16, "t": 1, "pos": [0.75, 0.0], "phase": "π/2"},
        {"id": 17, "t": 0, "pos": [5.0, -4.0]},
        {"id": 18, "t": 1, "pos": [0.75, 1.5], "phase": "3π/2"},
        {"id": 19, "t": 0, "pos": [0.75, 2.0]},
        {"id": 20, "t": 1, "pos": [4.0, -3.0], "phase": "π/5"},
        {"id": 21, "t": 0, "pos": [5.0, -3.0]},
    ],
    "edges": [
        [0, 13, 1],
        [1, 10, 1],
        [1, 12, 2],
        [1, 14, 2],
        [2, 17, 1],
        [2, 12, 2],
        [3, 9, 1],
        [4, 5, 1],
        [5, 14, 2],
        [6, 11, 1],
        [7, 16, 1],
        [8, 15, 1],
        [8, 14, 2],
        [9, 14, 2],
        [11, 12, 2],
        [12, 13, 2],
        [12, 16, 2],
        [12, 14, 2],
        [12, 18, 2],
        [12, 20, 2],
        [13, 14, 2],
        [14, 16, 2],
        [14, 18, 2],
        [18, 19, 1],
        [20, 21, 1],
    ],
}


def make_pivot_fixture() -> zx.Graph:
    return zx.Graph().from_json(PIVOT_JSON)


class TestPivotRule(MemgraphUnitTestCase):
    def test_pivot_rule(self):
        pyzx_graph = make_pivot_fixture()
        load_simple_graph(pyzx_graph, self.g)

        query_store = ZXQueryStore()

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.pivot_simp,
            db_query=[
                query_store._pivot_rule_single_interior_pauli(),
                query_store._pivot_rule_two_interior_pauli(),
            ],
            pyzx_name="pyzx_pivot_simp",
            db_name="memgraph_pivot_rule",
            print_results=True,
        )

        processed = _count_processed_records(run.db.return_value)
        self.assertGreater(processed, 0, "DB pivot rule did not fire")

        report = validate_structural_rule_results(
            original_graph=run.original_graph,
            pyzx_graph_after=run.pyzx.graph_after,
            db_graph_after=run.db.graph_after,
            check_boundary_counts=True,
            require_changed=True,
            print_results=False,
        )

        self.assertTrue(report["db_vs_pyzx_structural"])
