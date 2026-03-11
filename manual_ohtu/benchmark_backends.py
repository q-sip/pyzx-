"""Benchmark full_reduce across graph backends (simple, AGE, memgraph, neo4j).

Run with the 'all' Docker Compose profile to have every backend available:

    docker compose --profile all run --rm pyzx-age python manual_ohtu/benchmark_backends.py

Or with only specific profiles, e.g. just AGE:

    docker compose --profile age-prof run --rm pyzx-age python manual_ohtu/benchmark_backends.py
"""

import os
import sys
from time import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import pyzx as zx
from pyzx.graph.graph_s import GraphS

# ── Backend selection + optional backend probing ─────────────────────────────

ALL_BACKENDS = ["simple", "age", "memgraph", "neo4j"]
DEFAULT_BACKENDS = ["simple", "age"]


def _parse_requested_backends() -> List[str]:
    """Resolve requested backends from CLI or env.

    Priority:
    1) CLI: --backends=simple,age,...
    2) ENV: BENCH_BACKENDS=simple,age,...
    3) default: simple,age
    """
    value = os.getenv("BENCH_BACKENDS", "")
    for arg in sys.argv[1:]:
        if arg.startswith("--backends="):
            value = arg.split("=", 1)[1]
            break

    if not value.strip():
        return DEFAULT_BACKENDS

    requested = [b.strip().lower() for b in value.split(",") if b.strip()]
    unknown = [b for b in requested if b not in ALL_BACKENDS]
    if unknown:
        print(f"[warn] Ignoring unknown backends: {', '.join(unknown)}", file=sys.stderr)
    filtered = [b for b in requested if b in ALL_BACKENDS]
    return filtered if filtered else DEFAULT_BACKENDS


REQUESTED_BACKENDS = _parse_requested_backends()
BACKENDS_AVAILABLE: Dict[str, bool] = {"simple": True}


def _probe_backend(backend: str) -> bool:
    """Probe connectivity/import only for requested backends."""
    if backend == "age":
        try:
            from pyzx.graph.graph_AGE import GraphAGE as _GraphAGE
            probe = _GraphAGE(graph_id="_probe_bench_")
            try:
                probe.delete_graph()
            except Exception:
                pass
            probe.close()
            return True
        except Exception as exc:
            print(f"[warn] AGE backend unavailable: {exc}", file=sys.stderr)
            return False

    if backend == "memgraph":
        try:
            from pyzx.graph.graph_memgraph import GraphMemgraph as _GraphMemgraph  # type: ignore
            probe = _GraphMemgraph(database="memgraph", graph_id="_probe_bench_")
            probe.remove_all_data()
            probe.close()
            return True
        except Exception as exc:
            print(f"[warn] Memgraph backend unavailable: {exc}", file=sys.stderr)
            return False

    if backend == "neo4j":
        try:
            from pyzx.graph.graph_neo4j import GraphNeo4j as _GraphNeo4j  # type: ignore
            probe = _GraphNeo4j()
            probe.close()
            return True
        except Exception as exc:
            print(f"[warn] Neo4j backend unavailable: {exc}", file=sys.stderr)
            return False

    return backend == "simple"


for _backend in REQUESTED_BACKENDS:
    if _backend == "simple":
        BACKENDS_AVAILABLE[_backend] = True
    else:
        BACKENDS_AVAILABLE[_backend] = _probe_backend(_backend)

# Import AGE class lazily only if it is requested and available.
if BACKENDS_AVAILABLE.get("age", False):
    from pyzx.graph.graph_AGE import GraphAGE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reset_age() -> None:
    """Delete and recreate the default AGE graph namespace."""
    try:
        tmp = GraphAGE()
        try:
            tmp.delete_graph()
        except Exception:
            pass
        tmp.close()
    except Exception:
        pass


def _reset_memgraph(g: Any) -> None:
    try:
        g.remove_all_data()
    except Exception:
        pass


def _cleanup_age(g: "GraphAGE") -> None:
    try:
        g.delete_graph()
    except Exception:
        pass
    try:
        g.close()
    except Exception:
        pass


