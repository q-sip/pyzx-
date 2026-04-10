import os
from dotenv import load_dotenv
import pyzx as zx
from pyzx.simplify import spider_simp, to_gh
from pyzx.graph.zxdb.zxdb import ZXdb

# import random
# from pyzx.graph.graph_memgraph import GraphMemgraph

load_dotenv()
URI = os.getenv("MEMGRAPH_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
# for x in range(100):
#     print(f'seed ===== {x}')
# c = zx.generate.CNOT_HAD_PHASE_circuit(6, 50, seed=seed)


# g = zx.generate.cliffordT(3, 30, seed=8, backend='memgraph')
# c = g.copy(backend='simple')
# c_local = g.copy(backend='simple')
# g = c.to_graph(backend='memgraph')


with ZXdb(URI, AUTH[0], AUTH[1]) as zxdb:
    stop_requested = False
    found = False
    for q in range(2, 10):
        if stop_requested or found:
            break
        for d in range(10, 100, 10):
            if stop_requested or found:
                break
            for s in range(1, 100, 10):
                # g = zx.generate.cliffordT(q, d, seed=s, backend='memgraph')
                c = zx.generate.circuit_identity_two_qubit1()
                g = c.to_graph(backend="memgraph")
                c = g.copy(backend='simple')

                print(q, d, s)
                print('starting full reduce...')
                print(f"Node count: {g.num_vertices()}")
                input = "Pause"

                zxdb.full_reduce()

                print('full reduce done!')
                print(f"Node count zxdb: {g.num_vertices()}")
                nodes = g.num_vertices()

                g.normalize()
                print('normalize done')

                print('started comparing')
                g_local = g.copy(backend='simple')
                compare = zx.compare_tensors(g_local, c, preserve_scalar=False)
                print(f'Comparing: {compare}')

                zxdb.clear_all_data()

                zx.draw(g_local)

                # g_pyzx = zx.generate.cliffordT(q, d, seed=s, backend='simple')
                # print(f"Node count pyzx input: {g_pyzx.num_vertices()}")
                print(f"Node count pyzx input: {c.num_vertices()}")
                zx.draw(c)

                spider_simp(c)

                zx.draw(c)
                print('pyzx spider_simp done!')
                print(f"Node count pyzx: {c.num_vertices()}")

                if nodes != c.num_vertices():
                    found = True
                    print(f"{q,d,s} failed")
                    break

                zxdb.clear_all_data()

                if not compare:
                    print('Comparison failed, stopping loop.')
                    print(f"{q,d,s} failed")
                    stop_requested = True
                    break

# zxdb = ZXdb(URI, AUTH[0], AUTH[1])
# path = zxdb.current_path
# print('starting full reduce...')
# print(f"Node count: {g.num_vertices()}")
# zxdb.full_reduce()
# #zx.full_reduce(c_local)
# print('full reduce done!')
# print(f"Node count zxdb: {g.num_vertices()}")
# #print(f'node count pyzx: {c_local.num_vertices()}')

# # zx.full_reduce(s)
# # s.normalize()
# # 2. Now PyZX can safely read it
# g.normalize()
# print('normalize done')
# # 3. Copy the graph to local memory (Simple backend) so the tensor calculation
# # doesn't have to send 10,000 queries to Memgraph, which takes forever.
# # zx.to_graph_like(g)
# g_local = g.copy(backend='simple')
# print('g_local copy done')
# # c_opt = zx.extract_circuit(g.clone())

# 4. Compare the reduced graph directly to the original circuit!
# print('started comparing')
# compare = zx.compare_tensors(g_local, c, preserve_scalar=False)
# print(f'Comparing: {compare}')
# if False == False:
#     print(f'False with seed {x}')
#     break
# zxdb.clear_all_data()
# g.clear_clones()