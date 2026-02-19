# PyZX - Python library for quantum circuit rewriting
#        and optimization using the ZX-calculus
# Copyright (C) 2018 - Aleks Kissinger and John van de Wetering

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Graph database-based simplification strategies using Cypher queries.

This module provides high-level simplification algorithms for ZX-diagrams
stored in graph databases (Memgraph/Neo4j), analogous to pyzx.simplify but
using Cypher query rewrites instead of in-memory graph operations.

Main procedures:
- :func:`full_reduce_db`: Full simplification using all available rewrites
- :func:`clifford_simp_db`: Clifford simplifications only
- :func:`interior_clifford_simp`: Interior clifford simplifications
- :func:`gadget_simp_db`: Phase gadget fusion

Each function takes a session_factory and graph_id to identify which graph
in the database to simplify.

Example usage:
    from neo4j import GraphDatabase
    from pyzx.graph.memgraph_simplify import full_reduce_db
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    
    def session_factory():
        return driver.session(database="neo4j")
    
    # Simplify graph with ID "my_circuit"
    full_reduce_db(session_factory, graph_id="my_circuit", quiet=False)
"""

__all__ = [
    'spider_simp', 
    'to_gh',
    'interior_clifford_simp', 
    'clifford_simp_db',
    'pivot_gadget_simp_db',
    'gadget_simp_db',
    'full_reduce_db',
    'reduce_scalar_db',
    'Stats'
]


from typing import Callable, Optional, Dict, Any
from .graph.memgraph_queries import ZXQueryStore
from pyzx.utils import VertexType, EdgeType
from pyzx.graph.base import BaseGraph, VT, ET


class Stats:
    """Statistics tracker for rewrite operations."""
    
    def __init__(self) -> None:
        self.num_rewrites: Dict[str, int] = {}
    
    def count_rewrites(self, rule: str, n: int) -> None:
        """Record that n rewrites of the given rule were applied."""
        if rule in self.num_rewrites:
            self.num_rewrites[rule] += n
        else:
            self.num_rewrites[rule] = n
    
    def __str__(self) -> str:
        s = "GRAPH DB REWRITES\n"
        nt = 0
        for r, n in self.num_rewrites.items():
            nt += n
            s += "%s %s\n" % (str(n).rjust(6), r)
        s += "%s TOTAL" % str(nt).rjust(6)
        return s

def toggle_edge(ty: EdgeType) -> EdgeType:
    """Swap the regular and Hadamard edge types."""
    return EdgeType.HADAMARD if ty == EdgeType.SIMPLE else EdgeType.SIMPLE

def to_gh(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True
) -> None:
    """
    Turns every red node into a green node by applying a Hadamard to the edges incident to red nodes.
    
    This function operates directly on the graph database using a single Cypher query.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: The identifier of the graph to modify
        quiet: If False, print execution details
    """
    query = ZXQueryStore().get("to_gh")
    _execute_query(session_factory, query, {"graph_id": graph_id}, quiet=quiet)

def _execute_query(
    session_factory: Callable,
    query: str,
    params: Optional[Dict[str, Any]] = None,
    quiet: bool = True
) -> int:
    """
    Execute a Cypher query and return the count of changes made.
    
    Args:
        session_factory: Function that returns a database session
        query: Cypher query string to execute
        params: Query parameters (default: empty dict)
        quiet: If False, print execution details
        
    Returns:
        Number of rewrites applied (extracted from query result)
    """
    if params is None:
        params = {}
    
    with session_factory() as session:
        result = session.run(query, params)
        record = result.single()
        
        if record is None:
            return 0
        
        # Try to extract count from various possible return formats
        count = 0
        if hasattr(record, 'values'):
            values = record.values()
            if values and len(values) > 0:
                count = values[0] or 0
        
        if not quiet and count > 0:
            print(f"Applied {count} rewrites")
        
        return count


def spider_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Perform spider fusion on the graph in the database.
    Fuses adjacent spiders of the same color.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    query = queries.get("spider_fusion_rewrite")
    
    # Add graph_id filter to query
    # Note: This assumes your queries support graph_id filtering
    params = {"graph_id": graph_id}
    
    count = _execute_query(session_factory, query, params, quiet)
    
    if stats:
        stats.count_rewrites("spider_fusion", count)
    
    return count > 0


def hadamard_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Cancel adjacent Hadamard gates on the same edge.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    query = queries.get("hadamard_edge_cancellation")
    params = {"graph_id": graph_id}
    
    count = _execute_query(session_factory, query, params, quiet)
    
    if stats:
        stats.count_rewrites("hadamard_cancellation", count)
    
    return count > 0


def pivot_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Apply pivot rewrites (both two-interior and single-interior variants).
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    params = {"graph_id": graph_id}
    
    # Try two-interior pivot first
    query1 = queries.get("pivot_rule_two_interior_pauli")
    count1 = _execute_query(session_factory, query1, params, quiet)
    
    # Try single-interior pivot
    query2 = queries.get("pivot_rule_single_interior_pauli")
    count2 = _execute_query(session_factory, query2, params, quiet)
    
    total_count = count1 + count2
    
    if stats:
        stats.count_rewrites("pivot", total_count)
    
    return total_count > 0


def lcomp_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Apply local complementation rewrites.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    query = queries.get("local_complement_full")
    params = {"graph_id": graph_id}
    
    count = _execute_query(session_factory, query, params, quiet)
    
    if stats:
        stats.count_rewrites("local_complement", count)
    
    return count > 0


def bialgebra_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Apply bialgebra rewrites (red-green, Hadamard, and simplification variants).
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    params = {"graph_id": graph_id}
    
    # Try all bialgebra variants
    query1 = queries.get("bialgebra_red_green")
    count1 = _execute_query(session_factory, query1, params, quiet)
    
    query2 = queries.get("bialgebra_hadamard")
    count2 = _execute_query(session_factory, query2, params, quiet)
    
    query3 = queries.get("bialgebra_simplification")
    count3 = _execute_query(session_factory, query3, params, quiet)
    
    total_count = count1 + count2 + count3
    
    if stats:
        stats.count_rewrites("bialgebra", total_count)
    
    return total_count > 0


def interior_clifford_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Repeatedly apply interior Clifford simplifications until none apply.
    This includes spider fusion, Hadamard cancellation, pivot, and local complementation.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    if not quiet:
        print("Starting interior_clifford_simp...")
    
    applied_any = False
    iteration = 0
    
    while True:
        iteration += 1
        if not quiet:
            print(f"  Iteration {iteration}")
        
        i1 = spider_simp(session_factory, graph_id, quiet, stats)
        i2 = hadamard_simp(session_factory, graph_id, quiet, stats)
        i3 = pivot_simp(session_factory, graph_id, quiet, stats)
        i4 = lcomp_simp(session_factory, graph_id, quiet, stats)
        
        if not (i1 or i2 or i3 or i4):
            break
        
        applied_any = True
    
    if not quiet:
        print(f"Completed interior_clifford_simp after {iteration} iterations")
    
    return applied_any


def pivot_boundary_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Apply pivot rewrites involving boundary vertices.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    query = queries.get("pivot_boundary")
    params = {"graph_id": graph_id}
    
    count = _execute_query(session_factory, query, params, quiet)
    
    if stats:
        stats.count_rewrites("pivot_boundary", count)
    
    return count > 0


def clifford_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Apply Clifford simplifications including interior and boundary pivots.
    Keeps applying rounds of interior_clifford_simp and pivot_boundary_simp
    until neither can be applied.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    if not quiet:
        print("Starting clifford_simp_db...")
    
    applied_any = False
    
    while True:
        i1 = interior_clifford_simp(session_factory, graph_id, quiet, stats)
        i2 = pivot_boundary_simp(session_factory, graph_id, quiet, stats)
        
        if i1 or i2:
            applied_any = True
        
        if not i2:
            break
    
    if not quiet:
        print("Completed clifford_simp_db")
    
    return applied_any


def pivot_gadget_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Apply pivot gadget simplifications.
    This handles phase gadgets using pivot-style rewrites.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    query = queries.get("pivot_gadget")
    params = {"graph_id": graph_id}
    
    count = _execute_query(session_factory, query, params, quiet)
    
    if stats:
        stats.count_rewrites("pivot_gadget", count)
    
    return count > 0


def gadget_simp(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> bool:
    """
    Fuse phase gadgets that act on the same targets.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        True if any rewrites were applied, False otherwise
    """
    queries = ZXQueryStore()
    params = {"graph_id": graph_id}
    
    # Try both gadget fusion variants
    query1 = queries.get("gadget_fusion_red_green")
    count1 = _execute_query(session_factory, query1, params, quiet)
    
    query2 = queries.get("gadget_fusion_hadamard")
    count2 = _execute_query(session_factory, query2, params, quiet)
    
    # Try the combined variant
    query3 = queries.get("gadget_fusion_both")
    count3 = _execute_query(session_factory, query3, params, quiet)
    
    total_count = count1 + count2 + count3
    
    if stats:
        stats.count_rewrites("gadget_fusion", total_count)
    
    return total_count > 0


def reduce_scalar(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> int:
    """
    Simplified reduction strategy for scalar ZX-diagrams.
    Skips boundary pivot operations.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
        
    Returns:
        Number of iterations performed
    """
    if not quiet:
        print("Starting reduce_scalar_db...")
    
    iteration = 0
    while True:
        if not quiet:
            print(f"  Iteration {iteration + 1}")
        
        # Basic simplifications
        i1 = spider_simp(session_factory, graph_id, quiet, stats)
        i2 = hadamard_simp(session_factory, graph_id, quiet, stats)
        i3 = pivot_simp(session_factory, graph_id, quiet, stats)
        i4 = lcomp_simp(session_factory, graph_id, quiet, stats)
        
        if i1 or i2 or i3 or i4:
            iteration += 1
            continue
        
        # Gadget simplifications
        i5 = pivot_gadget_simp(session_factory, graph_id, quiet, stats)
        i6 = gadget_simp(session_factory, graph_id, quiet, stats)
        
        if i5 or i6:
            iteration += 1
            continue
        
        # No more rewrites possible
        break
    
    if not quiet:
        print(f"Completed reduce_scalar_db after {iteration} iterations")
    
    return iteration


def full_reduce(
    session_factory: Callable,
    graph_id: str,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> None:
    """
    The main simplification routine for graph database ZX-diagrams.
    
    This is the database equivalent of pyzx.simplify.full_reduce.
    It uses a combination of Clifford simplifications and gadget strategies.
    
    The algorithm:
    1. Initial interior Clifford simplification
    2. Initial pivot gadget simplification
    3. Main loop:
       - Full Clifford simplification (including boundary)
       - Gadget fusion
       - Interior Clifford simplification
       - Pivot gadget simplification
       - Repeat until no changes
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        quiet: If False, print progress information
        stats: Optional statistics tracker
    """
    if not quiet:
        print(f"Starting full_reduce_db on graph '{graph_id}'...")
    
    # Initial simplifications
    if not quiet:
        print("Phase 1: Initial interior clifford simplification")
    interior_clifford_simp(session_factory, graph_id, quiet, stats)
    
    if not quiet:
        print("Phase 2: Initial pivot gadget simplification")
    pivot_gadget_simp(session_factory, graph_id, quiet, stats)
    
    # Main reduction loop
    if not quiet:
        print("Phase 3: Main reduction loop")
    
    iteration = 0
    while True:
        iteration += 1
        if not quiet:
            print(f"  Main loop iteration {iteration}")
        
        # Full Clifford simplification
        clifford_simp(session_factory, graph_id, quiet, stats)
        
        # Gadget simplification
        i = gadget_simp(session_factory, graph_id, quiet, stats)
        
        # Interior Clifford again
        interior_clifford_simp(session_factory, graph_id, quiet, stats)
        
        # Pivot gadget
        j = pivot_gadget_simp(session_factory, graph_id, quiet, stats)
        
        # Check if any gadget operations were applied
        if not (i or j):
            if not quiet:
                print("No more gadget rewrites applicable, terminating")
            break
    
    if not quiet:
        print(f"Completed full_reduce_db after {iteration} iterations")
        if stats:
            print(stats)


def custom_reduce(
    session_factory: Callable,
    graph_id: str,
    rules: list,
    max_iterations: int = 100,
    quiet: bool = True,
    stats: Optional[Stats] = None
) -> None:
    """
    Apply a custom sequence of rewrite rules iteratively.
    
    Args:
        session_factory: Function that returns a database session
        graph_id: Identifier of the graph to simplify
        rules: List of rule names to apply (e.g., ["spider_fusion", "hadamard_cancellation"])
        max_iterations: Maximum number of iterations to perform
        quiet: If False, print progress information
        stats: Optional statistics tracker
    """
    queries = ZXQueryStore()
    available_rules = queries.list_rules()
    
    # Validate rules
    for rule in rules:
        if rule not in available_rules:
            raise ValueError(f"Unknown rule '{rule}'. Available: {available_rules}")
    
    if not quiet:
        print(f"Starting custom_reduce with rules: {rules}")
    
    for iteration in range(max_iterations):
        if not quiet:
            print(f"  Iteration {iteration + 1}")
        
        applied_any = False
        for rule_name in rules:
            query = queries.get(rule_name)
            params = {"graph_id": graph_id}
            count = _execute_query(session_factory, query, params, quiet)
            
            if count > 0:
                applied_any = True
                if stats:
                    stats.count_rewrites(rule_name, count)
        
        if not applied_any:
            if not quiet:
                print(f"No rewrites applied, terminating after {iteration + 1} iterations")
            break
    
    if not quiet:
        print("Completed custom_reduce")
        if stats:
            print(stats)
