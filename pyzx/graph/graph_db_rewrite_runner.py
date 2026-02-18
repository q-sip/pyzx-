"""
Graph Database Rewrite Runner for ZX-Calculus Cypher Queries

Execute ZX-diagram rewrites stored in graph databases (Memgraph/Neo4j) with:
- Run individual rewrites or sequences of rules
- Performance timing for each query
- Result collection and statistics

Example usage:
    from neo4j import GraphDatabase
    from pyzx.graph.graph_db_rewrite_runner import run_rewrite, run_rewrites
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    
    def session_factory():
        return driver.session(database="neo4j")
    
    # Run a single rule
    result, elapsed = run_rewrite(
        session_factory,
        graph_id="my_circuit",
        rule_name="spider_fusion_rewrite"
    )
    
    # Run multiple rules
    results = run_rewrites(
        session_factory,
        graph_id="my_circuit",
        rules=["spider_fusion_rewrite", "hadamard_edge_cancellation"],
        measure_time=True
    )
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Callable

from .memgraph_queries import ZXQueryStore


def get_query_store() -> ZXQueryStore:
    """Get the query store instance."""
    return ZXQueryStore()


def list_available_rules() -> List[str]:
    """
    List all available rewrite rule names.
    
    Returns:
        List of rule names that can be used with run_rewrite()
    """
    query_store = get_query_store()
    return query_store.list_rules()


def run_rewrite(
    session_factory: Callable,
    graph_id: str,
    rule_name: str,
    params: Optional[Dict[str, Any]] = None,
    measure_time: bool = True,
    quiet: bool = True,
) -> Tuple[Optional[int], Optional[float]]:
    """
    Execute a single Cypher rewrite rule on a graph in the database.
    
    Args:
        session_factory: Callable that returns a database session (Neo4j/Memgraph)
        graph_id: Identifier of the graph to rewrite
        rule_name: Name of the rewrite rule (e.g., 'spider_fusion_rewrite')
        params: Additional query parameters (graph_id is set automatically)
        measure_time: If True, measure and return execution time
        quiet: If False, print execution details
    
    Returns:
        Tuple of (count, elapsed_seconds) where:
        - count: Number of rewrites applied (or None if query doesn't return count)
        - elapsed_seconds: Execution time (or None if measure_time=False)
    
    Raises:
        ValueError: If rule_name is not found in the query store
    
    Example:
        count, elapsed = run_rewrite(session_factory, "circuit_1", "spider_fusion_rewrite")
        print(f"Applied {count} spider fusions in {elapsed:.3f}s")
    """
    query_store = get_query_store()
    
    # Validate rule name
    if rule_name not in query_store.list_rules():
        available = query_store.list_rules()
        raise ValueError(
            f"Unknown rewrite rule: '{rule_name}'. "
            f"Available rules: {available}"
        )
    
    # Get the Cypher query
    cypher = query_store.get(rule_name)
    
    # Prepare parameters
    run_params = dict(params or {})
    run_params["graph_id"] = graph_id
    
    # Execute the query
    start = time.perf_counter() if measure_time else 0.0
    
    with session_factory() as session:
        result = session.run(cypher, run_params)
        record = result.single()
    
    elapsed = (time.perf_counter() - start) if measure_time else None
    
    # Extract count from result
    count = None
    if record:
        # Try to extract a count value from the first field
        values = record.values()
        if values and len(values) > 0:
            count = values[0]
    
    if not quiet:
        if count is not None:
            print(f"Rule '{rule_name}': {count} rewrites applied", end="")
            if elapsed:
                print(f" ({elapsed:.3f}s)")
            else:
                print()
        elif elapsed:
            print(f"Rule '{rule_name}': completed in {elapsed:.3f}s")
    
    return (count, elapsed)


def run_rewrites(
    session_factory: Callable,
    graph_id: str,
    rules: Optional[List[str]] = None,
    params: Optional[Dict[str, Any]] = None,
    measure_time: bool = True,
    quiet: bool = False,
) -> List[Dict[str, Any]]:
    """
    Execute multiple rewrite rules sequentially on a graph.
    
    This is useful for simplification passes and performance benchmarking.
    
    Args:
        session_factory: Callable that returns a database session
        graph_id: Identifier of the graph to rewrite
        rules: List of rule names to apply (default: all available rules)
        params: Additional query parameters
        measure_time: If True, measure execution time for each rule
        quiet: If False, print progress information
    
    Returns:
        List of dictionaries with keys:
        - 'rule': Rule name
        - 'count': Number of rewrites applied
        - 'elapsed_sec': Execution time (or None if measure_time=False)
        - 'success': True if execution succeeded
    
    Example:
        results = run_rewrites(
            session_factory,
            "circuit_1",
            rules=["spider_fusion_rewrite", "hadamard_edge_cancellation"],
            quiet=False
        )
        
        for r in results:
            print(f"{r['rule']}: {r['count']} rewrites in {r['elapsed_sec']:.3f}s")
    """
    query_store = get_query_store()
    rule_list = rules or query_store.list_rules()
    
    if not quiet:
        print(f"Running {len(rule_list)} rewrite rules on graph '{graph_id}'...")
    
    results = []
    for rule_name in rule_list:
        try:
            count, elapsed = run_rewrite(
                session_factory,
                graph_id,
                rule_name,
                params=params,
                measure_time=measure_time,
                quiet=quiet,
            )
            results.append({
                "rule": rule_name,
                "count": count,
                "elapsed_sec": elapsed,
                "success": True,
            })
        except Exception as e:
            if not quiet:
                print(f"Error running rule '{rule_name}': {e}")
            results.append({
                "rule": rule_name,
                "count": None,
                "elapsed_sec": None,
                "success": False,
                "error": str(e),
            })
    
    if not quiet:
        successful = sum(1 for r in results if r.get("success") is True)
        total_count = sum(r["count"] or 0 for r in results if r.get("success") is True)
        print(f"Completed: {successful}/{len(rule_list)} rules, {total_count} total rewrites")
    
    return results


def run_rewrite_until_complete(
    session_factory: Callable,
    graph_id: str,
    rule_name: str,
    max_iterations: int = 100,
    params: Optional[Dict[str, Any]] = None,
    quiet: bool = True,
) -> Tuple[int, int]:
    """
    Repeatedly apply a rewrite rule until no more matches are found.
    
    Args:
        session_factory: Callable that returns a database session
        graph_id: Identifier of the graph to rewrite
        rule_name: Name of the rewrite rule to apply
        max_iterations: Maximum number of iterations to prevent infinite loops
        params: Additional query parameters
        quiet: If False, print progress information
    
    Returns:
        Tuple of (total_rewrites, iterations)
    
    Example:
        total, iters = run_rewrite_until_complete(
            session_factory,
            "circuit_1",
            "spider_fusion_rewrite"
        )
        print(f"Applied {total} spider fusions in {iters} iterations")
    """
    if not quiet:
        print(f"Applying rule '{rule_name}' until completion...")
    
    total_rewrites = 0
    iteration = 0
    
    for iteration in range(1, max_iterations + 1):
        count, _ = run_rewrite(
            session_factory,
            graph_id,
            rule_name,
            params=params,
            measure_time=False,
            quiet=True,
        )
        
        if count is None or count == 0:
            break
        
        total_rewrites += count
        
        if not quiet:
            print(f"  Iteration {iteration}: {count} rewrites")
    
    if not quiet:
        print(f"Completed after {iteration} iterations: {total_rewrites} total rewrites")
    
    return (total_rewrites, iteration)
