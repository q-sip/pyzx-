import pyzx as zx
from tests.tests_from_zxdb._base_unittest import Neo4jUnitTestCase
from pyzx.graph.neo4j_queries import CypherRewrites
from .helpers import (
    load_simple_graph_into_neo4j,
    run_rule_on_backends,
    validate_rule_results,
)
from .helpers import make_bialgebra_fixture, mark_bialgebra_fixture_pattern, assert_boundary_degrees_are_one, print_boundary_info
from .random_queries import BIALGEBRA_SIMPLIFICATION_MUTANT, BIALGEBRA_SIMPLIFICATION



class TestBialgebraFixture(Neo4jUnitTestCase):
    def test_bialgebra_correct_query(self):
        qubits = 2
        pyzx_graph = make_bialgebra_fixture()

        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_bialgebra_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.bialg_simp,
            db_query=BIALGEBRA_SIMPLIFICATION,
            pyzx_name="pyzx_bialg_simp",
            db_name="neo4j_bialg_simp",
            print_results=True,
        )
        #print_boundary_info(run.pyzx.graph_after, "pyzx")
        #print_boundary_info(run.db.graph_after, "db")

        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")
        assert_boundary_degrees_are_one(run.pyzx.graph_after, "pyzx_graph_after")
        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")

        report = validate_rule_results(
            original_graph=run.original_graph,
            pyzx_graph_after=run.pyzx.graph_after,
            db_graph_after=run.db.graph_after,
            qubits=qubits,
            preserve_scalar=False,
            max_tensor_qubits=9,
            check_backend_agreement=True,
            check_boundary_counts=True,
            print_results=True,
        )

        self.assertTrue(report["pyzx_vs_original"])
        self.assertTrue(report["db_vs_original"])
        self.assertTrue(report["db_vs_pyzx"])

    def test_bialgebra_mutant(self):
        pyzx_graph = make_bialgebra_fixture()

        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_bialgebra_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.bialg_simp,
            db_query=BIALGEBRA_SIMPLIFICATION_MUTANT,
            pyzx_name="pyzx_bialg_simp",
            db_name="neo4j_bialg_simp_mutant",
            print_results=True,
        )

        #print_boundary_info(run.pyzx.graph_after, "pyzx")
        #print_boundary_info(run.db.graph_after, "db")

        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")
        assert_boundary_degrees_are_one(run.pyzx.graph_after, "pyzx_graph_after")
        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")

        with self.assertRaises(AssertionError):
            validate_rule_results(
                original_graph=run.original_graph,
                pyzx_graph_after=run.pyzx.graph_after,
                db_graph_after=run.db.graph_after,
                qubits=2,
                preserve_scalar=False,
                max_tensor_qubits=9,
                check_backend_agreement=False,
                check_boundary_counts=True,
                print_results=True,
            )


    def test_bialgebra_actual_query(self):
        qubits = 2
        pyzx_graph = make_bialgebra_fixture()

        load_simple_graph_into_neo4j(pyzx_graph, self.g)

        marked = mark_bialgebra_fixture_pattern(self.g)
        self.assertEqual(marked, 4, "Expected exactly 4 marked pattern nodes")

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.bialg_simp,
            db_query=CypherRewrites.BIALGEBRA_SIMPLIFICATION,
            pyzx_name="pyzx_bialg_simp",
            db_name="neo4j_bialg_simp",
            print_results=True,
        )
        #print_boundary_info(run.pyzx.graph_after, "pyzx")
        #print_boundary_info(run.db.graph_after, "db")

        self.assertNotEqual(run.db.return_value, [], "DB rewrite did not fire")
        assert_boundary_degrees_are_one(run.pyzx.graph_after, "pyzx_graph_after")
        assert_boundary_degrees_are_one(run.db.graph_after, "db_graph_after")
        assert_boundary_degrees_are_one(pyzx_graph, "original_graph")

        report = validate_rule_results(
            original_graph=run.original_graph,
            pyzx_graph_after=run.pyzx.graph_after,
            db_graph_after=run.db.graph_after,
            qubits=qubits,
            preserve_scalar=False,
            max_tensor_qubits=9,
            check_backend_agreement=True,
            check_boundary_counts=True,
            print_results=True,
        )

        self.assertTrue(report["pyzx_vs_original"])
        self.assertTrue(report["db_vs_original"])
        self.assertTrue(report["db_vs_pyzx"])