def _cleanup_memgraph(g: Any) -> None:
    try:
        g.remove_all_data()
    except Exception:
        pass
    try:
        g.close()
    except Exception:
        pass


# ── Result container ──────────────────────────────────────────────────────────

@dataclass
class RunResult:
    backend: str
    qubits: int
    depth: int
    v_before: int
    e_before: int
    v_after: int
    e_after: int
    elapsed: float
    correct: Optional[bool]          # None = not checked / error
    stats: Optional[Mapping[str, int]] = None
    error: Optional[str] = field(default=None)


# ── Per-backend runner ────────────────────────────────────────────────────────

# Skip tensor comparison when the combined input/output tensor would exceed this
# many complex128 elements (~1 GiB at 16 bytes each = 67M elements).
_TENSOR_ELEMENT_LIMIT = 67_000_000


def _tensor_safe(qubits: int) -> bool:
    """Return True if compare_tensors is safe for a circuit with this many qubits."""
    # Tensor has shape (2,)*qubits x 2 for inputs and outputs.
    return (2 ** qubits) ** 2 <= _TENSOR_ELEMENT_LIMIT


def _run_simple(circuit: zx.Circuit, qubits: int, depth: int) -> RunResult:
    g = circuit.to_graph(backend="simple")
    v0, e0 = g.num_vertices(), g.num_edges()
    t0 = time()
    zx.full_reduce(g)
    elapsed = time() - t0
    v1, e1 = g.num_vertices(), g.num_edges()
    if _tensor_safe(qubits):
        correct: Optional[bool] = zx.compare_tensors(circuit, g)
    else:
        correct = None  # too large to compare
    return RunResult("simple", qubits, depth, v0, e0, v1, e1, elapsed, correct)


def _run_age(circuit: zx.Circuit, qubits: int, depth: int) -> RunResult:
    g = None
    try:
        graph_id = f"bench_age_{qubits}_{depth}_{int(time() * 1_000_000)}"
        g = GraphAGE(graph_id=graph_id)
        g.reset_stats()
        g_simple = circuit.to_graph(backend="simple")
        for v in g_simple.vertices():
            g.add_vertex_indexed(v)
            g.set_type(v, g_simple.type(v))
            g.set_phase(v, g_simple.phase(v))
            g.set_qubit(v, g_simple.qubit(v))
            g.set_row(v, g_simple.row(v))
        for e in g_simple.edges():
            g.add_edge(e, g_simple.edge_type(e))
        g.set_inputs(g_simple.inputs())
        g.set_outputs(g_simple.outputs())

        v0, e0 = g.num_vertices(), g.num_edges()
        t0 = time()
        try:
            g.begin_batch()
            zx.full_reduce(g)
            g.end_batch()
        except Exception:
            g.rollback_batch()
            raise
        elapsed = time() - t0
        v1, e1 = g.num_vertices(), g.num_edges()
        if _tensor_safe(qubits):
            try:
                correct: Optional[bool] = zx.compare_tensors(circuit, g)
            except MemoryError:
                correct = None
                print(f"      [age] compare_tensors OOM skipped", file=sys.stderr)
            except Exception as ce:
                correct = None
                print(f"      [age] compare_tensors error: {ce}", file=sys.stderr)
        else:
            correct = None  # too large to compare
        return RunResult(
            "age",
            qubits,
            depth,
            v0,
            e0,
            v1,
            e1,
            elapsed,
            correct,
            stats=g.stats(),
        )
    except Exception as exc:
        return RunResult("age", qubits, depth, 0, 0, 0, 0, 0.0, None, error=str(exc))
    finally:
        if g is not None:
            _cleanup_age(g)


