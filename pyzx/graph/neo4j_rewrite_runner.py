"""
Run Neo4j Cypher rewrites with selectable query variants and optional performance timing.

Use this to:
- Choose which Cypher query variant runs for each rewrite (e.g. SPIDER_FUSION vs SPIDER_FUSION_2).
- Run rewrites with graph_id and collect result counts.
- Measure execution time per query for performance analysis.

Configuration (per run):
- Environment: PYZX_NEO4J_REWRITE_<RULE>=<VARIANT>  e.g. PYZX_NEO4J_REWRITE_SPIDER_FUSION=SPIDER_FUSION_2
- Or pass query_config dict to run_rewrite(s): {"spider_fusion": "SPIDER_FUSION_2"}
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .neo4j_queries import CypherRewrites


# Registry: logical rule name -> list of (variant_id, cypher_string)
# Add new variants here to compare performance.
REWRITE_REGISTRY: Dict[str, List[Tuple[str, str]]] = {
    "hadamard_edge_cancellation": [
        ("HADAMARD_EDGE_CANCELLATION", CypherRewrites.HADAMARD_EDGE_CANCELLATION),
    ],
    "spider_fusion": [
        ("SPIDER_FUSION", CypherRewrites.SPIDER_FUSION),
        ("SPIDER_FUSION_2", CypherRewrites.SPIDER_FUSION_2),
    ],
    "pivot_two_interior_pauli": [
        ("PIVOT_TWO_INTERIOR_PAULI", CypherRewrites.PIVOT_TWO_INTERIOR_PAULI),
    ],
    "pivot_single_interior_pauli": [
        ("PIVOT_SINGLE_INTERIOR_PAULI", CypherRewrites.PIVOT_SINGLE_INTERIOR_PAULI),
    ],
    "local_complement": [
        ("LOCAL_COMPLEMENT", CypherRewrites.LOCAL_COMPLEMENT),
    ],
    "local_complement_full": [
        ("LOCAL_COMPLEMENT_FULL", CypherRewrites.LOCAL_COMPLEMENT_FULL),
    ],
    "gadget_fusion_red_green": [
        ("GADGET_FUSION_RED_GREEN", CypherRewrites.GADGET_FUSION_RED_GREEN),
    ],
    "gadget_fusion_hadamard": [
        ("GADGET_FUSION_HADAMARD", CypherRewrites.GADGET_FUSION_HADAMARD),
    ],
    "gadget_fusion_both": [
        ("GADGET_FUSION_BOTH", CypherRewrites.GADGET_FUSION_BOTH),
    ],
    "pivot_gadget": [
        ("PIVOT_GADGET", CypherRewrites.PIVOT_GADGET),
    ],
    "pivot_boundary": [
        ("PIVOT_BOUNDARY", CypherRewrites.PIVOT_BOUNDARY),
    ],
    "bialgebra_red_green": [
        ("BIALGEBRA_RED_GREEN", CypherRewrites.BIALGEBRA_RED_GREEN),
    ],
    "bialgebra_hadamard": [
        ("BIALGEBRA_HADAMARD", CypherRewrites.BIALGEBRA_HADAMARD),
    ],
    "bialgebra_simplification": [
        ("BIALGEBRA_SIMPLIFICATION", CypherRewrites.BIALGEBRA_SIMPLIFICATION),
    ],
}


def get_variant_for_rule(
    rule_name: str,
    query_config: Optional[Dict[str, str]] = None,
) -> str:
    """
    Resolve which query variant to use for a rule.
    Precedence: query_config[rule_name] > env PYZX_NEO4J_REWRITE_<RULE> > first variant in registry.
    """
    key = rule_name.upper().replace("-", "_")
    env_var = f"PYZX_NEO4J_REWRITE_{key}"
    from_env = os.environ.get(env_var)
    from_config = (query_config or {}).get(rule_name.lower().replace("_", "-")) or (query_config or {}).get(rule_name)

    chosen = from_config or from_env
    variants = REWRITE_REGISTRY.get(rule_name.lower())
    if not variants:
        raise KeyError(f"Unknown rewrite rule: {rule_name}. Known: {list(REWRITE_REGISTRY.keys())}")

    if chosen:
        for vid, _ in variants:
            if vid == chosen or vid.lower() == (chosen or "").lower():
                return vid
        raise ValueError(f"Variant '{chosen}' not in {[v[0] for v in variants]}")
    return variants[0][0]


def get_cypher(rule_name: str, variant_id: Optional[str] = None, query_config: Optional[Dict[str, str]] = None) -> str:
    """Get the Cypher string for a rule (and optional variant)."""
    rule_key = rule_name.lower()
    variants = REWRITE_REGISTRY.get(rule_key)
    if not variants:
        raise KeyError(f"Unknown rewrite rule: {rule_name}")
    vid = variant_id or get_variant_for_rule(rule_name, query_config=query_config)
    for v, cypher in variants:
        if v == vid:
            return cypher.strip()
    raise ValueError(f"Variant '{vid}' not found for rule {rule_name}")


def run_rewrite(
    session_factory,
    graph_id: str,
    rule_name: str,
    variant_id: Optional[str] = None,
    query_config: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    measure_time: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
    """
    Run one Cypher rewrite in a write transaction.

    session_factory: callable that returns a Neo4j session (e.g. graph._get_session).
    graph_id: graph to restrict to (pass as $graph_id if your query uses it).
    rule_name: logical name from REWRITE_REGISTRY (e.g. 'spider_fusion').
    variant_id: optional variant (e.g. 'SPIDER_FUSION_2'); else from config/env/default.
    query_config: optional dict of rule_name -> variant_id for this run.
    params: extra parameters for the query (graph_id is set automatically).
    measure_time: if True, return (result, elapsed_seconds).

    Returns (result_data, elapsed_seconds or None). result_data is the first record as dict, or None.
    """
    cypher = get_cypher(rule_name, variant_id=variant_id, query_config=query_config)
    run_params = dict(params or {})
    run_params["graph_id"] = graph_id

    start = time.perf_counter()
    with session_factory() as session:
        rec = session.execute_write(
            lambda tx: tx.run(cypher, **run_params).single()
        )
    elapsed = time.perf_counter() - start if measure_time else None

    data = rec.data() if rec else None
    return (data, elapsed)


def run_rewrites(
    session_factory,
    graph_id: str,
    rules: Optional[List[str]] = None,
    query_config: Optional[Dict[str, str]] = None,
    measure_time: bool = True,
) -> List[Dict[str, Any]]:
    """
    Run multiple rewrites in sequence. Good for simplification passes and performance comparison.

    rules: list of rule names (default: all registered).
    Returns list of {rule, variant, result, elapsed_sec} for analysis.
    """
    rule_list = rules or list(REWRITE_REGISTRY.keys())
    results = []
    for rule_name in rule_list:
        variant = get_variant_for_rule(rule_name, query_config=query_config)
        data, elapsed = run_rewrite(
            session_factory,
            graph_id,
            rule_name,
            variant_id=variant,
            query_config=query_config,
            measure_time=measure_time,
        )
        results.append({
            "rule": rule_name,
            "variant": variant,
            "result": data,
            "elapsed_sec": elapsed,
        })
    return results
