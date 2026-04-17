import random
import unittest
import pyzx as zx

from utils import benchmark_rule, zx_graph_to_db
from zxdb.zxdb import ZXdb

SEED = 0
random.seed(SEED)

# OK
# python -m unittest tests.test_hadamard_cancellation
class TestHadamardCancellation(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        self.qubits = 2
        circuit = zx.generate.CNOT_HAD_PHASE_circuit(qubits=self.qubits,depth=10*self.qubits,clifford=False)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_Hadamard_cancel(self):
        rule_functions = [self.zxdb.hadamard_cancel]
        rule_names = ["db_hadamard_cancel"]
        benchmark_rule(rule_functions, rule_names, self.zx_graph, self.zxdb, self.qubits, visualize=False)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()