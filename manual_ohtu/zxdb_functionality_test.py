import os
from dotenv import load_dotenv
import pyzx as zx
import random
from pyzx.graph.zxdb.zxdb import ZXdb
from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
# for x in range(100):
#     print(f'seed ===== {x}')
c = zx.generate.CNOT_HAD_PHASE_circuit(10, 75, seed=50)
g = c.to_graph(backend='memgraph')

#copy_simp candidates
# vs = list(g.vertices())
# for idx in range(50):
#     x_spider = g.add_vertex(zx.VertexType.X, qubit=0, row=idx, phase=0.25)
#     z_state = g.add_vertex(zx.VertexType.Z, qubit=1, row=idx, phase=float(random.randint(0, 1)))
#     g.add_edge((z_state, x_spider))


#local_complementation_rule candidates, leaves some isolated parts but should be correct (tensors match)
# vs = list(g.vertices())
# for idx in range(10):
#     # Create the central Z-spider with +/- 0.5 phase
#     center_phase = 0.5 if random.random() > 0.5 else -0.5
#     center = g.add_vertex(zx.VertexType.Z, qubit=0, row=idx+100, phase=center_phase)

#     # Create a random number of Z-spider neighbors (between 3 and 5)
#     num_neighbors = random.randint(3, 5)
#     for n in range(num_neighbors):
#         # The neighbors can have any phase, keep them as Z-spiders
#         neighbor = g.add_vertex(zx.VertexType.Z, qubit=n+1, row=idx+100, phase=0.25)
#         # They MUST be connected by HADAMARD edges for the rule to trigger
#         g.add_edge((center, neighbor), edgetype=zx.EdgeType.HADAMARD)

zxdb = ZXdb(URI, AUTH[0], AUTH[1])
path = zxdb.current_path
print('starting full reduce...')
print(f"Node count: {g.num_vertices()}")
zxdb.full_reduce()
print('full reduce done!')
print(f"Node count: {g.num_vertices()}")
# zx.full_reduce(s)
# s.normalize()

# 2. Now PyZX can safely read it
g.normalize()
print('normalize done')
# 3. Copy the graph to local memory (Simple backend) so the tensor calculation
# doesn't have to send 10,000 queries to Memgraph, which takes forever.
# zx.to_graph_like(g)
g_local = g.copy(backend='simple')
print('g_local copy done')
# c_opt = zx.extract_circuit(g.clone())

# 4. Compare the reduced graph directly to the original circuit!
print('started comparing')
compare = zx.compare_tensors(g_local, c, preserve_scalar=False)
print(f'Comparing: {compare}')
# if False == False:
#     print(f'False with seed {x}')
#     break
zxdb.clear_all_data()
# g.clear_clones()