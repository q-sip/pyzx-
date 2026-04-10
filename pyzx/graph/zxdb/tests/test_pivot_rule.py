import random
import unittest
import pyzx as zx
import json
import matplotlib

from utils import benchmark_rule, zx_graph_to_db
matplotlib.use('Agg')

from zxdb.pyzx_utils import compose_zx_graphs
from zxdb.zxdb import ZXdb

SEED = 1337
random.seed(SEED)

# OK
# python -m unittest tests.test_pivot_rule
class TestPivotRule(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        # A random circuit quite rarely contains instances where pivoting can be applied
        # so we use a fixed circuit here.
        filepath = "circuits\\pivot_circuit2.json"
        with open(filepath, "r") as f:
            circuit_json = json.load(f)
        circuit = zx.Graph().from_json(circuit_json)

        for _ in range(12):
            circuit, qubits = compose_zx_graphs(circuit, circuit, connected_ratio=0.25)

        with open("circuits\\pivot_circuit_temp.json", "w") as f:
            json.dump(json.loads(circuit.to_json()), f, indent=4)

        self.qubits = qubits
        #circuit = zx.generate.CNOT_HAD_PHASE_circuit(self.qubits, depth = 100*self.qubits)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_pivot_rule(self):
        rule_functions = [self.zxdb.pivot_rule, zx.pivot_simp]
        rule_names = ["db_pivot_rule", "pyzx_pivot_rule"]
        # Here test_tensor_equivalence can fail at PyZX end
        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="pivot",
                       test_isomorphism=True,
                       test_degree_distributions=True,
                       test_tensor_equivalence=True,
                       visualize=False)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()