import random
import unittest
import pyzx as zx
from utils import benchmark_rule, zx_graph_to_db
from zxdb.generate import CNOT_HAD_PHASE_graph
from zxdb.zxdb import ZXdb
SEED = 10
random.seed(SEED)

# OK
# python -m unittest tests.test_spider_fusion
class TestSpiderFusion(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        self.qubits = 2
        circuit = CNOT_HAD_PHASE_graph(qubits=self.qubits, depth=10*self.qubits, clifford=False)
        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_spider_fusion(self):
        rule_functions = [self.zxdb.spider_fusion, zx.spider_simp]
        rule_names = ["db_spider_fusion", "pyzx_spider_fusion"]

        #rule_functions = [zx.spider_simp]
        #rule_names = ["pyzx_spider_fusion"]


        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule = "spider_fusion",
                       visualize=False, 
                       test_tensor_equivalence=True,
                       test_isomorphism=True,
                       test_degree_distributions=True)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()