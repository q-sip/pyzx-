import pyzx as zx
import random

def get_messy_graph(n_vertices=20, n_edges=40):
    g = zx.Graph(backend="memgraph")
    # 1. Add random vertices with random phases and types
    v_list = []
    for _ in range(n_vertices):
        v = g.add_vertex(
            ty=random.choice([0, 1, 2]), # Z, X, or H-box
            phase=random.choice([0, 1, 0.5, 0.25]) # 0, pi, pi/2, pi/4
        )
        v_list.append(v)

    # 2. Add random edges (including multiple edges between same types)
    for _ in range(n_edges):
        s, t = random.sample(v_list, 2)
        g.add_edge((s, t), edgetype=random.choice([1, 2])) # Simple or Hadamard

    return g

# Now run your loop with this
for _ in range(1000):
    try:
        g = get_messy_graph(n_vertices=200, n_edges=400)
        zx.full_reduce(g)
    except:
        continue
