from dataclasses import dataclass
from typing import Any, Callable, Optional, Dict
import time
import pyzx as zx
from pyzx.utils import VertexType, EdgeType

@dataclass
class BackendRunResult:
    name: str
    elapsed_s: float
    return_value: Any
    graph_after: Any
    stats_before: Optional[str]
    stats_after: Optional[str]


@dataclass
class RuleRunResult:
    original_graph: Any
    pyzx: BackendRunResult
    db: BackendRunResult


def _safe_stats(graph: Any) -> Optional[str]:
    try:
        return graph.stats()
    except Exception:
        return None


def _run_pyzx_rule(
    graph: Any,
    rule_fn: Callable[[Any], Any],
    name: str,
    print_results: bool = True,
) -> BackendRunResult:
    stats_before = _safe_stats(graph)

    start = time.perf_counter()
    return_value = rule_fn(graph)
    elapsed_s = time.perf_counter() - start

    stats_after = _safe_stats(graph)

    if print_results:
        print(f"\n{name}")
        print(f"  time:   {elapsed_s:.6f}s")
        print(f"  before: {stats_before}")
        print(f"  after:  {stats_after}")
        print(f"  return: {return_value}")

    return BackendRunResult(
        name=name,
        elapsed_s=elapsed_s,
        return_value=return_value,
        graph_after=graph,
        stats_before=stats_before,
        stats_after=stats_after,
    )


def _run_neo4j_query(
    graph: Any,
    query: str,
    name: str,
    params: Optional[Dict[str, Any]] = None,
    print_results: bool = True,
) -> BackendRunResult:
    """
    Executes a Cypher rewrite query against a GraphNeo4j-like backend.

    Assumes:
    - graph._get_session() exists
    - graph.graph_id exists if your query uses $graph_id
    """
    stats_before = _safe_stats(graph)

    run_params = dict(params or {})
    if "graph_id" not in run_params and hasattr(graph, "graph_id"):
        run_params["graph_id"] = graph.graph_id

    start = time.perf_counter()
    with graph._get_session() as session:
        cursor = session.run(query, run_params)
        try:
            return_value = list(cursor)
        except Exception:
            return_value = None
    elapsed_s = time.perf_counter() - start

    stats_after = _safe_stats(graph)

    if print_results:
        print(f"\n{name}")
        print(f"  time:   {elapsed_s:.6f}s")
        print(f"  before: {stats_before}")
        print(f"  after:  {stats_after}")
        print(f"  return: {return_value}")

    return BackendRunResult(
        name=name,
        elapsed_s=elapsed_s,
        return_value=return_value,
        graph_after=graph,
        stats_before=stats_before,
        stats_after=stats_after,
    )


def run_rule_on_backends(
    *,
    original_graph: Any,
    db_graph: Any,
    pyzx_rule: Callable[[Any], Any],
    db_query: str,
    pyzx_name: str = "pyzx_rule",
    db_name: str = "neo4j_rule",
    db_params: Optional[Dict[str, Any]] = None,
    print_results: bool = True,
) -> RuleRunResult:
    """
    Run the same logical rewrite on:
    - a copied in-memory PyZX graph
    - a DB-backed Neo4j graph via Cypher

    Returns both mutated graphs and timing/results.
    """
    original_copy = original_graph.copy()
    pyzx_graph = original_graph.copy()

    pyzx_result = _run_pyzx_rule(
        graph=pyzx_graph,
        rule_fn=pyzx_rule,
        name=pyzx_name,
        print_results=print_results,
    )

    db_result = _run_neo4j_query(
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

def _normalized_copy(graph: Any) -> Any:
    g = graph.copy()
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

    if check_boundary_counts:
        orig_in = len(original_graph.inputs())
        orig_out = len(original_graph.outputs())

        pyzx_boundary_ok = (
            len(pyzx_graph_after.inputs()) == orig_in
            and len(pyzx_graph_after.outputs()) == orig_out
        )
        db_boundary_ok = (
            len(db_graph_after.inputs()) == orig_in
            and len(db_graph_after.outputs()) == orig_out
        )

        report["pyzx_boundary_ok"] = pyzx_boundary_ok
        report["db_boundary_ok"] = db_boundary_ok

        assert pyzx_boundary_ok, "PyZX rewrite changed boundary counts"
        assert db_boundary_ok, "Neo4j rewrite changed boundary counts"

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
    assert db_vs_original, "Neo4j result is not semantically equal to the original graph"

    if check_backend_agreement:
        db_vs_pyzx = _tensor_equal(
            db_graph_after,
            pyzx_graph_after,
            preserve_scalar=preserve_scalar,
        )
        report["db_vs_pyzx"] = db_vs_pyzx
        assert db_vs_pyzx, "Neo4j result is not semantically equal to the PyZX result"

    if print_results:
        print("\nValidation")
        for k, v in report.items():
            print(f"  {k}: {v}")

    return report

def load_simple_graph_into_neo4j(src_graph, dst_graph):
    """
    Copy a normal in-memory PyZX graph into an existing GraphNeo4j instance.

    src_graph: graph from backend="simple"
    dst_graph: already-created GraphNeo4j, with the graph_id you want to keep
    """
    # Start clean for this graph_id
    with dst_graph._get_session() as session:
        session.run(
            "MATCH (n {graph_id: $graph_id}) DETACH DELETE n",
            {"graph_id": dst_graph.graph_id},
        )

    vmap = {}

    # 1) Copy vertices
    for v in src_graph.vertices():
        new_v = dst_graph.add_vertex(
            src_graph.type(v),
            qubit=src_graph.qubit(v),
            row=src_graph.row(v),
            phase=src_graph.phase(v),
        )
        vmap[v] = new_v

    # 2) Copy boundary lists
    dst_graph.set_inputs([vmap[v] for v in src_graph.inputs()])
    dst_graph.set_outputs([vmap[v] for v in src_graph.outputs()])

    # 3) Copy edges
    for e in src_graph.edges():
        s, t = src_graph.edge_st(e)
        dst_graph.add_edge(
            (vmap[s], vmap[t]),
            edgetype=src_graph.edge_type(e),
        )

    return dst_graph




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
