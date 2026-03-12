from dataclasses import dataclass
from typing import Any, Callable, Optional, Dict, Sequence, Union
import pyzx as zx
from pyzx.utils import VertexType, EdgeType
import re
from fractions import Fraction
from collections import Counter

@dataclass
class BackendRunResult:
    return_value: Any
    graph_after: Any


@dataclass
class RuleRunResult:
    original_graph: Any
    pyzx: BackendRunResult
    db: BackendRunResult

def _graph_signature(graph: Any) -> dict:
    vertices = list(graph.vertices())
    edges = list(graph.edges())

    vertex_type_counts = Counter(int(_as_vertex_type(graph.type(v))) for v in vertices)
    edge_type_counts = Counter(int(_as_edge_type(graph.edge_type(e))) for e in edges)

    phase_multiset = Counter()
    degree_multiset = Counter()
    boundary_degree_multiset = Counter()

    for v in vertices:
        vt = _as_vertex_type(graph.type(v))
        deg = graph.vertex_degree(v)
        degree_multiset[deg] += 1

        if vt == VertexType.BOUNDARY:
            boundary_degree_multiset[deg] += 1
        else:
            p = _phase_to_float_pi_units(_safe_get(lambda: graph.phase(v), 0))
            if p is None:
                p = 0.0
            phase_multiset[_phase_mod_2(p)] += 1

    try:
        n_inputs = len(list(graph.inputs()))
    except Exception:
        n_inputs = 0
    try:
        n_outputs = len(list(graph.outputs()))
    except Exception:
        n_outputs = 0

    return {
        "num_vertices": len(vertices),
        "num_edges": len(edges),
        "num_inputs": n_inputs,
        "num_outputs": n_outputs,
        "vertex_type_counts": dict(sorted(vertex_type_counts.items())),
        "edge_type_counts": dict(sorted(edge_type_counts.items())),
        "degree_multiset": dict(sorted(degree_multiset.items())),
        "boundary_degree_multiset": dict(sorted(boundary_degree_multiset.items())),
        "phase_multiset": dict(sorted(phase_multiset.items())),
    }

def validate_structural_rule_results(
    *,
    original_graph: Any,
    pyzx_graph_after: Any,
    db_graph_after: Any,
    check_boundary_counts: bool = True,
    require_changed: bool = True,
    print_results: bool = True,
) -> dict:
    """
    Validation for fixtures that are not tensor-valid in PyZX, but where we still
    want a deterministic unit test comparing PyZX and DB rewrites structurally.
    """
    report: Dict[str, Any] = {}

    original_sig = _graph_signature(original_graph)
    pyzx_sig = _graph_signature(pyzx_graph_after)
    db_sig = _graph_signature(db_graph_after)

    if check_boundary_counts:
        pyzx_boundary_ok = (
            original_sig["num_inputs"] == pyzx_sig["num_inputs"]
            and original_sig["num_outputs"] == pyzx_sig["num_outputs"]
        )
        db_boundary_ok = (
            original_sig["num_inputs"] == db_sig["num_inputs"]
            and original_sig["num_outputs"] == db_sig["num_outputs"]
        )
        report["pyzx_boundary_ok"] = pyzx_boundary_ok
        report["db_boundary_ok"] = db_boundary_ok

        assert pyzx_boundary_ok, "PyZX rewrite changed boundary counts"
        assert db_boundary_ok, "Benchmark rewrite changed boundary counts"

    backend_agreement = pyzx_sig == db_sig
    report["db_vs_pyzx_structural"] = backend_agreement
    assert backend_agreement, (
        "Benchmark result does not match PyZX structurally.\n"
        f"PyZX: {pyzx_sig}\n"
        f"DB:   {db_sig}"
    )

    if require_changed:
        pyzx_changed = pyzx_sig != original_sig
        db_changed = db_sig != original_sig
        report["pyzx_changed"] = pyzx_changed
        report["db_changed"] = db_changed

        assert pyzx_changed, "PyZX rewrite did not change the graph"
        assert db_changed, "Benchmark rewrite did not change the graph"

    if print_results:
        print("\nStructural Validation")
        for k, v in report.items():
            print(f"  {k}: {v}")

    return report


def _boundary_vertices(graph: Any) -> list:
    out = []
    for v in graph.vertices():
        try:
            if _as_vertex_type(graph.type(v)) == VertexType.BOUNDARY:
                out.append(v)
        except Exception:
            pass
    return out


