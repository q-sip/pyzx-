import pyzx as zx

from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase
from tests.tests_from_zxdb.helpers import (
    load_simple_graph,
    make_z_spider_fusion_fixture,
    make_x_spider_fusion_fixture,
    run_rule_on_backends,
    validate_rule_results,
    _count_processed_records,
)
from pyzx.graph.memgraph_queries import ZXQueryStore


class TestSpiderFusion(MemgraphUnitTestCase):
    def _run_spider_fusion_case(self, fixture_fn, db_query: str, db_name: str):
        qubits = 1
        pyzx_graph = fixture_fn()

        load_simple_graph(pyzx_graph, self.g)

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.spider_simp,
            db_query=db_query,
            pyzx_name="pyzx_spider_simp",
            db_name=db_name,
            print_results=True,
        )

        processed = _count_processed_records(run.db.return_value)
        self.assertGreater(processed, 0, f"{db_name} did not fire")

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

    def test_spider_fusion_rewrite_1_z(self):
        self._run_spider_fusion_case(
            fixture_fn=make_z_spider_fusion_fixture,
            db_query=ZXQueryStore()._spider_fusion_rewrite(),
            db_name="memgraph_spider_fusion_rewrite_1_z",
        )

    def test_spider_fusion_rewrite_1_x(self):
        self._run_spider_fusion_case(
            fixture_fn=make_x_spider_fusion_fixture,
            db_query=ZXQueryStore()._spider_fusion_rewrite(),
            db_name="memgraph_spider_fusion_rewrite_1_x",
        )

    def test_spider_fusion_rewrite_2_z(self):
        self._run_spider_fusion_case(
            fixture_fn=make_z_spider_fusion_fixture,
            db_query=ZXQueryStore()._spider_fusion_rewrite_2(),
            db_name="memgraph_spider_fusion_rewrite_2_z",
        )

    def test_spider_fusion_rewrite_2_x(self):
        self._run_spider_fusion_case(
            fixture_fn=make_x_spider_fusion_fixture,
            db_query=ZXQueryStore()._spider_fusion_rewrite_2(),
            db_name="memgraph_spider_fusion_rewrite_2_x",
        )