def _run_memgraph(circuit: zx.Circuit, qubits: int, depth: int) -> RunResult:
    g = None
    try:
        from pyzx.graph.graph_memgraph import GraphMemgraph  # type: ignore
        from pyzx import memgraph_simplify as _mem_simplify  # type: ignore

        g = GraphMemgraph(database="memgraph", graph_id="_bench_run_")
        _reset_memgraph(g)
        # Populate from circuit
        g_simple = circuit.to_graph(backend="simple")
        # Build memgraph copy vertex by vertex
        for v in g_simple.vertices():
            g.add_vertex_indexed(v)
            g.set_type(v, g_simple.type(v))
            g.set_phase(v, g_simple.phase(v))
            g.set_qubit(v, g_simple.qubit(v))
            g.set_row(v, g_simple.row(v))
        for e in g_simple.edges():
            g.add_edge(e, g_simple.edge_type(e))
        g.set_inputs(g_simple.inputs())
        g.set_outputs(g_simple.outputs())
        v0, e0 = g.num_vertices(), g.num_edges()
        t0 = time()
        _mem_simplify.full_reduce(g)
        elapsed = time() - t0
        v1, e1 = g.num_vertices(), g.num_edges()
        if _tensor_safe(qubits):
            try:
                g_local = g.copy(backend="simple")
                correct: Optional[bool] = zx.compare_tensors(circuit, g_local)
            except (MemoryError, Exception) as ce:
                correct = None
                print(f"      [memgraph] compare_tensors error: {ce}", file=sys.stderr)
        else:
            correct = None
        return RunResult("memgraph", qubits, depth, v0, e0, v1, e1, elapsed, correct)
    except Exception as exc:
        return RunResult("memgraph", qubits, depth, 0, 0, 0, 0, 0.0, None, error=str(exc))
    finally:
        if g is not None:
            _cleanup_memgraph(g)


def _run_neo4j(circuit: zx.Circuit, qubits: int, depth: int) -> RunResult:
    g = None
    try:
        g = circuit.to_graph(backend="neo4j")
        v0, e0 = g.num_vertices(), g.num_edges()
        t0 = time()
        zx.full_reduce(g)
        elapsed = time() - t0
        v1, e1 = g.num_vertices(), g.num_edges()
        try:
            correct: Optional[bool] = zx.compare_tensors(circuit, g)
        except Exception as ce:
            correct = None
        return RunResult("neo4j", qubits, depth, v0, e0, v1, e1, elapsed, correct)
    except Exception as exc:
        return RunResult("neo4j", qubits, depth, 0, 0, 0, 0, 0.0, None, error=str(exc))
    finally:
        if g is not None:
            try:
                g.close()
            except Exception:
                pass


_RUNNER: Dict[str, Callable] = {
    "simple": _run_simple,
    "age": _run_age,
    "memgraph": _run_memgraph,
    "neo4j": _run_neo4j,
}


# ── Table printer ─────────────────────────────────────────────────────────────

COL_BACKEND  = 9
COL_QUBITS   = 6
COL_DEPTH    = 5
COL_CIRCUIT  = 14   # "V_in / E_in"
COL_REDUCED  = 15   # "V_out / E_out"
COL_TIME     = 10
COL_CORRECT  = 7


def _header() -> str:
    return (
        f"{'backend':<{COL_BACKEND}} "
        f"{'qubits':>{COL_QUBITS}} "
        f"{'depth':>{COL_DEPTH}} "
        f"{'V_in/E_in':>{COL_CIRCUIT}} "
        f"{'V_out/E_out':>{COL_REDUCED}} "
        f"{'time(s)':>{COL_TIME}} "
        f"{'correct':>{COL_CORRECT}}"
    )


def _sep() -> str:
    return "-" * (
        COL_BACKEND + COL_QUBITS + COL_DEPTH +
        COL_CIRCUIT + COL_REDUCED + COL_TIME + COL_CORRECT + 6
    )


def _row(r: RunResult) -> str:
    if r.error:
        msg = r.error[:40]
        return (
            f"{r.backend:<{COL_BACKEND}} "
            f"{r.qubits:>{COL_QUBITS}} "
            f"{r.depth:>{COL_DEPTH}} "
            f"  ERROR: {msg}"
        )
    circuit_str  = f"{r.v_before}/{r.e_before}"
    reduced_str  = f"{r.v_after}/{r.e_after}"
    if r.correct is True:
        correct_str = "✓"
    elif r.correct is False:
        correct_str = "✗"
    else:
        correct_str = "big"  # skipped (circuit too large for tensor comparison)
    return (
        f"{r.backend:<{COL_BACKEND}} "
        f"{r.qubits:>{COL_QUBITS}} "
        f"{r.depth:>{COL_DEPTH}} "
        f"{circuit_str:>{COL_CIRCUIT}} "
        f"{reduced_str:>{COL_REDUCED}} "
        f"{r.elapsed:>{COL_TIME}.3f} "
        f"{correct_str:>{COL_CORRECT}}"
    )


