import os
from dotenv import load_dotenv
import pyzx as zx
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("MEMGRAPH_USER"), os.getenv("MEMGRAPH_PASSWORD"))
c = zx.generate.CNOT_HAD_PHASE_circuit(2, 20, seed=50)
g = c.to_graph(backend='memgraph')
zxdb = ZXdb(URI, AUTH[0], AUTH[1])
path = zxdb.current_path
def graph_full_reduce():
    zxdb.spider_fusion()
    print('hadamard_cancel')
    zxdb.hadamard_cancel()
    print('remove_identities')
    zxdb.remove_identities()
    print('pivot_rule')
    zxdb.pivot_rule()
    print('local_complementation_rule')
    zxdb.local_complementation_rule()
    print('phase_gadget_fusion_rule')
    zxdb.phase_gadget_fusion_rule()
    print('pivot_gadget_rule')
    zxdb.pivot_gadget_rule()
    print('pivot_boundary_rule')
    zxdb.pivot_boundary_rule()
    print('bialgebra_simp')
    zxdb.bialgebra_simp()
    print('get_degree_distribution')
    zxdb.get_degree_distribution()
    print('turn_hadamard_gates_into_edges')
    zxdb.turn_hadamard_gates_into_edges()

for x in range(100):
    graph_full_reduce()

g.normalize()

c_opt = zx.extract_circuit(g.clone())

print(f'Comparing: {zx.compare_tensors(c_opt, c)}')