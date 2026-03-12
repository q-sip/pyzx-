import pyzx as zx

from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase
from tests.tests_from_zxdb.helpers import (
    load_simple_graph,
    run_rule_on_backends,
    validate_structural_rule_results,
    assert_boundary_degrees_are_one
)
from pyzx.graph.memgraph_queries import ZXQueryStore


PIVOT_GADGET_JSON = {
    "version": 2,
    "backend": "multigraph",
    "variable_types": {},
    "scalar": {"power2": 0, "phase": "0"},
    "inputs": [4],
    "outputs": [14],
    "edata": {},
    "auto_simplify": False,
    "vertices": [
        {"id": 2, "t": 1, "pos": [3.25, -4.0], "phase": "π/4"},
        {"id": 4, "t": 0, "pos": [-3.25, -4.0]},
        {"id": 7, "t": 1, "pos": [-1.75, -4.0], "phase": "3π/2"},
        {"id": 8, "t": 1, "pos": [1.75, -2.25], "phase": "π/2"},
        {"id": 10, "t": 1, "pos": [5.25, -4.0], "phase": "7π/6"},
        {"id": 14, "t": 0, "pos": [6.25, -4.0]},
        {"id": 16, "t": 1, "pos": [0.25, -4.0], "phase": "π"},
        {"id": 17, "t": 0, "pos": [1.75, -1.5]},
    ],
    "edges": [
        [2, 8, 2],
        [2, 16, 2],
        [2, 10, 2],
        [4, 7, 1],
        [7, 16, 2],
        [8, 16, 2],
        [8, 17, 1],
        [10, 14, 1],
    ],
}


def make_pivot_gadget_fixture() -> zx.Graph:
    return zx.Graph().from_json(PIVOT_GADGET_JSON)


class TestPivotGadgetRule(MemgraphUnitTestCase):
    def test_pivot_gadget_rule(self):
        qubits = 1
        pyzx_graph = make_pivot_gadget_fixture()

        load_simple_graph(pyzx_graph, self.g)

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.pivot_gadget_simp,
            db_query=ZXQueryStore()._pivot_gadget(),
            pyzx_name="pyzx_pivot_gadget_simp",
            db_name="memgraph_pivot_gadget_rule",
            print_results=False,
        )

        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")

        assert_boundary_degrees_are_one(run.pyzx.graph_after, "pyzx_graph_after")
        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")

        report = validate_structural_rule_results(
            original_graph=run.original_graph,
            pyzx_graph_after=run.pyzx.graph_after,
            db_graph_after=run.db.graph_after,
            check_boundary_counts=True,
            require_changed=True,
            print_results=False,
        )

        self.assertTrue(report["db_vs_pyzx_structural"])
