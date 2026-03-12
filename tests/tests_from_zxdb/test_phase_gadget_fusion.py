import pyzx as zx

from tests.tests_from_zxdb._base_unittest_memgraph import MemgraphUnitTestCase
from tests.tests_from_zxdb.helpers import (
    load_simple_graph,
    run_rule_on_backends,
    validate_rule_results,
)
from pyzx.graph.memgraph_queries import ZXQueryStore


GADGET_FUSION_HADAMARD_JSON = {
    "version": 2,
    "backend": "multigraph",
    "variable_types": {},
    "scalar": {"power2": 0, "phase": "0"},
    "inputs": [],
    "outputs": [],
    "edata": {},
    "auto_simplify": False,
    "vertices": [
        {"id": 0, "t": 1, "pos": [0.0, 1.0]},
        {"id": 1, "t": 1, "pos": [0.5, -0.75]},
        {"id": 2, "t": 1, "pos": [0.5, -2.0], "phase": "π/3"},
        {"id": 3, "t": 1, "pos": [2.25, 1.0]},
        {"id": 4, "t": 1, "pos": [2.0, -2.0], "phase": "π/7"},
        {"id": 5, "t": 0, "pos": [3.5, 1.0]},
        {"id": 6, "t": 0, "pos": [-1.25, 1.0]},
        {"id": 7, "t": 1, "pos": [2.0, -0.75]},
    ],
    "edges": [
        [0, 6, 1],
        [0, 1, 2],
        [0, 7, 2],
        [1, 2, 2],
        [1, 3, 2],
        [3, 5, 1],
        [3, 7, 2],
        [4, 7, 2],
    ],
}


def make_phase_gadget_hadamard_graph() -> zx.Graph:
    return zx.Graph().from_json(GADGET_FUSION_HADAMARD_JSON)


def _sum_fusions(return_value) -> int:
    total = 0
    for rec in (return_value or []):
        try:
            total += int(rec["fusions_performed"])
        except Exception:
            pass
    return total


class TestPhaseGadgetFusionHadamard(MemgraphUnitTestCase):
    def test_phase_gadget_fusion_hadamard(self):
        pyzx_graph = make_phase_gadget_hadamard_graph()

        load_simple_graph(pyzx_graph, self.g)

        run = run_rule_on_backends(
            original_graph=pyzx_graph,
            db_graph=self.g,
            pyzx_rule=zx.gadget_simp,
            db_query=ZXQueryStore()._gadget_fusion_hadamard(),
            pyzx_name="pyzx_gadget_simp",
            db_name="memgraph_gadget_fusion_hadamard",
            print_results=True,
        )

        db_fusions = _sum_fusions(run.db.return_value)
        self.assertGreater(db_fusions, 0, "DB gadget fusion did not fire")

        report = validate_rule_results(
            original_graph=run.original_graph,
            pyzx_graph_after=run.pyzx.graph_after,
            db_graph_after=run.db.graph_after,
            qubits=0,
            preserve_scalar=False,
            max_tensor_qubits=9,
            check_backend_agreement=True,
            check_boundary_counts=True,
            print_results=True,
        )

        self.assertTrue(report["pyzx_vs_original"])
        self.assertTrue(report["db_vs_original"])
        self.assertTrue(report["db_vs_pyzx"])
