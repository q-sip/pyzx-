import random
import unittest
import pyzx as zx
import json
from utils import benchmark_rule, zx_graph_to_db
from zxdb.pyzx_utils import qubit_count
from zxdb.zxdb import ZXdb

SEED = 1337
random.seed(SEED)

# python -m unittest tests.test_pivot_boundary_rule
class TestPivotBoundaryRule(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        with open("circuits\\pivot_boundary_circuit.json", "r") as f:
            circuit_json = json.load(f)

        circuit = zx.Graph().from_json(circuit_json)

        for _ in range(9):
            circuit = circuit + circuit

        self.qubits = qubit_count(circuit)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_pivot_boundary_simp(self):

        rule_functions = [self.zxdb.pivot_boundary_rule, zx.pivot_boundary_simp]
        rule_names = ["db_pivot_boundary", "pyzx_pivot_boundary"]

        #rule_functions = [zx.pivot_boundary_simp]
        #rule_names = ["pyzx_pivot_boundary"]

        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="pivot_boundary",
                       visualize=False,
                       test_isomorphism=True,
                       test_degree_distributions=True,
                       test_tensor_equivalence=True)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()