def _prepare_graph_for_validation(graph: Any) -> Any:
    """
    Make a safe copy for boundary-count checks and tensor comparison.

    Key fix:
    - If the graph contains BOUNDARY vertices but its inputs/outputs are missing
      or incomplete, run auto_detect_io() on the copy.
    """
    g = graph.copy()

    boundaries = _boundary_vertices(g)
    if boundaries:
        try:
            inputs = list(g.inputs())
        except Exception:
            inputs = []
        try:
            outputs = list(g.outputs())
        except Exception:
            outputs = []

        io_set = set(inputs) | set(outputs)

        # If some boundary vertices are not classified as inputs/outputs,
        # tensor conversion will fail. Repair that on the validation copy.
        if len(io_set) != len(boundaries) or any(v not in io_set for v in boundaries):
            try:
                g.auto_detect_io()
            except Exception as e:
                raise ValueError(
                    "Graph contains boundary vertices but inputs/outputs are not "
                    f"properly set, and auto_detect_io() failed: {e}"
                ) from e

    return g


def _normalized_copy(graph: Any) -> Any:
    g = _prepare_graph_for_validation(graph)
    try:
        g.normalize()
    except Exception:
        pass
    return g


def _tensor_equal(g1: Any, g2: Any, preserve_scalar: bool = False) -> bool:
    a = _normalized_copy(g1)
    b = _normalized_copy(g2)
    return zx.compare_tensors(a, b, preserve_scalar=preserve_scalar)


def validate_rule_results(
    *,
    original_graph: Any,
    pyzx_graph_after: Any,
    db_graph_after: Any,
    qubits: int,
    preserve_scalar: bool = False,
    max_tensor_qubits: int = 9,
    check_backend_agreement: bool = True,
    check_boundary_counts: bool = True,
    print_results: bool = True,
) -> dict:
    """
    Validate semantic correctness of both implementations on small cases.
    """
    if qubits > max_tensor_qubits:
        raise ValueError(
            f"Tensor comparison is intended only for small tests. "
            f"Got qubits={qubits}, max_tensor_qubits={max_tensor_qubits}."
        )

    report = {}

    # Use prepared copies here too, so boundary-count checks are based on a
    # tensor-valid interpretation of the graph.
    original_prepared = _prepare_graph_for_validation(original_graph)
    pyzx_prepared = _prepare_graph_for_validation(pyzx_graph_after)
    db_prepared = _prepare_graph_for_validation(db_graph_after)

    if check_boundary_counts:
        orig_in = len(original_prepared.inputs())
        orig_out = len(original_prepared.outputs())

        pyzx_boundary_ok = (
            len(pyzx_prepared.inputs()) == orig_in
            and len(pyzx_prepared.outputs()) == orig_out
        )
        db_boundary_ok = (
            len(db_prepared.inputs()) == orig_in
            and len(db_prepared.outputs()) == orig_out
        )

        report["pyzx_boundary_ok"] = pyzx_boundary_ok
        report["db_boundary_ok"] = db_boundary_ok

        assert pyzx_boundary_ok, "PyZX rewrite changed boundary counts"
        assert db_boundary_ok, "Benchmark rewrite changed boundary counts"

    pyzx_vs_original = _tensor_equal(
        original_graph,
        pyzx_graph_after,
        preserve_scalar=preserve_scalar,
    )
    db_vs_original = _tensor_equal(
        original_graph,
        db_graph_after,
        preserve_scalar=preserve_scalar,
    )

    report["pyzx_vs_original"] = pyzx_vs_original
    report["db_vs_original"] = db_vs_original

    assert pyzx_vs_original, "PyZX result is not semantically equal to the original graph"
    assert db_vs_original, "Benchmark result is not semantically equal to the original graph"

    if check_backend_agreement:
        db_vs_pyzx = _tensor_equal(
            db_graph_after,
            pyzx_graph_after,
            preserve_scalar=preserve_scalar,
        )
        report["db_vs_pyzx"] = db_vs_pyzx
        assert db_vs_pyzx, "Benchmark result is not semantically equal to the PyZX result"

    if print_results:
        print("\nValidation")
        for k, v in report.items():
            print(f"  {k}: {v}")

    return report



def _run_pyzx_rule(
    graph: Any,
    rule_fn: Callable[[Any], Any],
    name: str,
    print_results: bool = True,
) -> BackendRunResult:
    return_value = rule_fn(graph)

    if print_results:
        print(f"\n{name}")
        print(f"  return: {return_value}")

    return BackendRunResult(return_value=return_value, graph_after=graph)

