"""
Incremental tensor validation during mem.full_reduce phases.

This script applies mem.full_reduce rules incrementally and validates tensor
equivalence after each step to identify which rule first breaks the original
circuit's tensor representation.

Usage:
    python -m manual_ohtu.tensor_validation_debug [seed] [backend]
    
    seed: Random seed for circuit generation (default: 42)
    backend: Graph backend ('memgraph', 'simple', etc.) (default: 'memgraph')
"""

from time import time
import sys
import pyzx as zx
import pyzx.memgraph_simplify as mem
from pyzx.tensor import compare_tensors


def capture_tensor(circuit):
    """Capture the tensor representation of a circuit."""
    try:
        return circuit.to_tensor()
    except Exception as e:
        print(f"ERROR: Failed to capture circuit tensor: {e}")
        return None


def validate_tensor_match(current_graph, original_tensor, phase_name, rule_name, iteration=None):
    """
    Compare current graph tensor to original circuit tensor.
    
    Returns:
        (matched: bool, error_msg: str or None)
    """
    iter_str = f" (iteration {iteration})" if iteration is not None else ""
    try:
        # Convert current graph to tensor for comparison
        current_tensor = current_graph.to_tensor()
        
        # Compare tensors (allowing global phase differences)
        matched = compare_tensors(current_tensor, original_tensor, preserve_scalar=False)
        
        if matched:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
        
        print(f"  [{phase_name}] {rule_name}{iter_str}: {status}")
        
        if not matched:
            return False, f"Tensor mismatch after {rule_name} in {phase_name}"
        return True, None
        
    except Exception as e:
        print(f"  [{phase_name}] {rule_name}{iter_str}: ERROR - {e}")
        return False, f"Error comparing tensors: {e}"


