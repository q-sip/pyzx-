
import pyzx as zx



def comparison_1(seed: int, backend: str | None = None):
    """compares neo4j-backend circuit reduction to itself
    backend = "neo4j" for neo4j
    backend = "igraph" for GraphIG
    backend = "simple" or None or leave parameter uninitialized for simple, default graph
    backend = "multigraph" for Multigraph
    backend = "graph_tool" for GraphGT
    """

    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=4, depth=20, seed=seed)

    g = c.to_graph(backend=backend)

    print(f"""Graph created with {g.num_vertices()}
        vertices and {g.num_edges()} edges for {backend}.""")
    print(f"Starting full reduce for {backend} backend...")

    zx.full_reduce(g)

    print(f"""Full reduce completed. Graph {backend}
    now has {g.num_vertices()} vertices and {g.num_edges()} edges.""")

    g.normalize()

    print(f"""Graph normalized. Graph {backend}
    now has {g.num_vertices()} vertices and {g.num_edges()} edges.""")

    c_opt = zx.extract_circuit(g.copy())

    return zx.compare_tensors(c, c_opt), g.num_vertices(), g.num_edges(), backend


def comparison_2(seed: int, b1: str | None = None, b2: str | None = None):
    """compares one backend to another"""
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=4, depth=40, seed=seed)

    g1 = c.to_graph(backend=b1)
    g2 = c.to_graph(backend=b2)

    zx.full_reduce(g1)
    zx.full_reduce(g2)

    g1.normalize()
    g2.normalize()

    c_opt1 = zx.extract_circuit(g1.copy())
    c_opt2 = zx.extract_circuit(g2.copy())

    return zx.compare_tensors(c_opt1, c_opt2)


print("simple:", comparison_1(42))
# print("igraph:", comparison_1(42, "igraph")) doesn't work, doesn't contain all mandatory methods
#print("Multigraph:", comparison_1(42, "multigraph"))
# print("graph_tool", comparison_1(42, "graph_tool")) deprecated
# print("quizx-vec", comparison_1(42, "quizx-vec"))
print("Neo4j:", comparison_1(42, "neo4j"))

#print("Neo4j vs simple:", comparison_2(42, "simple", "neo4j"))
