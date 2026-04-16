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
c = zx.generate.CNOT_HAD_PHASE_circuit(6, 50, seed=45)
# g = zx.generate.cliffordT(3, 30, seed=8, backend='memgraph')
# c = g.copy(backend='simple')
c_local = c.to_graph(backend='simple')
g = c.to_graph(backend='memgraph')


with ZXdb(URI, AUTH[0], AUTH[1]) as zxdb:


    stop_requested = False


    found = False

    for q in range(3, 10):



        if stop_requested or found:

            break

        for d in range(20, 100, 20):


            if stop_requested or found:

                break

            for s in range(3, 100, 20):

                g = zx.generate.CNOT_HAD_PHASE_circuit(q, d, seed=s)
                g = g.to_graph(backend="memgraph")
                c = g.copy(backend='simple')

                print(q, d, s, "vars")

                print(f"Node count zxdb before: {g.num_vertices()}")

                zxdb.full_reduce(g)

                print('full reduce done!')

                print(f"Node count zxdb: {g.num_vertices()}")


                nodes = g.num_vertices()

                g.normalize()

                print('normalize done')


        

                print(f"Node count pyzx start: {c.num_vertices()}")


                zx.full_reduce(c)


                print('full reduce done!')



                print(f"Node count pyzx: {c.num_vertices()}")
                compare = zx.compare_tensors(g, c, preserve_scalar=False)
                print(f'Comparing: {compare}')

                if g.num_vertices() < c.num_vertices():
                    print(" ")
                    print(" ")
                    print(" ")
                    print("We beat pyzx")
                    print(" ")
                    print(" ")


                paause = input("s")
                zxdb.clear_all_data()


                if not compare:

                    print('Comparison failed, stopping loop.')

                    print(f"{q,d,s} failed")
                    stop_requested = True
                    break




