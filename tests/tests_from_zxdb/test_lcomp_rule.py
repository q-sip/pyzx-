import unittest
from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase
from pyzx.graph.memgraph_queries import ZXQueryStore
from .helpers import (
    load_simple_graph,
    make_lcomp_fixture,
    mark_lcomp_fixture_pattern,
    run_db_rule_only,
    validate_db_only_rule,
    assert_boundary_degrees_are_one,
)


class TestLocalComplementFixture(MemgraphUnitTestCase):
    def test_local_complement_rewrite(self):
        qubits = 1
        pyzx_graph = make_lcomp_fixture()

        load_simple_graph(pyzx_graph, self.g)

        marked = mark_lcomp_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=ZXQueryStore()._local_complement_rewrite(),
            db_name="memgraph_local_complement",
            print_results=False,
        )

        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")

        # boundary sanity
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")
        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")

        # semantic check: DB result must be tensor-equivalent to original
        report = validate_db_only_rule(
            original_graph=run.original_graph,
            db_graph_after=run.db.graph_after,
            db_return_value=run.db.return_value,
            qubits=qubits,
            preserve_scalar=False,
            require_fired=True,
            check_boundary_counts=True,
            print_results=False,
        )

        self.assertTrue(report["db_vs_original"])

    def test_local_complement_full_rewrite(self):
        qubits = 1
        pyzx_graph = make_lcomp_fixture()

        load_simple_graph(pyzx_graph, self.g)

        marked = mark_lcomp_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=ZXQueryStore()._local_complement_full(),
            db_name="memgraph_local_complement",
            print_results=False,
        )

        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")

        # boundary sanity
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")
        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")

        # semantic check: DB result must be tensor-equivalent to original
        report = validate_db_only_rule(
            original_graph=run.original_graph,
            db_graph_after=run.db.graph_after,
            db_return_value=run.db.return_value,
            qubits=qubits,
            preserve_scalar=False,
            require_fired=True,
            check_boundary_counts=True,
            print_results=False,
        )

        self.assertTrue(report["db_vs_original"])