def _run_memgraph_query(
    graph: Any,
    query: Union[str, Sequence[str]],
    name: str,
    params: Optional[Dict[str, Any]] = None,
    print_results: bool = True,
) -> BackendRunResult:
    """
    Executes one or more Cypher rewrite queries against the Memgraph backend.

    If `query` is a list/tuple of queries, they are executed sequentially in the
    same session against the same graph, mirroring multi-step upstream rewrites.
    """
    run_params = dict(params or {})
    if "graph_id" not in run_params and hasattr(graph, "graph_id"):
        run_params["graph_id"] = graph.graph_id

    queries = [query] if isinstance(query, str) else list(query)
    return_value = []

    with graph._get_session() as session:
        for q in queries:
            cursor = session.run(q, run_params)
            return_value.extend(list(cursor))

    if print_results:
        print(f"\n{name}")
        print(f"  return: {return_value}")

    return BackendRunResult(return_value=return_value, graph_after=graph)

def run_rule_on_backends(
    *,
    original_graph: Any,
    db_graph: Any,
    pyzx_rule: Callable[[Any], Any],
    db_query: Union[str, Sequence[str]],
    pyzx_name: str = "pyzx_rule",
    db_name: str = "memgraph_rule",
    db_params: Optional[Dict[str, Any]] = None,
    print_results: bool = True,
) -> RuleRunResult:

    original_copy = original_graph.copy()
    pyzx_graph = original_graph.copy()

    pyzx_result = _run_pyzx_rule(
        graph=pyzx_graph,
        rule_fn=pyzx_rule,
        name=pyzx_name,
        print_results=print_results,
    )

    db_result = _run_memgraph_query(
        graph=db_graph,
        query=db_query,
        name=db_name,
        params=db_params,
        print_results=print_results,
    )

    return RuleRunResult(
        original_graph=original_copy,
        pyzx=pyzx_result,
        db=db_result,
    )


def make_bialgebra_fixture():
    g = zx.Graph(backend="simple")

    # boundaries
    i1 = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
    i2 = g.add_vertex(VertexType.BOUNDARY, qubit=1, row=0)
    o1 = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=3)
    o2 = g.add_vertex(VertexType.BOUNDARY, qubit=1, row=3)

    # A side: Z spiders (t=1)
    a1 = g.add_vertex(VertexType.Z, qubit=0, row=1)
    a2 = g.add_vertex(VertexType.Z, qubit=1, row=1)

    # B side: X spiders (t=2)
    b1 = g.add_vertex(VertexType.X, qubit=0, row=2)
    b2 = g.add_vertex(VertexType.X, qubit=1, row=2)

    # external legs
    g.add_edge((i1, a1), edgetype=EdgeType.SIMPLE)
    g.add_edge((i2, a2), edgetype=EdgeType.SIMPLE)
    g.add_edge((b1, o1), edgetype=EdgeType.SIMPLE)
    g.add_edge((b2, o2), edgetype=EdgeType.SIMPLE)

    # complete bipartite core
    g.add_edge((a1, b1), edgetype=EdgeType.SIMPLE)
    g.add_edge((a1, b2), edgetype=EdgeType.SIMPLE)
    g.add_edge((a2, b1), edgetype=EdgeType.SIMPLE)
    g.add_edge((a2, b2), edgetype=EdgeType.SIMPLE)

    g.set_inputs((i1, i2))
    g.set_outputs((o1, o2))

    return g

def mark_bialgebra_fixture_pattern(db_graph, pattern_id="fixture_bialg"):
    with db_graph._get_session() as session:
        result = session.run(
            """
            MATCH (n:Node)
            WHERE n.graph_id = $graph_id
              AND (
                    (n.t = 1 AND toInteger(n.row) = 1) OR
                    (n.t = 2 AND toInteger(n.row) = 2)
                  )
            SET n.pattern_id = $pattern_id
            RETURN count(n) AS marked
            """,
            {
                "graph_id": db_graph.graph_id,
                "pattern_id": pattern_id,
            },
        ).single()

    return result["marked"]

def assert_boundary_degrees_are_one(graph, name="graph"):
    bad_inputs = [(v, graph.vertex_degree(v)) for v in graph.inputs() if graph.vertex_degree(v) != 1]
    bad_outputs = [(v, graph.vertex_degree(v)) for v in graph.outputs() if graph.vertex_degree(v) != 1]

    if bad_inputs or bad_outputs:
        raise AssertionError(
            f"{name} has invalid boundary degrees. "
            f"bad_inputs={bad_inputs}, bad_outputs={bad_outputs}"
        )

