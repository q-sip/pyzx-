import os
from dotenv import load_dotenv
import pyzx as zx
import random
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
c = zx.generate.CNOT_HAD_PHASE_circuit(10, 200, seed=50)
g = c.to_graph(backend='memgraph')

#copy_simp candidates
# vs = list(g.vertices())
# for idx in range(50):
#     x_spider = g.add_vertex(zx.VertexType.X, qubit=0, row=idx, phase=0.25)
#     z_state = g.add_vertex(zx.VertexType.Z, qubit=1, row=idx, phase=float(random.randint(0, 1)))
#     g.add_edge((z_state, x_spider))

i = input('')
zxdb = ZXdb(URI, AUTH[0], AUTH[1])
path = zxdb.current_path
zxdb.full_reduce()
# zx.full_reduce(s)
# s.normalize()

# 2. Now PyZX can safely read it
g.normalize()
# 3. Copy the graph to local memory (Simple backend) so the tensor calculation
# doesn't have to send 10,000 queries to Memgraph, which takes forever.
# zx.to_graph_like(g)
g_local = g.copy(backend='simple')
# c_opt = zx.extract_circuit(g.clone())

# 4. Compare the reduced graph directly to the original circuit!
print(f'Comparing: {zx.compare_tensors(g_local, c, preserve_scalar=False)}')
# g.clear_clones()