import random
from time import time

import pyzx as zx
from pyzx.graph.graph_AGE import GraphAGE


def _cleanup_graph(g) -> None:
    """Delete AGE graph data and close the connection when applicable."""
    if g is None:
        return
    try:
        if isinstance(g, GraphAGE):
            try:
                g.delete_graph()
            except Exception:
                pass
            g.close()
    except Exception:
        pass


def _reset_default_age_graph() -> None:
    """Ensure the default AGE graph namespace is empty before manual runs."""
    g = None
    try:
        g = GraphAGE()
        try:
            g.delete_graph()
        except Exception:
            pass
    finally:
        if g is not None:
            try:
                g.close()
            except Exception:
                pass


def comparison_1(seed: int, backend: str = "age") -> bool:
    """Compare circuit reduction against the original circuit for one backend.

    backend = "age" for GraphAGE
    backend = "simple" for default graph
    backend = "multigraph" for Multigraph
    backend = "neo4j" for Neo4j
    """
    random.seed(seed)
    if backend == "age":
        _reset_default_age_graph()
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=2, depth=8)

    g = None
    g_clone = None
    try:
        g = c.to_graph(backend=backend)
        zx.full_reduce(g)
        g.normalize()
        zx.draw(g)

        return zx.compare_tensors(c, g)
    except Exception as exc:
        print(f"comparison_1 failed for backend={backend}: {exc}")
        return False
    finally:
        _cleanup_graph(g_clone)
        _cleanup_graph(g)


def comparison_2(seed: int, b1: str = "simple", b2: str = "age") -> bool:
    """Compare reduction results between two backends."""
    random.seed(seed)
    if b1 == "age" or b2 == "age":
        _reset_default_age_graph()
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=2, depth=8)

    g1 = None
    g2 = None
    g1_clone = None
    g2_clone = None
    try:
        g1 = c.to_graph(backend=b1)
        g2 = c.to_graph(backend=b2)

        zx.full_reduce(g1)
        zx.full_reduce(g2)

        g1.normalize()
        g2.normalize()

        return zx.compare_tensors(g1, g2)
    except Exception as exc:
        print(f"comparison_2 failed for backends=({b1}, {b2}): {exc}")
        return False
    finally:
        _cleanup_graph(g1_clone)
        _cleanup_graph(g2_clone)
        _cleanup_graph(g1)
        _cleanup_graph(g2)


if __name__ == "__main__":
    start = time()
    print("AGE:", comparison_1(42, "age"))
    print("AGE vs simple:", comparison_2(42, "simple", "age"))
    print(f"Finished in {time() - start:.2f}s")