def print_boundary_info(graph, name="graph"):
    print(f"\n{name} boundary info")
    print("inputs:")
    for v in graph.inputs():
        print(
            f"  v={v}, degree={graph.vertex_degree(v)}, type={graph.type(v)}, "
            f"qubit={graph.qubit(v)}, row={graph.row(v)}"
        )
    print("outputs:")
    for v in graph.outputs():
        print(
            f"  v={v}, degree={graph.vertex_degree(v)}, type={graph.type(v)}, "
            f"qubit={graph.qubit(v)}, row={graph.row(v)}"
        )

def make_hadamard_cancel_fixture():
    g = zx.Graph(backend="simple")
    i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
    m = g.add_vertex(VertexType.Z, qubit=0, row=1)      # degree-2 identity spider
    o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=2)

    g.add_edge((i, m), edgetype=EdgeType.HADAMARD)
    g.add_edge((m, o), edgetype=EdgeType.HADAMARD)

    g.set_inputs((i,))
    g.set_outputs((o,))
    return g

def mark_hadamard_cancel_pattern(db_graph, pattern_id="fixture_hh"):
    with db_graph._get_session() as session:
        # mark the middle node (row=1 in the fixture)
        marked_nodes = session.run(
            """
            MATCH (n:Node)
            WHERE n.graph_id = $graph_id AND toInteger(n.row) = 1
            SET n.pattern_id = $pattern_id
            RETURN count(n) AS c
            """,
            {"graph_id": db_graph.graph_id, "pattern_id": pattern_id},
        ).single()["c"]

        # mark the two incident wires so the path matcher sees them
        session.run(
            """
            MATCH (m:Node {graph_id:$graph_id, pattern_id:$pattern_id})-[w:Wire]-(b:Node {graph_id:$graph_id})
            WHERE b.pattern_id IS NULL
            SET w.pattern_id = $pattern_id
            """,
            {"graph_id": db_graph.graph_id, "pattern_id": pattern_id},
        )

    return marked_nodes

def _noop_rule(graph: Any) -> Any:
    """No-op rule for cases where PyZX has no equivalent primitive rewrite."""
    return None


def _count_processed_records(return_value: Any) -> int:
    total = 0
    if not isinstance(return_value, list):
        return total

    count_keys = (
        "patterns_processed",
        "rewrites_applied",
        "fusions_performed",
        "pivot_operations_performed",
        "interior_pauli_removed",
        "merged",
        "marked",
        "c",
    )

    for rec in return_value:
        try:
            keys = set(rec.keys())
        except Exception:
            continue

        for key in count_keys:
            if key in keys:
                try:
                    total += int(rec[key])
                except Exception:
                    pass
                break

    return total

def run_db_rule_only(
    *,
    original_graph: Any,
    db_graph: Any,
    db_query: str,
    db_name: str = "Benchmark_rule",
    db_params: Optional[Dict[str, Any]] = None,
    print_results: bool = True,
) -> RuleRunResult:
    """
    Run a DB rewrite without an in-memory PyZX equivalent.

    - Keeps an untouched copy of the original PyZX graph for semantic comparison.
    - Uses a no-op placeholder for the 'pyzx' side so callers can keep the same
      'RuleRunResult' shape as other tests.
    """
    original_copy = original_graph.copy()

    # "pyzx" placeholder: no mutation, no real timing significance
    pyzx_graph = original_graph.copy()
    pyzx_ret = _noop_rule(pyzx_graph)


    pyzx_result = BackendRunResult(
        return_value=pyzx_ret,
        graph_after=pyzx_graph,
    )

    db_result = _run_memgraph_query(
        graph=db_graph,
        query=db_query,
        name=db_name,
        params=db_params,
        print_results=print_results,
    )

    return RuleRunResult(
        original_graph=original_copy,
        pyzx=pyzx_result,
        db=db_result,
    )


