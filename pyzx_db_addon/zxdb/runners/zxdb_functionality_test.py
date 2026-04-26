import os
import faulthandler
import time
from dotenv import load_dotenv
import pyzx as zx
from pyzx.simplify import spider_simp, to_gh
import pyzx_db_addon
pyzx_db_addon.enable_pyzx_backend_overrides()
from pyzx_db_addon.zxdb.zxdb import ZXdb

# import random
# from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
# for x in range(100):
#     print(f'seed ===== {x}')
c = zx.generate.CNOT_HAD_PHASE_circuit(7, 30, seed=43)
# g = zx.generate.cliffordT(3, 30, seed=8, backend='memgraph')
# c = g.copy(backend='simple')
c_local = c.to_graph(backend='simple')
g = c.to_graph(backend='memgraph')


zxdb = ZXdb(URI, AUTH[0], AUTH[1])
# path = zxdb.current_path
print('starting full reduce...')
print(f"Node count: {g.num_vertices()}")
zxdb.full_reduce(g)
zx.full_reduce(c_local)
print('full reduce done!')
print(f"Node count zxdb: {g.num_vertices()}")
print(f'node count pyzx: {c_local.num_vertices()}')

# # zx.full_reduce(s)
# # s.normalize()
# # 2. Now PyZX can safely read it
g.normalize()
print('normalize done')
# # 3. Copy the graph to local memory (Simple backend) so the tensor calculation
# # doesn't have to send 10,000 queries to Memgraph, which takes forever.
# # zx.to_graph_like(g)
g_local = g.copy(backend='simple')
# print('g_local copy done')
# # c_opt = zx.extract_circuit(g.clone())

# 4. Compare the reduced graph directly to the original circuit!
# print('started comparing')
print('starting compare_tensors...')
start_compare = time.perf_counter()

# If compare_tensors appears stuck, emit Python stack traces every 60s.
faulthandler.dump_traceback_later(60, repeat=True)
try:
	compare = zx.compare_tensors(g_local, c, preserve_scalar=False)
finally:
	faulthandler.cancel_dump_traceback_later()

elapsed_compare = time.perf_counter() - start_compare
print(f'compare_tensors done in {elapsed_compare:.2f}s')
print(f'Comparing: {compare}')
# g = c.copy(backend="memgraph")


# if False == False:
#     print(f'False with seed {x}')
#     break
# zxdb.clear_all_data()
# g.clear_clones()




