"""Sequentially exercise each database backend end-to-end.

For every backend, `pyzx_db_addon.force_backend(name)` rebinds the
`Graph` attribute in all loaded pyzx.* modules to that backend's class,
so anything built on top of `pyzx.Graph` (e.g. `pyzx.generate.cliffordT`,
`pyzx.simplify.full_reduce`) creates and mutates graphs inside that
database. When memgraph is being demoed, every graph lives in memgraph.
"""

import traceback

import pyzx
import pyzx_db_addon
from pyzx.utils import VertexType, EdgeType


BACKENDS = ["vanilla", "age", "neo4j", "memgraph"]


def build_small_graph(g):
    v0 = g.add_vertex(VertexType.Z, qubit=0, row=0)
    v1 = g.add_vertex(VertexType.X, qubit=0, row=1)
    v2 = g.add_vertex(VertexType.Z, qubit=1, row=1)
    g.add_edge((v0, v1), EdgeType.SIMPLE)
    g.add_edge((v1, v2), EdgeType.HADAMARD)
    return g


def demo_backend(backend: str) -> None:
    print(f"\n=== {backend} ===")
    is_vanilla = backend == "vanilla"
    undo = [] if is_vanilla else pyzx_db_addon.force_backend(backend)
    try:
        g = pyzx.Graph() if is_vanilla else pyzx_db_addon.create_graph(backend)
        build_small_graph(g)
        print(f"small graph: {g.num_vertices()}v / {g.num_edges()}e")

        g_rand = pyzx.generate.cliffordT(3, 15)
        before = (g_rand.num_vertices(), g_rand.num_edges())
        pyzx.simplify.full_reduce(g_rand)
        after = (g_rand.num_vertices(), g_rand.num_edges())
        print(f"cliffordT full_reduce: {before[0]}v/{before[1]}e -> {after[0]}v/{after[1]}e")
        print(f"backend reported by graph: {getattr(g_rand, 'backend', '?')}")
    finally:
        pyzx_db_addon.restore_backend(undo)


def main():
    print("known backends:", sorted(set(pyzx_db_addon._BACKEND_FACTORIES)))
    for backend in BACKENDS:
        try:
            demo_backend(backend)
        except Exception as e:
            print(f"[{backend}] failed: {type(e).__name__}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
