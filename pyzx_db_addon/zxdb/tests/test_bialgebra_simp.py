import random
import unittest
import pyzx as zx
import json
from utils import benchmark_rule, zx_graph_to_db
from zxdb.generate import CNOT_HAD_PHASE_graph
from zxdb.zxdb import ZXdb

SEED = 42
random.seed(SEED)

# OK
# python -m unittest tests.test_bialgebra_simp
class TestBialgebraSimp(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        self.qubits = 500
        #with open("circuits\\bialgebra_circuit_4.json", "r") as f:
        #    circuit_json = json.load(f)
        #circuit = zx.Graph().from_json(circuit_json)
        circuit = CNOT_HAD_PHASE_graph(qubits=self.qubits, depth=10*self.qubits, clifford=False)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_bialgebra_simp(self):
        # self.zxdb.bialgebra_simp
        # "db_bialgebra_simp"
        rule_functions = [self.zxdb.bialgebra_simp, zx.bialg_simp]
        rule_names = ["db_bialgebra_simp", "pyzx_bialgebra_simp"]
        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="bialgebra_simp",
                       test_isomorphism=False,
                       test_degree_distributions=False,
                       test_tensor_equivalence=True,
                       visualize=False)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()