def validate_db_only_rule(
    *,
    original_graph: Any,
    db_graph_after: Any,
    db_return_value: Any,
    qubits: int,
    preserve_scalar: bool = False,
    max_tensor_qubits: int = 9,
    require_fired: bool = True,
    check_boundary_counts: bool = True,
    print_results: bool = True,
) -> dict:
    """
    Validation for DB-only rules:
      - optional: assert the DB rule fired (return_value non-empty / non-zero-ish)
      - optional: boundary counts preserved
      - tensor equivalence: DB vs original

    Returns a report dict similar to validate_rule_results, but DB-only.
    """
    if qubits > max_tensor_qubits:
        raise ValueError(
            f"Tensor comparison is intended only for small tests. "
            f"Got qubits={qubits}, max_tensor_qubits={max_tensor_qubits}."
        )

    report: Dict[str, Any] = {}

    # 1) Did the query fire?
    if require_fired:
        fired = False
        rv = db_return_value

        # Common cases:
        # - list(cursor) => [] when nothing matched
        # - list(cursor) => [Record(...)] when something returned
        # - might also be None on cursor-consumption errors
        if isinstance(rv, list) and len(rv) > 0:
            rec = rv[0]
            if "patterns_processed" in rec.keys():
                fired = int(rec["patterns_processed"]) > 0
            elif "rewrites_applied" in rec.keys():
                fired = int(rec["rewrites_applied"]) > 0
            elif "fusions_performed" in rec.keys():
                fired = int(rec["fusions_performed"]) > 0
            elif "pivot_operations_performed" in rec.keys():
                fired = int(rec["pivot_operations_performed"]) > 0
            elif "interior_pauli_removed" in rec.keys():
                fired = int(rec["interior_pauli_removed"]) > 0
            else:
                fired = len(rv) > 0
        else:
            fired = rv is not None

        report["db_fired"] = fired
        assert fired, "DB rewrite did not fire"

    # 2) Boundary counts preserved?
    if check_boundary_counts:
        orig_in = len(original_graph.inputs())
        orig_out = len(original_graph.outputs())
        db_boundary_ok = (
            len(db_graph_after.inputs()) == orig_in
            and len(db_graph_after.outputs()) == orig_out
        )
        report["db_boundary_ok"] = db_boundary_ok
        assert db_boundary_ok, "Benchmark rewrite changed boundary counts"

    # 3) Semantic equivalence
    db_vs_original = _tensor_equal(
        original_graph,
        db_graph_after,
        preserve_scalar=preserve_scalar,
    )
    report["db_vs_original"] = db_vs_original
    assert db_vs_original, "Benchmark result is not semantically equal to the original graph"

    if print_results:
        print("\nDB-only Validation")
        for k, v in report.items():
            print(f"  {k}: {v}")

    return report

def make_lcomp_fixture():
    r"""
    Minimal local-complementation fixture (1 qubit):
      input --(S)-- n1 --(S)-- output
                    \
                     (H)
                      \
                      center(Z, phase=0.5) --(H)-- n2
                                         \--(H)-- n3
    The lcomp rewrite should:
      - toggle edges among neighbors {n1,n2,n3} (create H edges since none exist)
      - add -center.phase to each neighbor phase
      - delete center
    """
    g = zx.Graph(backend="simple")

    # boundaries
    i = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=0)
    o = g.add_vertex(VertexType.BOUNDARY, qubit=0, row=5)

    # neighbors
    n1 = g.add_vertex(VertexType.Z, qubit=0, row=2, phase=0)
    n2 = g.add_vertex(VertexType.Z, qubit=0, row=3, phase=0)
    n3 = g.add_vertex(VertexType.Z, qubit=0, row=4, phase=0)

    # center (must be ±0.5 for proper ZX local complementation)
    c = g.add_vertex(VertexType.Z, qubit=0, row=1, phase=0.5)

    # wire the "spine"
    g.add_edge((i, n1), edgetype=EdgeType.SIMPLE)
    g.add_edge((n1, o), edgetype=EdgeType.SIMPLE)

    # hadamard star from center
    g.add_edge((c, n1), edgetype=EdgeType.HADAMARD)
    g.add_edge((c, n2), edgetype=EdgeType.HADAMARD)
    g.add_edge((c, n3), edgetype=EdgeType.HADAMARD)

    g.set_inputs((i,))
    g.set_outputs((o,))
    return g


def mark_lcomp_fixture_pattern(db_graph, pattern_id="fixture_lcomp"):
    """
    Marks the 4 internal nodes (center + 3 neighbors) by row.
    Assumes the fixture above: rows 1..4 are exactly those nodes.
    """
    with db_graph._get_session() as session:
        result = session.run(
            """
            MATCH (n:Node)
            WHERE n.graph_id = $graph_id
              AND n.t = 1
              AND toInteger(n.row) IN [1,2,3,4]
            SET n.pattern_id = $pattern_id
            RETURN count(n) AS marked
            """,
            {"graph_id": db_graph.graph_id, "pattern_id": pattern_id},
        ).single()
    return result["marked"]

