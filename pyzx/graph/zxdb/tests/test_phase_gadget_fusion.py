import random
import unittest
import pyzx as zx
import json
from utils import benchmark_rule, zx_graph_to_db
from zxdb.generate import PHASE_GADGET_GRAPH
from zxdb.pyzx_utils import qubit_count
from zxdb.zxdb import ZXdb

SEED = 1337
random.seed(SEED)

# OK
# python -m unittest tests.test_phase_gadget_fusion
class TestPhaseGadgetFusion(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        
        
        with open("circuits\\gadget_fusion_hadamard.json", "r") as f:
            circuit_json = json.load(f)
        circuit = zx.Graph().from_json(circuit_json)

        #with open("circuits\\gadget_fusion_red_green.json", "r") as f:
        #    circuit_json = json.load(f)
        #circuit = zx.Graph().from_json(circuit_json)

        for _ in range(18):
            circuit = circuit + circuit
        
        # Alternative tests
        #circuit = PHASE_GADGET_GRAPH(
        #    gadget_sizes=[3, 5, 7, 9])

        self.qubits = qubit_count(circuit)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)


    def test_lcomp_rule(self):

        rule_functions = [self.zxdb.phase_gadget_fusion_rule, zx.gadget_simp]
        rule_names = ["db_phase_gadget_fusion", "pyzx_phase_gadget_fusion"]

        #rule_functions = [zx.gadget_simp]
        #rule_names = ["pyzx_phase_gadget_fusion"]

        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="phase_gadget_fusion",
                       visualize=False,
                       test_isomorphism=False,
                       test_degree_distributions=True,
                       test_tensor_equivalence=False)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()