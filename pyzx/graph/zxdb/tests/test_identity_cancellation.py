from fractions import Fraction
import random
import unittest
import pyzx as zx

from utils import benchmark_rule, zx_graph_to_db
from zxdb.zxdb import ZXdb

SEED = 42
random.seed(SEED)

# OK
# python -m unittest tests.test_identity_cancellation
class TestIdentityCancel(unittest.TestCase):

    def setUp(self):
        self.zxdb = ZXdb()
        self.qubits = 1
        #circuit = zx.generate.CNOT_HAD_PHASE_circuit(qubits=self.qubits,depth=10*self.qubits,clifford=False)

        # A lot faster construct the graph than the circuit
        circuit = zx.Graph()
        inputs = []
        outputs = []
        qubit_vertices = {}
        for i in range(self.qubits):
            v_in = circuit.add_vertex(zx.VertexType.BOUNDARY, i, 0)
            inputs.append(v_in)
            qubit_vertices[i] = v_in

        for _ in range(10**2//2):
            for q in range(self.qubits):
                v_z = circuit.add_vertex(zx.VertexType.Z, phase = 0)
                circuit.add_edge(circuit.edge(qubit_vertices[q], v_z), zx.EdgeType.SIMPLE)
                qubit_vertices[q] = v_z
        
        for i in range(self.qubits):
            v_out = circuit.add_vertex(zx.VertexType.BOUNDARY, i, 1)
            circuit.add_edge(circuit.edge(qubit_vertices[i], v_out), zx.EdgeType.SIMPLE)
            outputs.append(v_out)

        circuit.set_outputs(outputs)
        circuit.set_inputs(inputs)

        self.zx_graph = zx_graph_to_db(self.zxdb, circuit)

    def test_identity_cancel(self):
        rule_functions = [self.zxdb.remove_identities, zx.id_simp]
        rule_names = ["db_identity_cancellation", "pyzx_identity_cancellation"]
        
        #rule_functions = [zx.id_simp]
        #rule_names = ["pyzx_identity_cancellation"]

        benchmark_rule(rule_functions, 
                       rule_names, 
                       self.zx_graph, 
                       self.zxdb, 
                       self.qubits,
                       rule="identity_cancellation", 
                       visualize=False,
                       test_isomorphism=True,
                       test_degree_distributions=True,
                       test_tensor_equivalence=True)

    def tearDown(self):
        self.zxdb.close()

if __name__ == '__main__':
    unittest.main()