def _as_vertex_type(t: Any) -> VertexType:
    if isinstance(t, VertexType):
        return t
    # VertexType is an IntEnum, so VertexType(1) -> VertexType.Z, etc.
    return VertexType(int(t))

def _phase_mod_2(p: float) -> float:
    x = float(p) % 2.0
    if abs(x - 2.0) < 1e-12:
        x = 0.0
    return round(x, 12)


def _as_edge_type(t: Any) -> EdgeType:
    if isinstance(t, EdgeType):
        return t
    return EdgeType(int(t))


def _safe_get(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _phase_to_float_pi_units(p: Any) -> Optional[float]:
    if p is None:
        return None
    if isinstance(p, (int, float)):
        return float(p)
    if isinstance(p, Fraction):
        return float(p)

    if isinstance(p, str):
        s = p.strip().replace("Π", "pi").replace("π", "pi").replace(" ", "")
        if s in ("0", "0.0", "+0", "-0"):
            return 0.0

        # "pi", "-pi", "pi/3", "-pi/3", "3pi/2", "-3pi/2"
        m = re.fullmatch(r"([+-]?\d*)?pi(?:/(\d+))?", s)
        if m:
            num_str, den_str = m.group(1), m.group(2)
            if num_str in (None, "", "+"):
                num = 1
            elif num_str == "-":
                num = -1
            else:
                num = int(num_str)
            den = int(den_str) if den_str else 1
            return float(Fraction(num, den))

        # "1/2" etc
        return float(Fraction(s))

    # last resort
    return float(p)


def load_simple_graph(src_graph, dst_graph):
    # Start clean for this graph_id
    with dst_graph._get_session() as session:
        session.run(
            "MATCH (n {graph_id: $graph_id}) DETACH DELETE n",
            {"graph_id": dst_graph.graph_id},
        )

    vmap = {}

    # 1) Copy vertices (coerce types + phases)
    for v in src_graph.vertices():
        ty = _as_vertex_type(src_graph.type(v))

        qubit = _safe_get(lambda: src_graph.qubit(v), None)
        row = _safe_get(lambda: src_graph.row(v), None)
        phase = _phase_to_float_pi_units(_safe_get(lambda: src_graph.phase(v), None))

        new_v = dst_graph.add_vertex(
            ty,
            qubit=qubit,
            row=row,
            phase=phase,
        )
        vmap[v] = new_v

    # 2) Copy boundary lists
    dst_graph.set_inputs([vmap[v] for v in _safe_get(lambda: src_graph.inputs(), [])])
    dst_graph.set_outputs([vmap[v] for v in _safe_get(lambda: src_graph.outputs(), [])])

    # 3) Copy edges (coerce edge type)
    for e in src_graph.edges():
        s, t = src_graph.edge_st(e)
        ety = _as_edge_type(src_graph.edge_type(e))
        dst_graph.add_edge((vmap[s], vmap[t]), edgetype=ety)

    return dst_graph

def make_z_spider_fusion_fixture():
    g = zx.Graph(backend="simple")

    i = g.add_vertex(zx.VertexType.BOUNDARY, 0, 0)
    a = g.add_vertex(zx.VertexType.Z, 0, 1, phase=Fraction(1, 4))
    b = g.add_vertex(zx.VertexType.Z, 0, 2, phase=Fraction(1, 2))
    o = g.add_vertex(zx.VertexType.BOUNDARY, 0, 3)

    g.add_edge((i, a), edgetype=zx.EdgeType.SIMPLE)
    g.add_edge((a, b), edgetype=zx.EdgeType.SIMPLE)
    g.add_edge((b, o), edgetype=zx.EdgeType.SIMPLE)

    g.set_inputs((i,))
    g.set_outputs((o,))
    return g

def make_x_spider_fusion_fixture():
    g = zx.Graph(backend="simple")

    i = g.add_vertex(zx.VertexType.BOUNDARY, 0, 0)
    a = g.add_vertex(zx.VertexType.X, 0, 1, phase=Fraction(1, 4))
    b = g.add_vertex(zx.VertexType.X, 0, 2, phase=Fraction(1, 2))
    o = g.add_vertex(zx.VertexType.BOUNDARY, 0, 3)

    g.add_edge((i, a), edgetype=zx.EdgeType.SIMPLE)
    g.add_edge((a, b), edgetype=zx.EdgeType.SIMPLE)
    g.add_edge((b, o), edgetype=zx.EdgeType.SIMPLE)

    g.set_inputs((i,))
    g.set_outputs((o,))
    return g
