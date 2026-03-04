import pyzx as zx
from tests.tests_from_zxdb._base_unittest_neo4j import Neo4jUnitTestCase
from pyzx.graph.neo4j_queries import CypherRewrites
from .helpers import (
    load_simple_graph_into_neo4j,
    run_db_rule_only,
    validate_db_only_rule,
)
from .helpers import make_hadamard_cancel_fixture, mark_hadamard_cancel_pattern
from .random_queries_neo4j import HADAMARD_EDGE_CANCELLATION_MUTANT



class TestHadamardCancel(Neo4jUnitTestCase):
    def test_hadamard_cancel_query(self):
        qubits = 1
        pyzx_graph = make_hadamard_cancel_fixture()
        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_hadamard_cancel_pattern(self.g)
        self.assertEqual(marked, 1)

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=CypherRewrites.HADAMARD_EDGE_CANCELLATION,
            db_name="neo4j_hadamard_cancel",
            print_results=True,
        )

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

    def test_hadamard_cancel_mutant_fails_semantics(self):
        qubits = 1
        pyzx_graph = make_hadamard_cancel_fixture()

        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_hadamard_cancel_pattern(self.g)
        self.assertEqual(marked, 1, "Expected exactly 1 marked middle node")

        run = run_db_rule_only(
            original_graph=pyzx_graph,
            db_graph=self.g,
            db_query=HADAMARD_EDGE_CANCELLATION_MUTANT,
            db_name="neo4j_hadamard_cancel_mutant",
            print_results=True,
        )

        # Should fire (return at least one record)
        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")

        # Should FAIL semantic equivalence vs original
        with self.assertRaises(AssertionError):
            validate_db_only_rule(
                original_graph=run.original_graph,
                db_graph_after=run.db.graph_after,
                db_return_value=run.db.return_value,
                qubits=qubits,
                preserve_scalar=False,
                require_fired=True,
                check_boundary_counts=True,
                print_results=True,
            )
