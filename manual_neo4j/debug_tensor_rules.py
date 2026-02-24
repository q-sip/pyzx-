import os
import numpy as np
import pyzx as zx
from pyzx.graph.graph_memgraph import GraphMemgraph
from pyzx.utils import EdgeType, VertexType
from pyzx import memgraph_simplify as mem
from pyzx.graph.graph_s import GraphS

print("Start script")

def verify_valid(g_current, rule_name, g_initial):
    g_copy = g_current.copy(backend="simple")
    g_copy.auto_detect_io()
    
    # Compare current state with INITIAL simple graph
    if zx.compare_tensors(g_initial, g_copy, preserve_scalar=False):
        print(f"  [PASS] {rule_name}")
        return True
    else:
        print(f"  [FAIL] {rule_name} BROKE the tensor!")
        return False

def debug_full_reduction_step_by_step():
    print("\n--- Debugging Full Reduction Step-by-Step ---")
    
    seed = 42
    import random
    random.seed(seed)
    np.random.seed(seed)
    
    # Create graph
    print("Generating random Clifford+T graph...")
    try:
        g_s_orig = zx.generate.cliffordT(3, 10, seed=seed)
    except Exception as e:
        print(f"Error generating graph: {e}")
        return

    # Setup Memgraph
    g_mem = GraphMemgraph(graph_id="debug_full_reduce")
    with g_mem._get_session() as session:
        session.run("MATCH (n:Node {graph_id: 'debug_full_reduce'}) DETACH DELETE n")
        
    print("Generating into Memgraph...")
    g_mem = zx.generate.cliffordT(3, 10, backend="memgraph", seed=seed)
    
    print(f"Created Memgraph graph with ID: {g_mem.graph_id}")
    
    # Create corresponding Simple graph (initial state for reference)
    g_s = g_s_orig
    g_s.auto_detect_io() # Should be set by generate, but safe to call
    
    # Verify initial match
    print("Verifying initial state...")
    g_mem_copy = g_mem.copy(backend="simple")
    g_mem_copy.auto_detect_io()
    if not zx.compare_tensors(g_s, g_mem_copy, preserve_scalar=False):
        print("INITIAL STATE MISMATCH! Aborting.")
        return
    print("Initial state MATCH.")

    session = g_mem.session_get
    gid = g_mem.graph_id
    
    # Check to_gh
    if hasattr(mem, 'to_gh'):
        print("Applying to_gh...")
        mem.to_gh(session, gid, quiet=True)
        if not verify_valid(g_mem, "to_gh", g_s): return
    else:
        print("to_gh not found")

    # Loop 
    for i in range(1, 10):
        print(f"Iteration {i}")
        
        print(f"  Running id_simp...")
        num = mem.id_simp(session, gid, quiet=True)
        if num:
            if not verify_valid(g_mem, "id_simp", g_s): return
            
        print(f"  Running spider_simp...")
        num = mem.spider_simp(session, gid, quiet=True)
        if num:
            if not verify_valid(g_mem, "spider_simp", g_s): return
            
        print(f"  Running pivot_simp...")
        num = mem.pivot_simp(session, gid, quiet=True)
        if num:
            if not verify_valid(g_mem, "pivot_simp", g_s): return
            
        print(f"  Running lcomp_simp...")
        num = mem.lcomp_simp(session, gid, quiet=True)
        if num:
            if not verify_valid(g_mem, "lcomp_simp", g_s): return

    print("Completed iterations.")

if __name__ == "__main__":
    debug_full_reduction_step_by_step()