def run_tensor_validation(seed=42, backend="memgraph"):
    """
    Main validation function that applies mem.full_reduce phases incrementally.
    
    Args:
        seed: Random seed for circuit generation
        backend: Graph backend to use
    """
    print(f"\n{'='*70}")
    print(f"TENSOR VALIDATION DEBUG - mem.full_reduce phases")
    print(f"{'='*70}")
    print(f"Seed: {seed}, Backend: {backend}\n")
    
    # Generate test circuit (matching full_test2.py)
    print("1. Generating test circuit (4 qubits, depth 40)...")
    c = zx.generate.CNOT_HAD_PHASE_circuit(qubits=4, depth=40, seed=seed)
    original_tensor = capture_tensor(c)
    
    if original_tensor is None:
        print("ERROR: Could not capture original circuit tensor")
        return False
    
    print(f"   Original circuit: {len(c.gates)} gates")
    
    # Convert to graph
    print(f"\n2. Converting to {backend} graph...")
    g = c.to_graph(backend=backend)
    graph_id = g.get_graph_id()
    session = g.session_get
    
    print(f"   Graph ID: {graph_id}")
    print(f"   Initial vertices: {len(g.vertices())}")
    print(f"   Initial edges: {len(g.edges())}")
    
    # Verify initial tensor match
    print(f"\n3. Verifying initial graph matches original circuit...")
    matched, err = validate_tensor_match(g, original_tensor, "Initial", "Circuit to Graph")
    if not matched:
        print(f"\nERROR: Initial graph tensor doesn't match circuit!")
        print(f"  {err}")
        return False
    
    # Phase 1: Initial interior clifford simplification
    print(f"\n4. PHASE 1: Initial interior clifford simplification")
    print(f"   {'─'*60}")
    # Phase 1: Broken down into exact steps to trap the math error!
    print(f"\n4. PHASE 1: Initial interior clifford simplification (Deconstructed)")
    print(f"   {'─'*60}")
    
    mem.spider_simp(session, graph_id, quiet=True)
    matched, err = validate_tensor_match(g, original_tensor, "Phase 1", "spider_simp")
    if not matched: return False

    mem.id_simp(session, graph_id, quiet=True)
    matched, err = validate_tensor_match(g, original_tensor, "Phase 1", "id_simp")
    if not matched: return False

    mem.spider_simp(session, graph_id, quiet=True)
    matched, err = validate_tensor_match(g, original_tensor, "Phase 1", "spider_simp (pass 2)")
    if not matched: return False

    mem.pivot_simp(session, graph_id, quiet=True)
    matched, err = validate_tensor_match(g, original_tensor, "Phase 1", "pivot_simp")
    if not matched: return False

    mem.lcomp_simp(session, graph_id, quiet=True)
    matched, err = validate_tensor_match(g, original_tensor, "Phase 1", "lcomp_simp")
    if not matched: return False
    matched, err = validate_tensor_match(g, original_tensor, "Phase 1", "interior_clifford_simp")
    if not matched:
        print(f"\n{'!'*70}")
        print(f"FAILED at Phase 1: {err}")
        print(f"{'!'*70}\n")
        return False
    
    # Phase 2: Initial pivot gadget simplification
    print(f"\n5. PHASE 2: Initial pivot gadget simplification")
    print(f"   {'─'*60}")
    mem.pivot_gadget_simp(session, graph_id, quiet=True)
    matched, err = validate_tensor_match(g, original_tensor, "Phase 2", "pivot_gadget_simp")
    if not matched:
        print(f"\n{'!'*70}")
        print(f"FAILED at Phase 2: {err}")
        print(f"{'!'*70}\n")
        return False
    
    # Phase 3: Main reduction loop
    print(f"\n6. PHASE 3: Main reduction loop")
    print(f"   {'─'*60}")
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n   Loop iteration {iteration}:")
        
        # Clifford simplification (deconstructed)
        clifford_iter = 0
        while True:
            clifford_iter += 1

            mem.interior_clifford_simp(session, graph_id, quiet=True)
            matched, err = validate_tensor_match(
                g,
                original_tensor,
                "Phase 3",
                "clifford_simp/interior_clifford_simp",
                iteration,
            )
            if not matched:
                print(f"\n{'!'*70}")
                print(f"FAILED at Phase 3, iteration {iteration}: {err}")
                print(f"{'!'*70}\n")
                return False

            i2 = mem.pivot_boundary_simp(session, graph_id, quiet=True)
            matched, err = validate_tensor_match(
                g,
                original_tensor,
                "Phase 3",
                "clifford_simp/pivot_boundary_simp",
                iteration,
            )
            if not matched:
                print(f"\n{'!'*70}")
                print(f"FAILED at Phase 3, iteration {iteration}: {err}")
                print(f"{'!'*70}\n")
                return False

            if not i2:
                break
        
        # Gadget simplification
        i = mem.gadget_simp(session, graph_id, quiet=True)
        matched, err = validate_tensor_match(g, original_tensor, "Phase 3", "gadget_simp", iteration)
        if not matched:
            print(f"\n{'!'*70}")
            print(f"FAILED at Phase 3, iteration {iteration}: {err}")
            print(f"{'!'*70}\n")
            return False
        
        # Interior Clifford again
        mem.interior_clifford_simp(session, graph_id, quiet=True)
        matched, err = validate_tensor_match(g, original_tensor, "Phase 3", "interior_clifford_simp", iteration)
        if not matched:
            print(f"\n{'!'*70}")
            print(f"FAILED at Phase 3, iteration {iteration}: {err}")
            print(f"{'!'*70}\n")
            return False
        
        # Copy simplification
        k = mem.copy_simp(session, graph_id, quiet=True)
        matched, err = validate_tensor_match(g, original_tensor, "Phase 3", "copy_simp", iteration)
        if not matched:
            print(f"\n{'!'*70}")
            print(f"FAILED at Phase 3, iteration {iteration}: {err}")
            print(f"{'!'*70}\n")
            return False
        
        # Supplementarity simplification
        l = mem.supplementarity_simp(session, graph_id, quiet=True)
        matched, err = validate_tensor_match(g, original_tensor, "Phase 3", "supplementarity_simp", iteration)
        if not matched:
            print(f"\n{'!'*70}")
            print(f"FAILED at Phase 3, iteration {iteration}: {err}")
            print(f"{'!'*70}\n")
            return False
        
        # Pivot gadget simplification
        j = mem.pivot_gadget_simp(session, graph_id, quiet=True)
        matched, err = validate_tensor_match(g, original_tensor, "Phase 3", "pivot_gadget_simp", iteration)
        if not matched:
            print(f"\n{'!'*70}")
            print(f"FAILED at Phase 3, iteration {iteration}: {err}")
            print(f"{'!'*70}\n")
            return False
        
        # Check termination condition (same as mem.full_reduce)
        if not (i or j or k or l):
            mem.remove_isolated_vertices(session, graph_id, quiet=True)
            print(f"\n   No more gadget rewrites applicable, terminating")
            break
    
    # Final verification
    print(f"\n7. FINAL VALIDATION")
    print(f"   {'─'*60}")
    
    print(f"   Total iterations in Phase 3: {iteration}")
    print(f"   Final vertices: {len(g.vertices())}")
    print(f"   Final edges: {len(g.edges())}")
    
    # Check graph-like property
    is_graph_like = zx.simplify.is_graph_like(g)
    print(f"   Graph is graph-like: {is_graph_like}")
    
    # Final tensor validation
    matched, err = validate_tensor_match(g, original_tensor, "Final", "All phases completed")
    
    if not matched:
        print(f"\n{'!'*70}")
        print(f"ERROR: Tensor mismatch in final graph!")
        print(f"{err}")
        print(f"{'!'*70}\n")
        return False
    
    print(f"\n{'='*70}")
    print(f"✓ SUCCESS: All simplification phases passed tensor validation!")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    backend = sys.argv[2] if len(sys.argv) > 2 else "memgraph"
    
    success = run_tensor_validation(seed=seed, backend=backend)
    sys.exit(0 if success else 1)
