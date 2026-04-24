from types import NoneType

from numba import typeof

import pyzx as px
import pyzx as zx
from pyzx.graph.graph_memgraph import GraphMemgraph


def delete_all(g: GraphMemgraph):
    query = """MATCH (n) DETACH DELETE n;"""
    g.arb_quer_write(query=query)


def arb_write(g: GraphMemgraph):
    query = """
    MATCH (n:Node)-[r:Wire]-(m:Node) 
    WHERE n.t = 2 
    AND n.graph_id = "graph_test_zxdb"
    SET n.t = 1
    WITH r AS wire
    SET wire.t = CASE WHEN wire.t = 1 THEN 2 ELSE 1 END
    RETURN wire;
    """
    g.arb_quer_write(query=query, kala="koira", kissa="mieto")


from functools import wraps

# 1. Global registry to hold your 10k graph data
stats = {}


def track_rule(func, name):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # PyZX rewrite functions return the number of successful matches applied
        count = func(*args, **kwargs)
        try:
            if count > 0:
                stats[name] = stats.get(name, 0) + count
        except:
            pass
        return count

    return wrapper


# 2. Identify the core sub-rules used by full_reduce
# In PyZX, full_reduce is a loop of these specific functions:
rules_to_count = [
    'spider_simp', 'id_simp', 'pivot_simp',
    'lcomp_simp', 'gadget_simp', 'pivot_gadget_simp',
    'pivot_boundary_simp'
]

rules_to_count = [
    'interior_clifford_simp', 'pivot_gadget_simp', 'clifford_simp',
    'gadget_simp', 'copy_simp', 'supplementarity_simp',
    'remove_isolated_vertices'
]

rules_to_count = [
    'spider_simp', 'to_gh', 'id_simp',
    'pivot_simp', 'lcomp_simp', 'pivot_simp',
    'pivot_gadget_simp', 'pivot_boundary_simp', 'lcomp_simp', 'bialg_simp', 'bialg_op_simp', 'fuse_simp',
    'remove_self_loop_simp', 'id_simp', 'add_identity_rewrite',
    'gadget_simp', 'supplementarity_simp', 'copy_simp', 'color_change_rewrite', 'hopf_simp', 'z_to_z_box_simp',
    'gadget_phasepoly_simp', 'push_pauli_rewrite', 'euler_expansion_rewrite', 'pi_commute_rewrite', 'phase_free_simp', 'basic_simp', 'reduce_scalar'
]

# 3. Patch the simplify module directly
for rule_name in rules_to_count:
    if hasattr(zx.simplify, rule_name):
        original = getattr(zx.simplify, rule_name)
        setattr(zx.simplify, rule_name, track_rule(original, rule_name))

current_iteration = 0
qubit = 1
depth = 1
p_had: float = 0.2
p_t: float = 0.2
seed: int = 0
clifford: bool = False
# backend = "memgraph"
backend = "simple"
no_hadamard = True
internal = 0

g = GraphMemgraph()
try:
    for qubit in range(2, 15):
        for depth in range(1, 80):
            for seed in range(0, 50):
                for internal in range(0, 4):
                    # delete_all(g)
                    clifford = current_iteration % 2 == 0
                    p_had = (current_iteration % 10) / 10
                    p_t = (current_iteration % 11) / 10
                    no_hadamard = current_iteration % 13 == 0
                    if internal == 0:
                        c = px.generate.CNOT_HAD_PHASE_circuit(qubits=qubit,
                                                               depth=depth,
                                                               p_had=p_had,
                                                               p_t=p_t,
                                                               seed=seed,
                                                               clifford=clifford)
                        g = c.to_graph(backend=backend)
                    elif internal == 1:
                        g = px.generate.cliffordT(qubits=qubit, depth=depth, p_t=p_t, backend=backend, seed=seed)
                    elif internal == 2:
                        g = px.generate.cliffords(qubits=qubit, depth=depth, no_hadamard=no_hadamard, backend=backend,
                                                  seed=seed)
                    elif internal == 3:
                        g = px.generate.cliffordTmeas(qubits=qubit, depth=depth, p_t=p_t, backend=backend, seed=seed)

                    px.full_reduce(g)
                    current_iteration += 1

except EOFError as e:
    print(f"e:", end='\n')
    print(e)

print(f"iter: {current_iteration}", end='\n')
print(f"qubit: {qubit}", end='\n')
print(f"depth: {depth}", end='\n')
print(f"p_had: {p_had}", end='\n')
print(f"p_t: {p_t}", end='\n')
print(f"seed: {seed}", end='\n')
print(f"clifford: {clifford}", end='\n')
print(f"internal: {internal}", end='\n')
print(f"no_hadamard: {no_hadamard}", end='\n')

print(f"\nstats:", end='\n')
print(f"{stats}", end='\n')
# breakpoint()
