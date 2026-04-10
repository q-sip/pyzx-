import random
import unittest
import pyzx as zx
import json
from utils import benchmark_rule, zx_graph_to_db
from zxdb.zxdb import ZXdb

SEED = 1337
random.seed(SEED)

# OK
# python -m unittest tests.test_pivot_gadget_rule
class TestPivotGadgetRule(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        with open("circuits\\pivot_gadget_circuit2.json", "r") as f:
            circuit_json = json.load(f)
        circuit = zx.Graph().from_json(circuit_json)

        # Expand the circuit exponentially to increase qubit count
        for _ in range(14):
            circuit += circuit

        with open("circuits\\pivot_gadget_circuit_temp.json", "w") as f:
            json.dump(json.loads(circuit.to_json()), f, indent=4)

        types = circuit.types()
        boundaries = 0
        for v in circuit.vertices():
            if types[v] == zx.VertexType.BOUNDARY or types[v] == 0:
                boundaries += 1

        self.qubits = boundaries // 2
        print(f"Total qubits in test circuit: {self.qubits}")
        #circuit = zx.generate.CNOT_HAD_PHASE_circuit(self.qubits, depth = 100*self.qubits)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_pivot_gadget_simp(self):
        rule_functions = [self.zxdb.pivot_gadget_rule, zx.pivot_gadget_simp]
        rule_names = ["db_pivot_gadget_rule", "pyzx_pivot_gadget_rule"]
        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="pivot_gadget_rule",
                       test_isomorphism=True,
                       test_degree_distributions=False,
                       test_tensor_equivalence=True,
                       visualize=False)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()