# ── Main benchmark ────────────────────────────────────────────────────────────

# Grid to benchmark: (qubits, depth) pairs
BENCHMARK_GRID: List[Tuple[int, int]] = [
    (2, 5),
    (2, 10),
    (2, 20),
    (2, 40),
    (3, 10),
    (3, 20),
    (3, 40),
    (4, 10),
    (4, 20),
    (4, 40),
]

SEED = 42

# Backends to run in this benchmark (only include available ones)
ENABLED_BACKENDS = [b for b in REQUESTED_BACKENDS if BACKENDS_AVAILABLE.get(b, False)]

# ── Correctness detail level: True = full compare_tensors, False = vertex count only
USE_TENSOR_COMPARISON = True


def main() -> None:
    print()
    print("=" * (_sep().__len__()))
    print("  PyZX full_reduce benchmark")
    print(f"  Backends: {', '.join(ENABLED_BACKENDS)}")
    print(f"  Seed: {SEED}  |  Tensor comparison: {USE_TENSOR_COMPARISON}")
    print("=" * (_sep().__len__()))
    print(_header())
    print(_sep())

    all_results: List[RunResult] = []

    for (qubits, depth) in BENCHMARK_GRID:
        import random
        random.seed(SEED)
        circuit = zx.generate.CNOT_HAD_PHASE_circuit(qubits=qubits, depth=depth)

        block_results: List[RunResult] = []
        for backend in ENABLED_BACKENDS:
            runner = _RUNNER[backend]
            result = runner(circuit, qubits, depth)
            block_results.append(result)
            all_results.append(result)
            print(_row(result))

        # Separator between size groups
        print(_sep())

    # ── Summary: speedups relative to 'simple' ────────────────────────────────
    print()
    print("SUMMARY (time relative to 'simple')")
    print(_sep())
    fmt = f"  {{:<{COL_BACKEND}}}  {{:>{COL_QUBITS}}}  {{:>{COL_DEPTH}}}  {{:>10}}  {{:>10}}"
    print(fmt.format("backend", "qubits", "depth", "time(s)", "vs simple"))
    print(_sep())

    # Group by (qubits, depth)
    from itertools import groupby
    key = lambda r: (r.qubits, r.depth)
    for (q, d), group in groupby(all_results, key=key):
        rows = list(group)
        simple_time = next((r.elapsed for r in rows if r.backend == "simple"), None)
        for r in rows:
            if r.error:
                speedup = "ERROR"
            elif simple_time and r.elapsed > 0 and simple_time > 0:
                ratio = r.elapsed / simple_time
                speedup = f"{ratio:.2f}x"
            else:
                speedup = "N/A"
            print(fmt.format(r.backend, r.qubits, r.depth, f"{r.elapsed:.3f}", speedup))
        print()

    age_rows = [r for r in all_results if r.backend == "age" and r.stats]
    if age_rows:
        print("AGE INTERNAL STATS")
        print(_sep())
        print("  qubits depth      reads     writes    commits  cache(h/m)   batches(c/r)")
        print(_sep())
        for r in age_rows:
            s = r.stats or {}
            reads = s.get("reads", 0)
            writes = s.get("writes", 0)
            commits = s.get("commits", 0)
            cache_hits = s.get("cache_hits", 0)
            cache_miss = s.get("cache_misses", 0)
            b_started = s.get("batches_started", 0)
            b_rolled = s.get("batches_rolled_back", 0)
            print(
                f"  {r.qubits:>6} {r.depth:>5} "
                f"{reads:>10} {writes:>10} {commits:>10} "
                f"{cache_hits:>7}/{cache_miss:<7} "
                f"{b_started:>7}/{b_rolled:<7}"
            )


if __name__ == "__main__":
    main()
