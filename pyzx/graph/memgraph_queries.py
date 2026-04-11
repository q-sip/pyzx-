# THIS WAS THE CURRENT IMPLEMENTATION OF QUERIES, WORKS SOMETIMES FOR SEED 42 QUBIT 4 AND DEPTH 40, SOMETIMES ERRORS LIST INDEX. WORKING ON A FIX!!!

#Currently working implementation of queries

import textwrap

class ZXQueryStore:
    """
    Stores ZX-Calculus graph rewrite queries for Memgraph/Neo4j.
    """

    def __init__(self):
        # Mapping friendly snake_case names to the raw Cypher queries
        self._queries = {
            "hadamard_edge_cancellation": self._hadamard_edge_cancellation(),
            "spider_fusion_rewrite": self._spider_fusion_rewrite(),
          "id_simp": self._id_simp(),
          "remove_self_loop_simp": self._remove_self_loop_simp(),
          "remove_isolated_vertices": self._remove_isolated_vertices(),
          "remove_isolated_vertices_single": self._remove_isolated_vertices_single(),
          "remove_isolated_vertices_pair": self._remove_isolated_vertices_pair(),
            "pivot_rule_two_interior_pauli": self._pivot_rule_two_interior_pauli(),
            "pivot_rule_single_interior_pauli": self._pivot_rule_single_interior_pauli(),
            "local_complement_rewrite": self._local_complement_rewrite(),
            "gadget_fusion_red_green": self._gadget_fusion_red_green(),
            "gadget_fusion_hadamard": self._gadget_fusion_hadamard(),
            "pivot_gadget": self._pivot_gadget(),
            "pivot_boundary": self._pivot_boundary(),
            "to_gh": self._to_gh(),
            "bialgebra_red_green": self._bialgebra_red_green(),
            "bialgebra_hadamard": self._bialgebra_hadamard(),
            "bialgebra_simplification": self._bialgebra_simplification(),
            "local_complement_full": self._local_complement_full(),
            "gadget_fusion_both": self._gadget_fusion_both(),
            "spider_fusion_rewrite_2": self._spider_fusion_rewrite_2(),
          "copy_simp": self._copy_simp(),
          "supplementarity_simp": self._supplementarity_simp(),
        }

    def get(self, query_name: str) -> str:
        """Retrieves a specific query by its key name."""
        if query_name not in self._queries:
            raise ValueError(f"Query '{query_name}' not found. Available: {list(self._queries.keys())}")
        return self._queries[query_name]

    def list_rules(self):
        """Returns a list of all available rewrite rule names."""
        return list(self._queries.keys())

    # ==========================================
    # Query Definitions (Private Methods)
    # ==========================================

    def _remove_isolated_vertices_single(self):
        return """
        MATCH (n:Node)
        WHERE n.graph_id = $graph_id AND degree(n) = 0 AND n.t <> 0
        WITH n, n.t AS ty, n.phase AS ph
        DETACH DELETE n
        RETURN count(n) AS count
        """

    def _remove_isolated_vertices_pair(self):
        return """
        MATCH (n:Node)-[r:Wire]-(m:Node)
        WHERE n.graph_id = $graph_id AND m.graph_id = $graph_id
          AND degree(n) = 1 AND degree(m) = 1
          AND id(n) < id(m)
          AND n.t <> 0 AND m.t <> 0
        WITH n, m, r, n.t AS t1, m.t AS t2, n.phase AS p1, m.phase AS p2, r.t AS et
        DETACH DELETE n, m
        RETURN count(r) AS count
        """

    def _remove_isolated_vertices(self):
        # Keep this for backward compatibility if needed, but it shouldn't be used directly via _execute_query
        return self._remove_isolated_vertices_single() + "; " + self._remove_isolated_vertices_pair()


    def _to_gh(self):
        return """
        // Match all Red nodes (t: 2)
        MATCH (n:Node)
        WHERE n.graph_id = $graph_id AND n.t = 2
        WITH collect(n) AS red_nodes
        
        // Toggle edges connecting red nodes to non-red nodes (neighbors not in red_nodes)
        MATCH (u)-[r:Wire]-(v)
        WHERE u IN red_nodes AND NOT v IN red_nodes
        
        SET r.t = CASE r.t 
            WHEN 1 THEN 2 
            WHEN 2 THEN 1 
            ELSE r.t 
        END
        
        WITH red_nodes
        UNWIND red_nodes as n
        SET n.t = 1
        
        RETURN count(n) as nodes_converted
        """

    def _hadamard_edge_cancellation(self):
        return """
        MATCH path = (start:Node)-[:Wire*2..6]-(end:Node)
        WHERE start.graph_id = $graph_id 
          AND end.graph_id = $graph_id
          AND id(start) < id(end)
          AND ALL(node IN nodes(path)[1..-1] WHERE node.graph_id = $graph_id AND size([(node)-[]-() | 1]) = 2)
          AND ALL(edge IN relationships(path) WHERE edge.t = 2)
          AND NOT (size([(start)-[]-() | 1]) = 2 AND ALL(e IN [(start)-[r]-() | r] WHERE e.t = 2))
          AND NOT (size([(end)-[]-() | 1]) = 2 AND ALL(e IN [(end)-[r]-() | r] WHERE e.t = 2))
        
        WITH start, end, path, nodes(path)[1..-1] as nodes_to_delete
        ORDER BY length(path), start.id, end.id
        LIMIT 1
        
        OPTIONAL MATCH (start)-[e_exist:Wire]-(end)
        WITH start, end, nodes_to_delete, e_exist, CASE WHEN e_exist IS NOT NULL THEN e_exist.t ELSE NULL END AS ex_t
        
        UNWIND nodes_to_delete AS node
        DETACH DELETE node
        
        WITH DISTINCT start, end, e_exist, ex_t
        
        FOREACH (_ IN CASE WHEN ex_t IS NULL THEN [1] ELSE [] END |
             CREATE (start)-[:Wire {t: 1, graph_id: $graph_id}]->(end)
        )
        FOREACH (_ IN CASE WHEN ex_t = 2 THEN [1] ELSE [] END |
             SET e_exist.t = 1
             SET start.phase = coalesce(toFloat(start.phase), 0.0) + 1.0
        )
        
        RETURN 1 as patterns_processed
        """

    def _spider_fusion_rewrite(self):
        return """
        MATCH (u:Node)-[e:Wire]-(v:Node)
        WHERE u.graph_id = $graph_id AND v.graph_id = $graph_id
          AND id(u) < id(v)
          AND u.t IN [1, 2] AND v.t IN [1, 2]
          AND ( (e.t = 1 AND u.t = v.t) OR (e.t = 2 AND u.t <> v.t) )
          
        WITH u, v
        ORDER BY u.id, v.id
        LIMIT 1

        OPTIONAL MATCH (v)-[ev:Wire]-(nv:Node)
        WHERE nv <> u
        
        //  Extract ev.t BEFORE v is deleted
        WITH u, v, collect({node: nv, edge_t: ev.t}) as v_neighbors

        SET u.phase = coalesce(toFloat(u.phase), 0.0) + coalesce(toFloat(v.phase), 0.0)
        DETACH DELETE v

        WITH u, v_neighbors
        UNWIND (CASE WHEN size(v_neighbors)=0 THEN [null] ELSE v_neighbors END) AS vn
        WITH u, vn.node AS nv, vn.edge_t AS ev_t
        WHERE nv IS NOT NULL

        OPTIONAL MATCH (u)-[eu:Wire]-(nv)
        WITH u, nv, ev_t, eu, CASE WHEN eu IS NOT NULL THEN eu.t ELSE NULL END AS eu_t

        FOREACH (_ IN CASE WHEN eu IS NULL THEN [1] ELSE [] END |
            CREATE (u)-[:Wire {t: ev_t, graph_id: $graph_id}]->(nv)
        )
        FOREACH (_ IN CASE WHEN eu_t = 2 AND ev_t = 2 THEN [1] ELSE [] END |
            DELETE eu
        )
        FOREACH (_ IN CASE WHEN (eu_t = 1 AND ev_t = 2) OR (eu_t = 2 AND ev_t = 1) THEN [1] ELSE [] END |
            SET eu.t = 1
            SET nv.phase = coalesce(toFloat(nv.phase), 0.0) + 1.0
        )
        
        RETURN 1 as count
        """

    def _id_simp(self):
        return """
        MATCH (v:Node)
        WHERE v.graph_id = $graph_id
          AND v.t = 1  
          AND (v.phase IS NULL OR toFloat(v.phase) = 0.0)
        
        MATCH (v)-[r:Wire]-()
        WITH v, count(r) as d
        WHERE d = 2

        // AND n1 <> n2 protects against self-loops
        MATCH (v)-[e1:Wire]-(n1:Node)
        MATCH (v)-[e2:Wire]-(n2:Node)
        WHERE id(e1) < id(e2) AND n1 <> n2
        
        WITH v, n1, n2, e1, e2
        ORDER BY v.id, n1.id, n2.id
        LIMIT 1

        OPTIONAL MATCH (n1)-[e_exist:Wire]-(n2)
        WITH v, n1, n2, e1, e2, e_exist, CASE WHEN e_exist IS NOT NULL THEN e_exist.t ELSE NULL END AS ex_t,
             CASE WHEN e1.t = e2.t THEN 1 ELSE 2 END AS new_t
             
        DETACH DELETE v
        
        FOREACH (_ IN CASE WHEN ex_t IS NULL THEN [1] ELSE [] END |
             CREATE (n1)-[:Wire {t: new_t, graph_id: $graph_id}]->(n2)
        )
        FOREACH (_ IN CASE WHEN ex_t = 2 AND new_t = 2 THEN [1] ELSE [] END |
             DELETE e_exist
        )
        FOREACH (_ IN CASE WHEN (ex_t = 1 AND new_t = 2) OR (ex_t = 2 AND new_t = 1) THEN [1] ELSE [] END |
             SET e_exist.t = 1
             SET n1.phase = coalesce(toFloat(n1.phase), 0.0) + 1.0
        )

        RETURN 1 AS rewrites_applied
        """

    def _remove_self_loop_simp(self):
        return """
        // Remove self-loops on ZX-like nodes; Hadamard self-loops add a pi phase.
        MATCH (v:Node)-[e:Wire]-(v)
        WHERE v.graph_id = $graph_id AND v.t IN [1, 2]
        WITH v, COLLECT(e) AS loops,
             sum(CASE e.t WHEN 2 THEN 1 ELSE 0 END) AS had_count
      SET v.phase = coalesce(v.phase, 0) + CASE WHEN had_count % 2 = 1 THEN 1 ELSE 0 END
      FOREACH (loop IN loops | DELETE loop)
      RETURN count(DISTINCT v) AS rewrites_applied
        """

    def _pivot_rule_two_interior_pauli(self):
        return """
        MATCH (a:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(b:Node {t: 1})
        WHERE a.graph_id = $graph_id AND b.graph_id = $graph_id
          AND id(a) < id(b)  
          AND a.phase IS NOT NULL 
          AND b.phase IS NOT NULL
          AND toFloat(a.phase) = round(toFloat(a.phase)) 
          AND toFloat(b.phase) = round(toFloat(b.phase))

        // PROTECT PHASE GADGETS AND BOUNDARIES
        WITH a, b, pivot_edge
        OPTIONAL MATCH (a)-[e_bad_a]-(n_bad_a)
        WHERE n_bad_a <> b AND (NOT (n_bad_a.t = 1 AND e_bad_a.t = 2) OR degree(n_bad_a) = 1)
        WITH a, b, pivot_edge, count(n_bad_a) as bad_neighbors_a
        WHERE bad_neighbors_a = 0

        OPTIONAL MATCH (b)-[e_bad_b]-(n_bad_b)
        WHERE n_bad_b <> a AND (NOT (n_bad_b.t = 1 AND e_bad_b.t = 2) OR degree(n_bad_b) = 1)
        WITH a, b, pivot_edge, count(n_bad_b) as bad_neighbors_b
        WHERE bad_neighbors_b = 0

        WITH a, b, pivot_edge
        ORDER BY a.id
        LIMIT 1

        OPTIONAL MATCH (a)-[edge_a:Wire {t: 2}]-(neighbor_a {t: 1})
        WHERE neighbor_a <> b AND NOT EXISTS { MATCH (neighbor_a)-[:Wire]-(b) }
        WITH a, b, pivot_edge, COLLECT(DISTINCT neighbor_a) as neighbors_a

        OPTIONAL MATCH (b)-[edge_b:Wire {t: 2}]-(neighbor_b {t: 1})
        WHERE neighbor_b <> a AND NOT EXISTS { MATCH (neighbor_b)-[:Wire]-(a) } AND NOT neighbor_b IN neighbors_a
        WITH a, b, pivot_edge, neighbors_a, COLLECT(DISTINCT neighbor_b) as neighbors_b

        OPTIONAL MATCH (a)-[edge_shared_a:Wire {t: 2}]-(shared {t: 1})-[edge_shared_b:Wire {t: 2}]-(b)
        WITH a, b, pivot_edge, neighbors_a, neighbors_b, COLLECT(DISTINCT shared) as shared_neighbors

        CALL {
          WITH neighbors_a, neighbors_b
          UNWIND (CASE WHEN size(neighbors_a)=0 THEN [null] ELSE neighbors_a END) AS node_a
          UNWIND (CASE WHEN size(neighbors_b)=0 THEN [null] ELSE neighbors_b END) AS node_b
          WITH node_a, node_b WHERE node_a IS NOT NULL AND node_b IS NOT NULL
          OPTIONAL MATCH (node_a)-[existing:Wire]-(node_b)
          WITH node_a, node_b, existing, CASE WHEN existing IS NOT NULL THEN existing.t ELSE NULL END AS et
          
          FOREACH (_ IN CASE WHEN et IS NULL THEN [1] ELSE [] END | CREATE (node_a)-[:Wire {t: 2, graph_id: $graph_id}]->(node_b) )
          FOREACH (_ IN CASE WHEN et = 2 THEN [1] ELSE [] END | DELETE existing )
          FOREACH (_ IN CASE WHEN et = 1 THEN [1] ELSE [] END | SET node_a.phase = coalesce(toFloat(node_a.phase), 0.0) + 1.0 )
          
          RETURN count(*) as t1
        }


        CALL {
          WITH neighbors_a, shared_neighbors
          UNWIND (CASE WHEN size(neighbors_a)=0 THEN [null] ELSE neighbors_a END) AS node_a
          UNWIND (CASE WHEN size(shared_neighbors)=0 THEN [null] ELSE shared_neighbors END) AS shared_node
          WITH node_a, shared_node WHERE node_a IS NOT NULL AND shared_node IS NOT NULL
          OPTIONAL MATCH (node_a)-[existing:Wire]-(shared_node)
          WITH node_a, shared_node, existing, CASE WHEN existing IS NOT NULL THEN existing.t ELSE NULL END AS et
          
          FOREACH (_ IN CASE WHEN et IS NULL THEN [1] ELSE [] END | CREATE (node_a)-[:Wire {t: 2, graph_id: $graph_id}]->(shared_node) )
          FOREACH (_ IN CASE WHEN et = 2 THEN [1] ELSE [] END | DELETE existing )
          FOREACH (_ IN CASE WHEN et = 1 THEN [1] ELSE [] END | SET node_a.phase = coalesce(toFloat(node_a.phase), 0.0) + 1.0 )
          
          RETURN count(*) as t2
        }

        CALL {
          WITH neighbors_b, shared_neighbors
          UNWIND (CASE WHEN size(neighbors_b)=0 THEN [null] ELSE neighbors_b END) AS node_b
          UNWIND (CASE WHEN size(shared_neighbors)=0 THEN [null] ELSE shared_neighbors END) AS shared_node
          WITH node_b, shared_node WHERE node_b IS NOT NULL AND shared_node IS NOT NULL
          OPTIONAL MATCH (node_b)-[existing:Wire]-(shared_node)
          WITH node_b, shared_node, existing, CASE WHEN existing IS NOT NULL THEN existing.t ELSE NULL END AS et
          
          FOREACH (_ IN CASE WHEN et IS NULL THEN [1] ELSE [] END | CREATE (node_b)-[:Wire {t: 2, graph_id: $graph_id}]->(shared_node) )
          FOREACH (_ IN CASE WHEN et = 2 THEN [1] ELSE [] END | DELETE existing )
          FOREACH (_ IN CASE WHEN et = 1 THEN [1] ELSE [] END | SET node_b.phase = coalesce(toFloat(node_b.phase), 0.0) + 1.0 )
          
          RETURN count(*) as t3
        }
            
        // APPLY PIVOT PHASES
        FOREACH (n IN neighbors_a | SET n.phase = coalesce(toFloat(n.phase), 0.0) + toFloat(b.phase)) 
        FOREACH (n IN neighbors_b | SET n.phase = coalesce(toFloat(n.phase), 0.0) + toFloat(a.phase)) 
        FOREACH (shared_neighbor IN shared_neighbors | 
          SET shared_neighbor.phase = coalesce(toFloat(shared_neighbor.phase), 0.0) + toFloat(a.phase) + toFloat(b.phase) + 1.0
        )

        WITH a, b
        DETACH DELETE a, b

        RETURN COUNT(*) AS pivot_operations_performed
        """

    def _pivot_rule_single_interior_pauli(self):
        return """
        // Interior Pauli spider removal rule
        // Matches a pair (a)-(b) where both are Pauli spiders (t=1, integer phase) connected by Hadamard (t=2)
        // AND one of them (b) is connected to exactly one boundary node.
        MATCH (a:Node {t: 1})-[:Wire {t: 2}]-(b:Node {t: 1})
        WHERE a.graph_id = $graph_id AND b.graph_id = $graph_id
          AND toFloat(a.phase) IS NOT NULL 
          AND toFloat(b.phase) IS NOT NULL
          AND toFloat(a.phase) = round(toFloat(a.phase)) 
          AND toFloat(b.phase) = round(toFloat(b.phase))

        // Check b's connections: should be essentially (a)-[H]-(b)-[?]-(boundary)
        // b must have exactly 2 edges: one to a, one to boundary.
        MATCH (b)-[b_edge:Wire]-(b_neighbor)
        WITH a, b, collect(b_neighbor) as b_neighbors, collect(b_edge) as b_edges
        WHERE size(b_neighbors) = 2
          AND a IN b_neighbors 
          AND any(n IN b_neighbors WHERE n.t = 0) // One neighbor must be boundary

        // Identify the boundary neighbor
        WITH a, b, 
             [n IN b_neighbors WHERE n.t = 0][0] as boundary_vertex,
             [edge IN b_edges WHERE startNode(edge).t = 0 OR endNode(edge).t = 0][0] as boundary_edge

        // Now check 'a'. 'a' must be "interior-like" enough to pivot?
        // Actually, if this is a pivot, 'a' and 'b' form the pivot edge.
        // If 'b' is connected to boundary, 'a' will inherit that connection.
        // We must ensure 'a' doesn't have conflicting boundary connections that would mess up the graph?
        // But pivoting with a boundary node is tricky.

        // The logic below seems to restrict 'a' heavily:
        // "Check that a is connected to at least one t=1 vertex with t=2 edge"
        // "Check that ALL edges from/to a have t=2"
        
        // Let's relax this BUT ensure 'a' is not connected to ANY boundary.
        // If 'a' is connected to boundaries, we might merge boundaries or create multi-edges.
        
        OPTIONAL MATCH (a)-[a_bad_edge]-(a_bad_neighbor)
        WHERE NOT (a_bad_neighbor.t = 1 AND a_bad_edge.t = 2) AND a_bad_neighbor <> b
        WITH a, b, boundary_vertex, boundary_edge, count(a_bad_neighbor) as a_bad_count
        WHERE a_bad_count = 0

        // Take only the first match
        // LIMIT 1

        // Find all neighbors of a (excluding b) and update their phases
        WITH a, b, boundary_vertex, boundary_edge
        MATCH (a)-[:Wire]-(a_neighbor)
        WHERE a_neighbor <> b AND a_neighbor.graph_id = a.graph_id

        // Use FOREACH to update phases (handles empty collections automatically)
        WITH a, b, boundary_vertex, boundary_edge, COLLECT(a_neighbor) as a_neighbors
        FOREACH (neighbor IN a_neighbors |
          SET neighbor.phase = (coalesce(neighbor.phase, 0) + b.phase + a.phase) % 2 // Wait, pivot updates neighbors by a.phase + b.phase + pi?
          // Standard pivot on (u,v): neighbors of u get +v.phase, neighbors of v get +u.phase, shared get +u+v+pi
          // Here b only has 'boundary' neighbor. 'a' has 'a_neighbors'.
          // 'a_neighbors' are neighbors of 'a', so they get +b.phase.
          SET neighbor.phase = (coalesce(neighbor.phase, 0) + b.phase)
        )

        // Connect a_neighbors to boundary?
        // A pivot operates by complementing connectivity between N(u) and N(v).
        // N(b) = {boundary}. N(a) = {a_neighbors}.
        // New edges: (boundary) <-> (each n in a_neighbors).
        // The edge types are toggled. If (a)-(n) was H, and (b)-(boundary) was H, then (n)-(boundary) becomes present (if H*H=I?).
        
        // This rewrite seems to simply move 'a' to 'boundary'?
        // "Connect a to boundary with opposite edge type" --> Wait, the code connects 'a' to boundary?
        // CREATE (a)-[new_connection:Wire]->(boundary_vertex)
        // And deletes b.
        // This effectively ignores 'a_neighbors' connectivity changes!
        // It implies 'a' becomes the new 'b'? 
        
        // This rule seems to be implementing "identity removal" or "copying" if phases are 0?
        // If it's a pivot, nodes should be removed.
        // If the code preserves 'a', it's not a standard pivot removal.
        
        // Let's assume the previous logic was TRYING to implement a specific simplification 
        // that handles a Pauli chain ending at a boundary.
        // (a)-H-(b)-[type]-(boundary)
        // If we pivot (a,b), we remove a,b.
        // Neighbors of a (let's say {n}) connect to neighbors of b ({boundary}).
        // So {n} connected to {boundary}.
        // The original code was:
        // CREATE (a)-[new_connection:Wire]->(boundary_vertex)
        // DETACH DELETE b
        // This keeps 'a'. So 'a' effectively becomes the neighbor of 'boundary'. 
        // This is valid if 'a' was ONLY connected to 'b' and other nodes, and we want to "pull" 'a' to the boundary?
        
        // ACTUALLY, if this rule is "Pivot", both u and v should be removed.
        // If 'a' is preserved, it's NOT a pivot.
        
        // Let's stick to modifying the SAFETY check I added (a_bad_count = 0) 
        // and keep the rest of the logic "as is" assuming it does what's intended for "single interior pauli".
        // The previous code had strict strict checks on "a" having only t=2 edges.
        
        // Returning to the safe "just filter bad neighbors" approach.
        
        RETURN COUNT(*) as interior_pauli_removed
        """

    def _local_complement_rewrite(self):
        return """
        // Find local complementation pattern: Z-spider with ±π/2 phase, all neighbors via Hadamard
        MATCH (center:Node {t: 1})
        WHERE center.graph_id = $graph_id
          AND center.phase IS NOT NULL
          AND (toFloat(center.phase) = 0.5 OR toFloat(center.phase) = -0.5)
        
        // Check for any "bad" connections (boundary nodes, simple edges, or non-Z neighbors)
        OPTIONAL MATCH (center)-[bad_edge]-(bad_neighbor)
        WHERE NOT (bad_neighbor.t = 1 AND bad_edge.t = 2)
        WITH center, count(bad_neighbor) as bad_connections
        WHERE bad_connections = 0

        // Collect all Hadamard-connected Z-spider neighbors
        MATCH (center)-[w:Wire {t: 2}]-(nbr:Node {t: 1})
        WHERE nbr.graph_id = $graph_id
        WITH center, COLLECT(DISTINCT nbr) AS neighbors
        WHERE size(neighbors) > 0
        ORDER BY center.id
        LIMIT 1  
        
        // Update phases (once per center) safely using floats
        WITH center, neighbors
        FOREACH (n IN neighbors |
          SET n.phase = coalesce(toFloat(n.phase), 0.0) - coalesce(toFloat(center.phase), 0.0)
        )
        
        // Toggle edges between all neighbor pairs (local complement)
        WITH center, neighbors, range(0, size(neighbors)-2) AS indices_i
        UNWIND indices_i AS i
        WITH center, neighbors, i, range(i+1, size(neighbors)-1) AS indices_j
        UNWIND indices_j AS j
        WITH center, neighbors, neighbors[i] AS n1, neighbors[j] AS n2
        
        // Explicitly check for existing edges
        OPTIONAL MATCH (n1)-[e:Wire]-(n2)
        WITH center, neighbors, n1, n2, COLLECT(e) as found_edges
        
        // Deletions: Delete all found edges
        FOREACH (edge IN found_edges | DELETE edge)
        
        // Creations: Create one Hadamard edge if none existed
        FOREACH (_ IN CASE WHEN size(found_edges) = 0 THEN [1] ELSE [] END | 
            CREATE (n1)-[:Wire {t: 2, graph_id: $graph_id}]->(n2)
        )
        
        // Remove the center
        WITH DISTINCT center
        DETACH DELETE center
        
        // AGGREGATE to fix the warning
        RETURN count(DISTINCT center) AS num_processed
        """

    def _gadget_fusion_red_green(self):
        return """
        // 1. Find all t=1 nodes with degree 1 (phase spiders)
        MATCH (p:Node {t: 1})
        WHERE p.graph_id = $graph_id AND degree(p) = 1
        WITH p

        // 3. Now that we have the correct 'p' nodes, find their single neighbor 'x', ensuring it's a t=2 node.
        MATCH (p)-[e:Wire {t: 1}]-(x:Node {t: 2})

        // 4. For each gadget, find its external neighbors (t=1 nodes, excluding the phase spider itself).
        WITH p, x
        MATCH (x)-[:Wire]-(n:Node {t: 1})
        WHERE n <> p

        // 5. Group gadgets by their identical set of external neighbors.
        // A sorted list of neighbor IDs serves as a unique key for the group.
        WITH p, x, n
        ORDER BY id(n)
        WITH p, x, COLLECT(id(n)) AS neighbor_key

        // 6. For each group (identified by neighbor_key), collect the phase spiders and their corresponding X-spiders.
        WITH neighbor_key, p, x
        ORDER BY p.id, x.id
        WITH neighbor_key, COLLECT(p) AS phase_spiders, COLLECT(x) AS x_spiders
        // We only care about groups with more than one gadget to fuse.
        WHERE size(phase_spiders) > 1

        // 7. UNWIND the list of phase spiders to access their properties.
        UNWIND phase_spiders AS ps

        // 8. Re-group by neighbor_key to calculate the sum of phases *for each group*.
        WITH
            neighbor_key,
            phase_spiders,
            x_spiders,
            sum(coalesce(ps.phase, 0.0)) AS total_phase

        // 9. Select one gadget to survive and identify the rest for deletion.
        WITH
            total_phase,
            phase_spiders[0] AS survivor_p,
            x_spiders[0] AS survivor_x,
            phase_spiders[1..] AS to_delete_p,
            x_spiders[1..] AS to_delete_x

        // 10. Perform the rewrite:
        // a) Update the phase of the surviving phase spider.
        SET survivor_p.phase = total_phase

        // b) Delete all other gadgets in the group.
        FOREACH (p_del IN to_delete_p | DETACH DELETE p_del)
        FOREACH (x_del IN to_delete_x | DETACH DELETE x_del)

        // Return the number of fusion operations performed.
        RETURN count(*) AS fusions_performed;
        """

    def _gadget_fusion_hadamard(self):
        return """
        // 1. Find all t=1 nodes with degree exactly 1 (phase spiders)
        MATCH (p:Node {t: 1})-[r:Wire]-(neighbor)
        WHERE p.graph_id = $graph_id
        WITH p, count(r) AS degree

        // 2. Filter for nodes that have a degree of exactly 1. These are our phase spiders.
        WHERE degree = 1

        // 3. Now that we have the correct 'p' nodes, find their single neighbor 'z_center',
        //    ensuring it's a Z-spider (t=1) and the connection is a Hadamard edge (t=2).
        MATCH (p)-[e:Wire {t: 2}]-(z_center:Node {t: 1})

        // 4. For each gadget, find its external neighbors: other Z-spiders (t=1) connected
        //    to the central Z-spider via Hadamard edges.
        WITH p, z_center
        MATCH (z_center)-[:Wire {t: 2}]-(n:Node {t: 1})
        WHERE n <> p

        // 5. Group gadgets by their identical set of external neighbors.
        // A sorted list of neighbor IDs serves as a unique key for the group.
        WITH p, z_center, n ORDER BY id(n)
        WITH p, z_center, COLLECT(id(n)) AS neighbor_key

        // 6. For each group (identified by neighbor_key), collect the phase spiders and their corresponding central spiders.
        WITH neighbor_key, p, z_center
        ORDER BY p.id, z_center.id
        WITH neighbor_key, COLLECT(p) AS phase_spiders, COLLECT(z_center) AS central_spiders
        // We only care about groups with more than one gadget to fuse.
        WHERE size(phase_spiders) > 1

        // 7. UNWIND the list of phase spiders to access their properties.
        UNWIND phase_spiders AS ps

        // 8. Re-group by neighbor_key to calculate the sum of phases *for each group*.
        WITH
            neighbor_key,
            phase_spiders,
            central_spiders,
            sum(coalesce(ps.phase, 0.0)) AS total_phase

        // 9. Select one gadget to survive and identify the rest for deletion.
        WITH
            total_phase,
            phase_spiders[0] AS survivor_p,
            central_spiders[0] AS survivor_z,
            phase_spiders[1..] AS to_delete_p,
            central_spiders[1..] AS to_delete_z

        // 10. Perform the rewrite:
        // a) Update the phase of the surviving phase spider.
        SET survivor_p.phase = total_phase

        // b) Delete all other gadgets in the group (both the leaf and the now-redundant central spider).
        FOREACH (p_del IN to_delete_p | DETACH DELETE p_del)
        FOREACH (z_del IN to_delete_z | DETACH DELETE z_del)

        // Return the number of fusion operations performed.
        RETURN count(*) AS fusions_performed;
        """

    def _pivot_gadget(self):
        return """
        // Canonical pivot-gadget rewrite equivalent to
        // match_pivot_gadget + pivot_NOT_REWORKED (single match per call).

        // Candidate pair: z_j is Pauli, z_alpha is non-Pauli, both interior Z-spiders.
        MATCH (z_j:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(z_alpha:Node {t: 1})
        WHERE z_j.graph_id = $graph_id AND z_alpha.graph_id = $graph_id
          AND z_j.phase IS NOT NULL AND z_alpha.phase IS NOT NULL
          AND toFloat(z_j.phase) = round(toFloat(z_j.phase))
          AND NOT (toFloat(z_alpha.phase) = 0.0 OR toFloat(z_alpha.phase) = 1.0)
          AND degree(z_alpha) > 1

        // Neighbors must be Z-spiders (interior condition in matcher).
        OPTIONAL MATCH (z_j)-[e_bad_j:Wire]-(n_bad_j:Node)
        WHERE n_bad_j <> z_alpha AND n_bad_j.t <> 1
        WITH z_j, z_alpha, count(e_bad_j) AS bad_j
        WHERE bad_j = 0

        OPTIONAL MATCH (z_alpha)-[e_bad_a:Wire]-(n_bad_a:Node)
        WHERE n_bad_a <> z_j AND n_bad_a.t <> 1
        WITH z_j, z_alpha, count(e_bad_a) AS bad_a
        WHERE bad_a = 0

        // z_j may not be connected to a phase-gadget leaf (except through pivot edge).
        OPTIONAL MATCH (z_j)-[:Wire]-(leaf:Node {t: 1})
        WHERE leaf <> z_alpha AND degree(leaf) = 1
        WITH z_j, z_alpha, count(leaf) AS leaf_count
        WHERE leaf_count = 0

        // Keep one candidate to avoid overlapping rewrites in one transaction.
        WITH z_j, z_alpha
        ORDER BY toFloat(z_j.phase) DESC, z_j.id, z_alpha.id
        LIMIT 1

        // Compute n0, n1, n2 sets from pivot_NOT_REWORKED.
        OPTIONAL MATCH (z_j)-[:Wire]-(n_j:Node {t: 1})
        WHERE n_j <> z_alpha
        WITH z_j, z_alpha, COLLECT(DISTINCT n_j) AS neighbors_j_all

        OPTIONAL MATCH (z_alpha)-[:Wire]-(n_a:Node {t: 1})
        WHERE n_a <> z_j
        WITH z_j, z_alpha, neighbors_j_all, COLLECT(DISTINCT n_a) AS neighbors_alpha_all

        WITH z_j, z_alpha,
             [n IN neighbors_j_all WHERE n IN neighbors_alpha_all] AS shared_neighbors,
             [n IN neighbors_j_all WHERE NOT n IN neighbors_alpha_all] AS neighbors_j,
             [n IN neighbors_alpha_all WHERE NOT n IN neighbors_j_all] AS neighbors_alpha,
             coalesce(toFloat(z_j.phase), 0.0) AS zj_phase,
             coalesce(toFloat(z_alpha.phase), 0.0) AS alpha_phase

        // Gadgetization pre-step from match_pivot_gadget.
        MATCH (n:Node {graph_id: $graph_id})
        WITH z_j, z_alpha, neighbors_j, neighbors_alpha, shared_neighbors, zj_phase, alpha_phase,
             coalesce(max(n.id), -1) AS max_id
        CREATE (v_gadget:Node {
            t: 1,
            phase: alpha_phase,
            graph_id: $graph_id,
            id: max_id + 1,
            qubit: -2,
            row: z_j.row
        })
        SET z_j.qubit = -1,
            z_alpha.phase = 0.0
        CREATE (z_alpha)-[:Wire {t: 1, graph_id: $graph_id}]->(v_gadget)

        // Phase updates from pivot_NOT_REWORKED.
        FOREACH (n IN neighbors_alpha |
          SET n.phase = coalesce(toFloat(n.phase), 0.0) + zj_phase
        )
        FOREACH (n IN shared_neighbors |
          SET n.phase = coalesce(toFloat(n.phase), 0.0) + zj_phase + 1.0
        )

        // Boundary-like rewiring for m[1][1] = [v_gadget]: move edge from z_alpha to z_j and toggle type.
        WITH z_j, z_alpha, v_gadget, neighbors_j, neighbors_alpha, shared_neighbors
        MATCH (z_alpha)-[zg:Wire]-(v_gadget)
        WITH z_j, z_alpha, v_gadget, neighbors_j, neighbors_alpha, shared_neighbors,
             CASE coalesce(zg.t, 1)
               WHEN 1 THEN 2
               WHEN 2 THEN 1
               ELSE 2
             END AS rewired_t,
             zg
        DELETE zg
        CREATE (z_j)-[:Wire {t: rewired_t, graph_id: $graph_id}]->(v_gadget)

        WITH z_alpha, neighbors_j, neighbors_alpha, shared_neighbors

        CALL {
            WITH neighbors_j, neighbors_alpha
            UNWIND neighbors_j AS a_node
            UNWIND neighbors_alpha AS b_node
            WITH a_node, b_node
            WHERE a_node <> b_node
            OPTIONAL MATCH (a_node)-[e:Wire]-(b_node)
            WITH a_node, b_node, COLLECT(e) AS existing_edges
            WITH a_node, b_node, existing_edges, head([rel IN existing_edges | rel.t]) AS edge_t
            FOREACH (edge IN CASE WHEN edge_t = 2 THEN existing_edges ELSE [] END | DELETE edge)
            FOREACH (_ IN CASE WHEN edge_t IS NULL THEN [1] ELSE [] END |
              CREATE (a_node)-[:Wire {t: 2, graph_id: $graph_id}]->(b_node)
            )
            FOREACH (_ IN CASE WHEN edge_t = 1 THEN [1] ELSE [] END |
              SET a_node.phase = coalesce(toFloat(a_node.phase), 0.0) + 1.0
            )
            RETURN count(*) AS toggles_01
        }

        CALL {
            WITH neighbors_alpha, shared_neighbors
            UNWIND neighbors_alpha AS a_node
            UNWIND shared_neighbors AS b_node
            WITH a_node, b_node
            WHERE a_node <> b_node
            OPTIONAL MATCH (a_node)-[e:Wire]-(b_node)
            WITH a_node, b_node, COLLECT(e) AS existing_edges
            WITH a_node, b_node, existing_edges, head([rel IN existing_edges | rel.t]) AS edge_t
            FOREACH (edge IN CASE WHEN edge_t = 2 THEN existing_edges ELSE [] END | DELETE edge)
            FOREACH (_ IN CASE WHEN edge_t IS NULL THEN [1] ELSE [] END |
              CREATE (a_node)-[:Wire {t: 2, graph_id: $graph_id}]->(b_node)
            )
            FOREACH (_ IN CASE WHEN edge_t = 1 THEN [1] ELSE [] END |
              SET a_node.phase = coalesce(toFloat(a_node.phase), 0.0) + 1.0
            )
            RETURN count(*) AS toggles_12
        }

        CALL {
            WITH neighbors_j, shared_neighbors
            UNWIND neighbors_j AS a_node
            UNWIND shared_neighbors AS b_node
            WITH a_node, b_node
            WHERE a_node <> b_node
            OPTIONAL MATCH (a_node)-[e:Wire]-(b_node)
            WITH a_node, b_node, COLLECT(e) AS existing_edges
            WITH a_node, b_node, existing_edges, head([rel IN existing_edges | rel.t]) AS edge_t
            FOREACH (edge IN CASE WHEN edge_t = 2 THEN existing_edges ELSE [] END | DELETE edge)
            FOREACH (_ IN CASE WHEN edge_t IS NULL THEN [1] ELSE [] END |
              CREATE (a_node)-[:Wire {t: 2, graph_id: $graph_id}]->(b_node)
            )
            FOREACH (_ IN CASE WHEN edge_t = 1 THEN [1] ELSE [] END |
              SET a_node.phase = coalesce(toFloat(a_node.phase), 0.0) + 1.0
            )
            RETURN count(*) AS toggles_02
        }

        // Remove z_alpha (m[1][0] is empty in pivot_NOT_REWORKED).
        WITH z_alpha
        DETACH DELETE z_alpha
        RETURN count(*) AS pivot_operations_performed
        """

    def _pivot_boundary(self):
        return """
        // Find a boundary pivot candidate
        MATCH (z_j:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(z_alpha:Node {t: 1})
        MATCH (z_alpha)-[boundary_wire:Wire]-(boundary_node:Node {t: 0})
        WHERE z_j.graph_id = $graph_id AND z_alpha.graph_id = $graph_id
          AND z_j.phase IS NOT NULL
          AND toFloat(z_j.phase) = round(toFloat(z_j.phase))

        // z_j MUST be interior and have EXACTLY ONE other neighbor (n_j).
        MATCH (z_j)-[e_j:Wire]-(n_j:Node)
        WHERE n_j <> z_alpha
        WITH z_j, z_alpha, boundary_node, boundary_wire, pivot_edge, COLLECT(n_j) AS nj_list, COLLECT(e_j) AS ej_list
        WHERE size(nj_list) = 1
          AND nj_list[0].t = 1 AND ej_list[0].t = 2

        // z_alpha can only have ONE boundary edge; other neighbors must be Z via Hadamard
        OPTIONAL MATCH (z_alpha)-[e_bad_a:Wire]-(n_bad_a:Node)
        WHERE n_bad_a <> z_j AND n_bad_a <> boundary_node AND NOT (n_bad_a.t = 1 AND e_bad_a.t = 2)
        WITH z_j, z_alpha, boundary_node, boundary_wire, pivot_edge, nj_list, count(e_bad_a) AS bad_a
        WHERE bad_a = 0

        // Prevent Concurrency Issues
        WITH z_j, z_alpha, boundary_node, boundary_wire, pivot_edge, nj_list[0] AS n_j
        ORDER BY z_j.id, z_alpha.id, boundary_node.id
        LIMIT 1

        // Gadgetize z_alpha's phase (Extract it so we can safely pivot)
        MATCH (n:Node {graph_id: $graph_id})
        WITH z_j, z_alpha, boundary_node, boundary_wire, pivot_edge, n_j, coalesce(max(n.id), -1) AS max_id
        
        CREATE (v1:Node {
            t: 1,
            phase: coalesce(toFloat(z_alpha.phase), 0.0),
            graph_id: $graph_id,
            id: max_id + 1,
            qubit: -2,
            row: z_alpha.row
        }),
        (v2:Node {
            t: 1,
            phase: 0.0,
            graph_id: $graph_id,
            id: max_id + 2,
            qubit: -1,
            row: z_alpha.row
        })
        CREATE (v1)-[:Wire {t: 2, graph_id: $graph_id}]->(v2)
        CREATE (z_alpha)-[:Wire {t: 2, graph_id: $graph_id}]->(v2)
        
        // Find N(z_alpha) excluding z_j and boundary_node
        WITH z_j, z_alpha, boundary_node, boundary_wire, n_j, v2
        OPTIONAL MATCH (z_alpha)-[:Wire {t: 2}]-(n_a:Node {t: 1})
        WHERE n_a <> z_j
        // neighbors_alpha includes original Z-neighbors AND the new v2 gadget center
        WITH z_j, z_alpha, boundary_node, boundary_wire, n_j, v2, COLLECT(DISTINCT n_a) + [v2] AS neighbors_alpha

        // Update phases (N(z_alpha) gets z_j.phase)
        FOREACH (n IN neighbors_alpha |
          SET n.phase = coalesce(toFloat(n.phase), 0.0) + coalesce(toFloat(z_j.phase), 0.0)
        )

        FOREACH (_ IN CASE WHEN n_j IN neighbors_alpha THEN [1] ELSE [] END |
          SET n_j.phase = coalesce(toFloat(n_j.phase), 0.0) + 1.0
        )

        WITH z_j, z_alpha, boundary_node, boundary_wire, n_j, neighbors_alpha,
             CASE coalesce(boundary_wire.t, 1)
               WHEN 1 THEN 2
               WHEN 2 THEN 1
               ELSE 2
             END AS boundary_new_t
        
        DELETE boundary_wire
        CREATE (boundary_node)-[:Wire {t: boundary_new_t, graph_id: $graph_id}]->(n_j)

        // Connect n_j to neighbors_alpha (Toggle H-edges)
        WITH z_j, z_alpha, n_j, [x IN neighbors_alpha WHERE x <> n_j] AS pure_neighbors_alpha
        
        CALL {
            WITH n_j, pure_neighbors_alpha
            UNWIND pure_neighbors_alpha AS b_node
            OPTIONAL MATCH (n_j)-[e:Wire]-(b_node)
            WITH n_j, b_node, COLLECT(e) AS existing_edges
            WITH n_j, b_node, existing_edges, head([rel IN existing_edges | rel.t]) AS edge_t
            FOREACH (edge IN CASE WHEN edge_t = 2 THEN existing_edges ELSE [] END | DELETE edge)
            FOREACH (_ IN CASE WHEN edge_t IS NULL THEN [1] ELSE [] END |
              CREATE (n_j)-[:Wire {t: 2, graph_id: $graph_id}]->(b_node)
            )
            FOREACH (_ IN CASE WHEN edge_t = 1 THEN [1] ELSE [] END |
              SET n_j.phase = coalesce(toFloat(n_j.phase), 0.0) + 1.0
            )
            RETURN count(*) AS toggles
        }

        // REMOVE BOTH z_j and z_alpha to complete the pivot
        WITH z_j, z_alpha
        DETACH DELETE z_j, z_alpha
        
        RETURN 1 AS pivot_operations_performed
        """

    def _bialgebra_red_green(self):
        return """
        // Find bialgebra pattern: Z-spider (t=1) connected to X-spider (t=2) by simple edge
        MATCH (n1:Node {t: 1})-[w:Wire {t: 1}]->(n2:Node {t: 2})
        WHERE n1.graph_id = $graph_id AND n2.graph_id = $graph_id
        
        WITH n1, n2, w
        LIMIT 10  // Process in small batches due to complexity
        
        // Gather n1's neighbors (except n2)
        OPTIONAL MATCH (n1)-[edge1:Wire]-(nb1:Node)
        WHERE nb1 <> n2
        WITH n1, n2, w, COLLECT({node: nb1, edge: edge1}) AS n1_neighs
        
        // Gather n2's neighbors (except n1)
        OPTIONAL MATCH (n2)-[edge2:Wire]-(nb2:Node)
        WHERE nb2 <> n1
        WITH n1, n2, w, n1_neighs, COLLECT({node: nb2, edge: edge2}) AS n2_neighs
        
        // Create new nodes for n1 (becomes t=2)
        UNWIND n1_neighs AS conn1
        CREATE (new_n1:Node {t: 2, phase: coalesce(n1.phase, 0), graph_id: $graph_id})
        CREATE (new_n1)-[:Wire {t: conn1.edge.t, graph_id: $graph_id}]-(conn1.node)
        WITH n1, n2, w, COLLECT(new_n1) AS new_n1s, n2_neighs
        
        // Create new nodes for n2 (becomes t=1)
        UNWIND n2_neighs AS conn2
        CREATE (new_n2:Node {t: 1, phase: coalesce(n2.phase, 0), graph_id: $graph_id})
        CREATE (new_n2)-[:Wire {t: conn2.edge.t, graph_id: $graph_id}]-(conn2.node)
        WITH n1, n2, new_n1s, COLLECT(new_n2) AS new_n2s
        
        // Create all-to-all connections between new nodes
        FOREACH (n1x IN new_n1s |
            FOREACH (n2x IN new_n2s |
                CREATE (n1x)-[:Wire {t: 1, graph_id: $graph_id}]->(n2x)
            )
        )
        
        // Delete original nodes
        WITH n1, n2
        DETACH DELETE n1, n2
        
        RETURN COUNT(*) AS rewrites_applied
        """

    def _bialgebra_hadamard(self):
        return """
        // Find bialgebra pattern: two Z-spiders connected by Hadamard edge
        MATCH (n1:Node {t: 1})-[w:Wire {t: 2}]->(n2:Node {t: 1})
        WHERE n1.graph_id = $graph_id AND n2.graph_id = $graph_id
        
        WITH n1, n2, w
        LIMIT 10  // Process in small batches
        
        // Gather n1's neighbors (except n2)
        OPTIONAL MATCH (n1)-[edge1:Wire]-(nb1:Node)
        WHERE nb1 <> n2
        WITH n1, n2, w, COLLECT({node: nb1, edge: edge1}) AS n1_neighs
        
        // Gather n2's neighbors (except n1)
        OPTIONAL MATCH (n2)-[edge2:Wire]-(nb2:Node)
        WHERE nb2 <> n1
        WITH n1, n2, w, n1_neighs, COLLECT({node: nb2, edge: edge2}) AS n2_neighs
        
        // Create new X-spiders (t=2) for n1's neighbors
        UNWIND n1_neighs AS conn1
        CREATE (new_n1:Node {t: 2, phase: 0, graph_id: $graph_id})
        CREATE (new_n1)-[:Wire {t: conn1.edge.t, graph_id: $graph_id}]-(conn1.node)
        WITH n1, n2, w, COLLECT(new_n1) AS new_n1s, n2_neighs
        
        // Create new Z-spiders (t=1) for n2's neighbors, flip Hadamard edges
        UNWIND n2_neighs AS conn2
        CREATE (new_n2:Node {t: 1, phase: 0, graph_id: $graph_id})
        WITH new_n2, conn2, n1, n2, new_n1s, n2_neighs
        // Flip edge type: Hadamard (2) becomes Simple (1), Simple (1) becomes Hadamard (2)
        CREATE (new_n2)-[:Wire {t: CASE conn2.edge.t WHEN 1 THEN 2 ELSE 1 END, graph_id: $graph_id}]-(conn2.node)
        WITH n1, n2, new_n1s, COLLECT(new_n2) AS new_n2s
        
        // Create all-to-all simple connections between new nodes
        FOREACH (n1x IN new_n1s |
            FOREACH (n2x IN new_n2s |
                CREATE (n1x)-[:Wire {t: 1, graph_id: $graph_id}]->(n2x)
            )
        )
        
        // Delete original nodes
        WITH n1, n2
        DETACH DELETE n1, n2
        
        RETURN COUNT(*) AS rewrites_applied
        """

    def _bialgebra_simplification(self):
        return """
        // Find complete bipartite subgraph K_{m,n} where m,n >= 2
        // All Z-spiders (t=1) connect to all X-spiders (t=2) with simple edges
        // All spiders are phase-free, each has exactly one external connection
        
        // Step 1: Find a seed - phase-free Z-spider with multiple X-neighbors
        MATCH (z_seed:Node {t: 1, phase: 0})
        WHERE z_seed.graph_id = $graph_id
        
        // Collect all its X-neighbors (must be phase-free, connected by simple edge)
        WITH z_seed
        MATCH (z_seed)-[:Wire {t: 1}]-(x_cand:Node {t: 2, phase: 0})
        WHERE x_cand.graph_id = $graph_id
        WITH z_seed, COLLECT(DISTINCT x_cand) AS x_group
        WHERE size(x_group) >= 2
        
        // Step 2: Find all Z-spiders that connect to ALL these X-spiders (complete bipartite)
        WITH x_group
        MATCH (z_cand:Node {t: 1, phase: 0})
        WHERE z_cand.graph_id = $graph_id
        
        // Check each z_cand connects to all x's in x_group with simple edges
        WITH x_group, z_cand
        WHERE size([(z_cand)-[:Wire {t: 1}]-(x) WHERE x IN x_group | x]) = size(x_group)
        
        WITH x_group, COLLECT(DISTINCT z_cand) AS z_group
        WHERE size(z_group) >= 2
        
        // Step 3: Verify X-spiders also form complete bipartite (each X connects to all Z's)
        WITH z_group, x_group
        WHERE ALL(x IN x_group WHERE 
            size([(x)-[:Wire {t: 1}]-(z) WHERE z IN z_group | z]) = size(z_group)
        )
        
        // Step 4: Verify external connection requirement
        // Each Z has degree = |x_group| + 1, each X has degree = |z_group| + 1
        WITH z_group, x_group
        WHERE ALL(z IN z_group WHERE size([(z)-[:Wire]-(n) | n]) = size(x_group) + 1)
          AND ALL(x IN x_group WHERE size([(x)-[:Wire]-(n) | n]) = size(z_group) + 1)
        
        // Only process one match at a time
        WITH z_group, x_group
        LIMIT 1
        
        // Step 5: Calculate positions for new nodes
        WITH z_group, x_group,
             reduce(q = 0.0, v IN z_group | q + v.qubit) / size(z_group) AS avg_qubit_z,
             reduce(r = 0.0, v IN z_group | r + v.row) / size(z_group) AS avg_row_z,
             reduce(q = 0.0, v IN x_group | q + v.qubit) / size(x_group) AS avg_qubit_x,
             reduce(r = 0.0, v IN x_group | r + v.row) / size(x_group) AS avg_row_x
        
        // Step 6: Create new collapsed nodes
        // New Z-spider replaces the X-group, new X-spider replaces the Z-group
        CREATE (new_z:Node {t: 1, phase: 0, graph_id: $graph_id, qubit: avg_qubit_x, row: avg_row_x})
        CREATE (new_x:Node {t: 2, phase: 0, graph_id: $graph_id, qubit: avg_qubit_z, row: avg_row_z})
        CREATE (new_z)-[:Wire {t: 1, graph_id: $graph_id}]-(new_x)
        
        // Step 7: Reconnect external edges from X-spiders to new Z-spider
        WITH z_group, x_group, new_z, new_x
        UNWIND x_group AS old_x
        OPTIONAL MATCH (old_x)-[e:Wire]-(external)
        WHERE NOT external IN z_group
        WITH z_group, x_group, new_z, new_x, external, e.t AS edge_type
        WHERE external IS NOT NULL
        MERGE (new_z)-[:Wire {t: edge_type, graph_id: $graph_id}]-(external)
        
        // Step 8: Reconnect external edges from Z-spiders to new X-spider
        WITH z_group, x_group, new_z, new_x
        UNWIND z_group AS old_z
        OPTIONAL MATCH (old_z)-[e:Wire]-(external)
        WHERE NOT external IN x_group
        WITH z_group, x_group, new_z, new_x, external, e.t AS edge_type
        WHERE external IS NOT NULL
        MERGE (new_x)-[:Wire {t: edge_type, graph_id: $graph_id}]-(external)
        
        // Step 9: Delete old nodes
        WITH z_group, x_group, new_z, new_x
        FOREACH (node IN z_group + x_group | DETACH DELETE node)
        
        RETURN 1 AS rewrites_applied
        """

    def _local_complement_full(self):
        return """
        MATCH (center:Node)
        WHERE center.graph_id = $graph_id
          AND center.t = 1
          AND (center.phase = 0.5 OR center.phase = -0.5 OR center.phase = 1.5)

        // PROTECT GADGETS
        OPTIONAL MATCH (center)-[bad_edge]-(bad_neighbor)
        WHERE NOT (bad_neighbor.t = 1 AND bad_edge.t = 2) OR degree(bad_neighbor) = 1
        WITH center, count(bad_neighbor) as bad_connections
        WHERE bad_connections = 0

        MATCH (center)-[w:Wire {t:2}]-(nbr:Node {t:1})
        WITH center, collect(distinct nbr) as neighbors
        WHERE size(neighbors) > 0 AND degree(center) = size(neighbors)

        WITH center, neighbors
        ORDER BY center.id
        LIMIT 1

        FOREACH (n IN neighbors | 
            SET n.phase = coalesce(toFloat(n.phase), 0.0) - coalesce(toFloat(center.phase), 0.0)
        )

        WITH center, neighbors
        DETACH DELETE center

        WITH neighbors
        WHERE size(neighbors) >= 2
        UNWIND range(0, size(neighbors)-2) as i
        UNWIND range(i+1, size(neighbors)-1) as j
        WITH neighbors[i] as n1, neighbors[j] as n2

        OPTIONAL MATCH (n1)-[e:Wire]-(n2)
        WITH n1, n2, e, CASE WHEN e IS NOT NULL THEN e.t ELSE NULL END AS et
        
        FOREACH (_ IN CASE WHEN et IS NULL THEN [1] ELSE [] END |
             CREATE (n1)-[:Wire {t: 2, graph_id: $graph_id}]->(n2)
        )
        FOREACH (_ IN CASE WHEN et = 2 THEN [1] ELSE [] END |
             DELETE e
        )
        FOREACH (_ IN CASE WHEN et = 1 THEN [1] ELSE [] END |
             SET n1.phase = coalesce(toFloat(n1.phase), 0.0) + 1.0
        )

        RETURN 1 as count
        """

    def _gadget_fusion_both(self):
        return """
        // Combined Phase Gadget Fusion: handles both Z-gadgets (t=2 edges) and X-gadgets (t=1 edges)

        // 1. Find all degree-1 phase spiders (t=1, degree=1)
        MATCH (p:Node {t: 1})
        WHERE p.graph_id = $graph_id AND degree(p) = 1

        // 2. Find their single neighbor (the gadget center), which can be either Z (t=1) or X (t=2)
        MATCH (p)-[e:Wire]-(center:Node)
        WHERE (center.t = 1 AND e.t = 2) OR (center.t = 2 AND e.t = 1)

        // 3. Collect the edge type to distinguish Z-gadgets from X-gadgets
        WITH p, center, e.t AS edge_type

        // 4. For each gadget, find its external neighbors
        MATCH (center)-[:Wire]-(n:Node {t: 1})
        WHERE n <> p

        // 5. Group gadgets by their center type, edge type, and identical set of external neighbors
        WITH p, center, edge_type, n
        ORDER BY id(n)
        WITH p, center, edge_type, COLLECT(id(n)) AS neighbor_key

        // 6. Group by (edge_type, neighbor_key) to separate Z-gadgets from X-gadgets
        WITH edge_type, neighbor_key, p, center
        ORDER BY p.id, center.id
        WITH edge_type, neighbor_key, COLLECT(p) AS phase_spiders, COLLECT(center) AS centers
        WHERE size(phase_spiders) > 1

        // 7. Calculate the sum of phases for each group
        UNWIND phase_spiders AS ps
        WITH edge_type, neighbor_key, phase_spiders, centers, sum(coalesce(ps.phase, 0.0)) AS total_phase

        // 8. Select one gadget to survive and identify the rest for deletion
        WITH total_phase, phase_spiders[0] AS survivor_p, centers[0] AS survivor_center,
             phase_spiders[1..] AS to_delete_p, centers[1..] AS to_delete_centers

        // 9. Update the surviving phase spider and delete the rest
        SET survivor_p.phase = total_phase
        FOREACH (p_del IN to_delete_p | DETACH DELETE p_del)
        FOREACH (c_del IN to_delete_centers | DETACH DELETE c_del)

        RETURN count(*) AS fusions_performed
        """

    def _spider_fusion_rewrite_2(self):
        return """
        // Match all candidate edges for spider fusion
        MATCH (a:Node)-[r:Wire {t: 1}]->(b:Node)
        WHERE ((a.t = 1 AND b.t = 1) OR (a.t = 2 AND b.t = 2))
          AND a.graph_id = $graph_id AND b.graph_id = $graph_id
        WITH COLLECT(DISTINCT r) AS allEdges

        // Keep only edges where neither endpoint already appears
        WITH reduce( acc = {matchedEdges: [], matchedNodes: []}, e IN allEdges |
            CASE
              WHEN collections.contains(acc.matchedNodes, startNode(e)) OR collections.contains(acc.matchedNodes, endNode(e))
                THEN acc
              ELSE {
                matchedEdges: acc.matchedEdges + e,
                matchedNodes: acc.matchedNodes + [startNode(e), endNode(e)]
              }
            END
        ) AS result
        WITH result.matchedEdges AS matchedEdges

        // Step 2: For each matched edge, create a merged node
        UNWIND matchedEdges AS e
        WITH startNode(e) AS u, endNode(e) AS v

        // Step 3: Create the new merged node with safely added phase
        CREATE (merged:Node {
          phase: coalesce(toFloat(u.phase), 0.0) + coalesce(toFloat(v.phase), 0.0),
          t: u.t,
          graph_id: u.graph_id,
          id: u.id,
          qubit: u.qubit,
          row: u.row
        })
        WITH DISTINCT u, v, merged

        // Step 4: Reconnect neighbors of u and v to merged
        OPTIONAL MATCH (u)-[r:Wire]-(x)
        WHERE x <> v
        CREATE (merged)-[:Wire {t: r.t , graph_id: r.graph_id}]->(x)

        WITH DISTINCT u, v, merged
        // Outgoing edges from u
        OPTIONAL MATCH (v)-[r:Wire]-(y)
        WHERE y <> u
        CREATE (merged)-[:Wire {t: r.t , graph_id: r.graph_id}]->(y)

        // Step 5: Delete old nodes and the edge that connected them
        DETACH DELETE u, v

        RETURN COUNT(*) AS merged;
        """

    def _copy_simp(self):
        return """
        // Copy rule for arity-1 ZX spiders through their neighbor (ZX-only variant).
        MATCH (v:Node)-[vw:Wire]-(w:Node)
        WHERE v.graph_id = $graph_id AND w.graph_id = $graph_id
          AND v.t IN [1, 2] AND w.t IN [1, 2]
          AND v.phase IN [0, 1]
          AND degree(v) = 1
          AND (
            (vw.t = 2 AND w.t = v.t) OR
            (vw.t = 1 AND w.t <> v.t)
          )
        WITH v, w, vw
        ORDER BY v.id, w.id
        LIMIT 1

        WITH v, w, vw,
             CASE
               WHEN vw.t = 2 AND w.t = v.t AND v.t = 1 THEN 2
               WHEN vw.t = 2 AND w.t = v.t AND v.t = 2 THEN 1
               WHEN vw.t = 1 AND w.t <> v.t THEN v.t
               ELSE null
             END AS copy_type
        WHERE copy_type IS NOT NULL

        OPTIONAL MATCH (w)-[we:Wire]-(n:Node)
        WHERE n <> v
        WITH v, w, copy_type, coalesce(v.phase, 0) AS v_phase,
             COLLECT(n) AS neighbor_nodes, COLLECT(we.t) AS neighbor_edge_types

        // Get max ID before creation
        MATCH (all_n:Node {graph_id: $graph_id})
        WITH v, w, copy_type, v_phase, neighbor_nodes, neighbor_edge_types, coalesce(max(all_n.id), -1) AS max_id

        DETACH DELETE v, w

        WITH copy_type, v_phase, neighbor_nodes, neighbor_edge_types, max_id
        UNWIND range(0, size(neighbor_nodes) - 1) AS idx
        WITH copy_type, v_phase, neighbor_nodes[idx] AS n, neighbor_edge_types[idx] AS et, max_id + idx + 1 AS new_id
        
        // Ensure new nodes get a valid integer ID
        CREATE (u:Node {
          id: new_id,
          t: copy_type,
          phase: v_phase,
          graph_id: $graph_id
        })
        CREATE (u)-[:Wire {t: et, graph_id: $graph_id}]->(n)

        RETURN max(1) AS rewrites_applied
        """

    def _supplementarity_simp(self):
        return """
        // Supplementarity rule for non-Clifford Z-spiders with identical neighborhoods.
        MATCH (v:Node {t: 1})
        WHERE v.graph_id = $graph_id
          AND v.phase IS NOT NULL
          AND toFloat(v.phase) <> 0
          AND toFloat(v.phase) * 2 <> round(toFloat(v.phase) * 2)

        MATCH (w:Node {t: 1})
        WHERE w.graph_id = $graph_id
          AND id(v) < id(w)
          AND w.phase IS NOT NULL
          AND toFloat(w.phase) <> 0
          AND toFloat(w.phase) * 2 <> round(toFloat(w.phase) * 2)

        OPTIONAL MATCH (v)-[vw:Wire]-(w)

        OPTIONAL MATCH (v)-[:Wire]-(nv:Node)
        WHERE nv <> w
        WITH v, w, vw, COLLECT(DISTINCT nv) AS v_neighbors

        OPTIONAL MATCH (w)-[:Wire]-(nw:Node)
        WHERE nw <> v
        WITH v, w, vw, v_neighbors, COLLECT(DISTINCT nw) AS w_neighbors

        WHERE size(v_neighbors) = size(w_neighbors)
          AND ALL(n IN v_neighbors WHERE n IN w_neighbors)

        WITH v, w, v_neighbors AS neighbors,
             CASE WHEN vw IS NULL THEN 1 ELSE 2 END AS supp_type,
             coalesce(toFloat(v.phase), 0.0) AS alpha,
             coalesce(toFloat(w.phase), 0.0) AS beta

        WITH v, w, neighbors, supp_type,
             abs((alpha + beta) % 2) AS sum_mod2,
             abs((alpha - beta) % 2) AS diff_mod2

        WHERE (supp_type = 1 AND (sum_mod2 = 1 OR diff_mod2 = 1))
           OR (supp_type = 2 AND (sum_mod2 = 0 OR diff_mod2 = 1))

        WITH v, w, neighbors, supp_type, sum_mod2
        ORDER BY v.id, w.id
        LIMIT 1

        FOREACH (n IN neighbors |
          FOREACH (_ IN CASE
            WHEN (supp_type = 1 AND sum_mod2 = 1) OR (supp_type = 2 AND sum_mod2 = 0)
            THEN [1] ELSE [] END |
            SET n.phase = coalesce(toFloat(n.phase), 0.0) + 1.0
          )
        )

        DETACH DELETE v, w

        RETURN 1 AS rewrites_applied
        """