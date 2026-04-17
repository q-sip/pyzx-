import random
import unittest
import pyzx as zx
import json
from utils import benchmark_rule, zx_graph_to_db
from zxdb.pyzx_utils import qubit_count
from zxdb.zxdb import ZXdb

SEED = 1337
random.seed(SEED)

# OK
# python -m unittest tests.test_lcomp_rule
class TestLCompRule(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        filepath = "circuits\\local_complementation_1.json"
        with open(filepath, "r") as f:
            circuit_json = json.load(f)
        circuit = zx.Graph().from_json(circuit_json)
        self.qubits = qubit_count(circuit)

        for _ in range(17):
            circuit = circuit + circuit

        with open("circuits\\temp_circuit.json", "w") as f:
            json.dump(json.loads(circuit.to_json()), f, indent=4)

        self.qubits = qubit_count(circuit)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_lcomp_rule(self):
        rule_functions = [self.zxdb.local_complementation_rule, zx.lcomp_simp]
        rule_names = ["db_local_complementation", "pyzx_local_complementation"]
        
        #rule_functions = [zx.lcomp_simp]
        #rule_names = ["pyzx_local_complementation"]

        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="local_complementation", 
                       visualize=False,
                       test_isomorphism=False,
                       test_degree_distributions=True,
                       test_tensor_equivalence=False)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()