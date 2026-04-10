import pyzx as zx
from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase
from pyzx.graph.memgraph_queries import ZXQueryStore
from .helpers import (
    load_simple_graph,
    run_db_rule_only,
    validate_db_only_rule,
)
from .helpers import make_hadamard_cancel_fixture, mark_hadamard_cancel_pattern, assert_boundary_degrees_are_one


class TestHadamardCancel(MemgraphUnitTestCase):
    def test_hadamard_cancel_query(self):
        qubits = 1
        pyzx_graph = make_hadamard_cancel_fixture()
        load_simple_graph(pyzx_graph, self.g)

        marked = mark_hadamard_cancel_pattern(self.g)
        self.assertEqual(marked, 1)

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=ZXQueryStore()._hadamard_edge_cancellation(),
            db_name="memgraph_hadamard_cancel",
            print_results=True,
        )

        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")

        report = validate_db_only_rule(
            original_graph=run.original_graph,
            db_graph_after=run.db.graph_after,
            db_return_value=run.db.return_value,
            qubits=qubits,
            preserve_scalar=False,
            require_fired=True,
            check_boundary_counts=True,
            print_results=True,
        )

        self.assertTrue(report["db_vs_original"])
