import os
from dotenv import load_dotenv
import pyzx as zx
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
c = zx.generate.CNOT_HAD_PHASE_circuit(8, 50, seed=50)
g = c.to_graph(backend='memgraph')
zxdb = ZXdb(URI, AUTH[0], AUTH[1])
path = zxdb.current_path

zxdb.full_reduce()

# 2. Now PyZX can safely read it
g.normalize()
# 3. Copy the graph to local memory (Simple backend) so the tensor calculation
# doesn't have to send 10,000 queries to Memgraph, which takes forever.
# zx.to_graph_like(g)
g_local = g.copy(backend='simple')
# c_opt = zx.extract_circuit(g.clone())

# 4. Compare the reduced graph directly to the original circuit!
print(f'Comparing: {zx.compare_tensors(g_local, c, preserve_scalar=False)}')
g.clear_clones()