import unittest
from tests.tests_from_zxdb._base_unittest_neo4j import Neo4jUnitTestCase
from pyzx.graph.neo4j_queries import CypherRewrites
from .helpers import (
    load_simple_graph_into_neo4j,
    make_lcomp_fixture,
    mark_lcomp_fixture_pattern,
    run_db_rule_only,
    validate_db_only_rule,
    assert_boundary_degrees_are_one,
)

from .random_queries_neo4j import LOCAL_COMPLEMENT_NEO4J


class TestLocalComplementFixture(Neo4jUnitTestCase):
    def test_correct_query(self):
        qubits = 1
        pyzx_graph = make_lcomp_fixture()

        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_lcomp_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=LOCAL_COMPLEMENT_NEO4J,
            db_name="neo4j_local_complement",
            print_results=True,
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
            print_results=True,
        )

        self.assertTrue(report["db_vs_original"])

    def test_current_query(self):
        qubits = 1
        pyzx_graph = make_lcomp_fixture()

        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_lcomp_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=CypherRewrites.LOCAL_COMPLEMENT,
            db_name="neo4j_local_complement",
            print_results=True,
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
            print_results=True,
        )

        self.assertTrue(report["db_vs_original"])
