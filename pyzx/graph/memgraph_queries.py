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
        // Find paths of Hadamard nodes (chains of H-gates that can cancel)
        MATCH path = (start:Node)-[:Wire*2..6]-(end:Node)
        WHERE start.graph_id = $graph_id 
          AND end.graph_id = $graph_id
          AND id(start) < id(end)
          // All intermediate nodes must be H-nodes (degree 2 simple gates)
          AND ALL(node IN nodes(path)[1..-1] WHERE node.graph_id = $graph_id AND size([(node)-[]-() | 1]) = 2)
          // All edges in path must be Hadamard edges (t=2)
          AND ALL(edge IN relationships(path) WHERE edge.t = 2)
          // Start and end should not be H-nodes themselves
          AND NOT (size([(start)-[]-() | 1]) = 2 AND ALL(e IN [(start)-[r]-() | r] WHERE e.t = 2))
          AND NOT (size([(end)-[]-() | 1]) = 2 AND ALL(e IN [(end)-[r]-() | r] WHERE e.t = 2))
        
        WITH start, end, nodes(path)[1..-1] as nodes_to_delete
        LIMIT 100  // Process in batches to avoid long transactions
        
        // Create direct connection with simple edge (Hadamards canceled)
        CREATE (start)-[:Wire {t: 1, graph_id: $graph_id}]->(end)
        
        // Delete intermediate Hadamard nodes
        WITH nodes_to_delete
        UNWIND nodes_to_delete AS node
        DETACH DELETE node
        
        RETURN COUNT(DISTINCT nodes_to_delete) as patterns_processed
        """

    def _spider_fusion_rewrite(self):
        return """
        // Find adjacent same-color spiders connected by simple edge
        MATCH (u:Node)-[e:Wire {t: 1}]-(v:Node)
        WHERE ((u.t = 1 AND v.t = 1) OR (u.t = 2 AND v.t = 2))
          AND u.graph_id = $graph_id 
          AND v.graph_id = $graph_id
          AND id(u) < id(v)  // Process each pair once
        
        WITH u, v, e
        LIMIT 100  // Batch size
        
        // Create merged node
        CREATE (merged:Node {
            t: u.t,
            phase: coalesce(u.phase, 0.0) + coalesce(v.phase, 0.0),
            graph_id: $graph_id,
            id: u.id,
            qubit: u.qubit,
            row: u.row
        })
        
        // Collect u neighbors
        WITH u, v, merged
        OPTIONAL MATCH (u)-[r:Wire]-(x:Node)
        WHERE x <> v
        WITH u, v, merged, collect({node_id: id(x), node_t: x.t, edge_t: r.t}) as u_conns
        
        // Collect v neighbors
        WITH u, v, merged, u_conns
        OPTIONAL MATCH (v)-[r:Wire]-(y:Node)
        WHERE y <> u
        WITH u, v, merged, u_conns + collect({node_id: id(y), node_t: y.t, edge_t: r.t}) as all_conns
        
        // Delete original nodes
        DETACH DELETE u, v
        
        // Unwind connections to process them
        WITH merged, all_conns
        UNWIND (CASE WHEN size(all_conns) > 0 THEN all_conns ELSE [null] END) as c
        WITH merged, c
        WHERE c IS NOT NULL
        
        // Re-match t to have a valid node reference for creating edges
        MATCH (t:Node) WHERE id(t) = c.node_id

        // Group by neighbor to handle parallel edges
        WITH merged, t, c.node_t as t_type, collect(c.edge_t) as edge_types
        
        // Logic for merging parallel edges
        // 1 = Simple, 2 = Hadamard
        // ...
        
        WITH merged, t, edge_types,
             CASE 
                WHEN t_type = 0 THEN 0 // Boundary
                WHEN t_type = merged.t THEN 1 // Same color
                ELSE 2 // Diff color
             END as relation_type
             
        WITH merged, t, edge_types, relation_type,
             // Count edges.
             // For Simple edges (1) and Hadamard edges (2).
             size([x IN edge_types WHERE x=1]) as n_simple,
             size([x IN edge_types WHERE x=2]) as n_hadamard
             
        // Determine final edge
        // If Boundary (relation 0): Always keep 1 edge (Simple). Be robust.
        // If Same Color (relation 1): 
        //    Simple edges cancel in pairs (n_simple % 2)
        //    Hadamard edges cancel in pairs (n_hadamard % 2)
        //    Result:
        //      If remaining simple -> Simple edge
        //      If remaining hadamard -> Hadamard edge
        //      If both? -> Hopf/loop logic? Usually don't happen in spider fusion unless already existed.
        //      If both exist, we need to create BOTH? GraphS can't.
        //      Assume standard fusion: pairs cancel.
        // If Diff Color (relation 2):
        //    Simple edges cancel (n_simple % 2)
        //    Hadamard edges merge? No, Hopf rule applies to Simple edges (1).
        //    Actually, standard Parallel Edge rule (fhopf):
        //    - Parallel H-edges (2) between diff colors: Cancel?
        //    - Parallel S-edges (1) between diff colors: Hopf rule.
        
        // Simplified Logic mimicking `GraphS.add_edge_smart`:
        // Just sum modulo 2?
        
        WITH merged, t, relation_type, n_simple, n_hadamard,
             CASE 
                WHEN relation_type = 0 THEN 1 // Boundary: always keep 1 simple edge
                WHEN relation_type = 1 THEN // Same Color
                     CASE 
                        WHEN n_simple > 0 THEN 1 // Keeping 1 simple edge allows subsequent fusion! 
                        // If we have parallel simple edges, they prevent Hopf? No, they CAUSE fusion.
                        // Ideally we fuse immediately. A simple edge between same color = fusion.
                        // If we keep 1, the next pass of spider_simp will fuse 'merged' with 't'.
                        // This preserves connectivity until fusion happens.
                        
                        ELSE 0 
                     END
                ELSE // Diff Color
                     n_simple % 2 // Hopf rule: simple edges cancel in pairs
             END as final_simple,
             
             CASE 
                WHEN relation_type = 0 THEN 0 // Boundary: no Hadamard
                WHEN relation_type = 1 THEN // Same Color
                     n_hadamard % 2 // Hopf rule (Same Color): Parallel H-edges cancel in pairs
                ELSE // Diff Color
                     // Parallel H-edges between Diff Color.
                     // Standard ZX: Keep them parrallel.
                     // GraphS: Cannot support.
                     // If we assume consistent "mod 2" behaviour for simplifications:
                     n_hadamard % 2
             END as final_hadamard
             
        // Handle Mixed Edges (Simple + Hadamard in parallel on Same Color)
        // This corresponds to a standard Hopf reduction where the Hadamard edge adds a pi phase.
        WITH merged, t, relation_type, final_simple, final_hadamard,
             CASE 
                WHEN relation_type = 1 AND final_simple > 0 AND final_hadamard > 0 THEN 1
                ELSE 0
             END as is_mixed
             
        WITH merged, t, final_simple, 
             CASE WHEN is_mixed = 1 THEN 0 ELSE final_hadamard END as real_final_hadamard,
             is_mixed
        
        // Create edges
        FOREACH (_ IN CASE WHEN final_simple > 0 THEN [1] ELSE [] END |
            MERGE (merged)-[:Wire {t: 1}]->(t)
        )
        FOREACH (_ IN CASE WHEN real_final_hadamard > 0 THEN [1] ELSE [] END |
            MERGE (merged)-[:Wire {t: 2}]->(t)
        )
        
        // Aggregate phase shift
        WITH merged, sum(is_mixed) as total_phase_shift
        SET merged.phase = merged.phase + total_phase_shift
        
        RETURN count(DISTINCT merged) as rewrites_applied
        """

    def _id_simp(self):
        # Identity removal: degree-2 spider with zero phase.
        # Fuses the two neighbors.
        # If neighbors are n1, n2 via e1, e2:
        # If e1.t == e2.t (both Simple or both Hadamard), result is Simple edge (type 1).
        # If e1.t != e2.t (one Simple, one Hadamard), result is Hadamard edge (type 2).
        # This matches the logic: H*H = I, S*S = I? No.
        # Simple*Simple = Simple.
        # Simple*Hadamard = Hadamard.
        # Hadamard*Hadamard = Simple.
        # So: type = (e1.t == e2.t) ? 1 : 2. Correct.
        return """
        MATCH (v:Node)
        WHERE v.graph_id = $graph_id
          AND v.t = 1  // ONLY Z-spiders (t=1) are identity spiders (phase 0)
          AND (v.phase IS NULL OR v.phase = 0)
        
        // Check degree using count instead of size() on pattern if problematic
        MATCH (v)-[r:Wire]-()
        WITH v, count(r) as d
        WHERE d = 2

        MATCH (v)-[e1:Wire]-(n1:Node)
        MATCH (v)-[e2:Wire]-(n2:Node)
        WHERE id(e1) < id(e2)
        
        // Ensure no other connections (redundant with degree check but safer against multigraphs)
        WITH v, n1, n2, e1, e2

        // Create new edge
        MERGE (n1)-[new_edge:Wire {t: CASE WHEN e1.t = e2.t THEN 1 ELSE 2 END}]-(n2)
        SET new_edge.graph_id = $graph_id

        // Remove v
        DETACH DELETE v

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
        // Find pivot candidates: two t=1 nodes with integer phases connected by t=2 edge
        MATCH (a:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(b:Node {t: 1})
        WHERE a.graph_id = $graph_id AND b.graph_id = $graph_id
          AND id(a) < id(b)  // Process each pair once
          AND a.phase IS NOT NULL 
          AND b.phase IS NOT NULL
          // Check if phases are integer multiples of pi (phase = k for integer k)
          // Use toFloat to handle potential string storage and avoid crashes on non-numeric types
          AND toFloat(a.phase) IS NOT NULL 
          AND toFloat(b.phase) IS NOT NULL
          AND toFloat(a.phase) = round(toFloat(a.phase)) 
          AND toFloat(b.phase) = round(toFloat(b.phase))

        // START CHANGE: Ensure a and b are strictly interior (no connections to boundaries or non-Z nodes)
        WITH a, b, pivot_edge
        OPTIONAL MATCH (a)-[e_bad_a]-(n_bad_a)
        WHERE n_bad_a <> b AND NOT (n_bad_a.t = 1 AND e_bad_a.t = 2)
        WITH a, b, pivot_edge, count(n_bad_a) as bad_neighbors_a
        WHERE bad_neighbors_a = 0

        OPTIONAL MATCH (b)-[e_bad_b]-(n_bad_b)
        WHERE n_bad_b <> a AND NOT (n_bad_b.t = 1 AND e_bad_b.t = 2)
        WITH a, b, pivot_edge, count(n_bad_b) as bad_neighbors_b
        WHERE bad_neighbors_b = 0
        // END CHANGE

        // Find neighbors of a (excluding b and nodes connected to b)
        WITH a, b, pivot_edge
        OPTIONAL MATCH (a)-[edge_a:Wire {t: 2}]-(neighbor_a {t: 1})
        WHERE neighbor_a <> b
          AND NOT EXISTS((neighbor_a)-[:Wire]-(b))  // Not connected to b
        WITH a, b, pivot_edge, COLLECT(DISTINCT neighbor_a) as neighbors_a

        // Find neighbors of b (excluding a and nodes connected to a)
        OPTIONAL MATCH (b)-[edge_b:Wire {t: 2}]-(neighbor_b {t: 1})
        WHERE neighbor_b <> a
          AND NOT EXISTS((neighbor_b)-[:Wire]-(a))  // Not connected to a
          AND NOT neighbor_b IN neighbors_a  // Extra safety check
        WITH a, b, pivot_edge, neighbors_a, COLLECT(DISTINCT neighbor_b) as neighbors_b

        // Find shared neighbors (connected to both a and b)
        OPTIONAL MATCH (a)-[edge_shared_a:Wire {t: 2}]-(shared {t: 1})-[edge_shared_b:Wire {t: 2}]-(b)
        WITH a, b, pivot_edge, neighbors_a, neighbors_b, COLLECT(DISTINCT shared) as shared_neighbors

        // neighbors_a x neighbors_b
        CALL {
          WITH neighbors_a, neighbors_b
          UNWIND neighbors_a AS node_a
          UNWIND neighbors_b AS node_b
          OPTIONAL MATCH (node_a)-[existing:Wire]-(node_b) 
          FOREACH (_ IN CASE WHEN existing IS NOT NULL THEN [1] ELSE [] END | 
            DELETE existing ) 
          FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END | 
            CREATE (node_a)-[:Wire {t: 2}]->(node_b) )
        }

        // neighbors_a x shared_neighbors
        CALL {
          WITH neighbors_a, shared_neighbors
          UNWIND neighbors_a AS node_a
          UNWIND shared_neighbors AS shared_node
          OPTIONAL MATCH (node_a)-[existing:Wire]-(shared_node) 
          FOREACH (_ IN CASE WHEN existing IS NOT NULL THEN [1] ELSE [] END | 
            DELETE existing ) 
          FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END | 
            CREATE (node_a)-[:Wire {t: 2}]->(shared_node) )
        }

        // neighbors_b x shared_neighbors
        CALL {
          WITH neighbors_b, shared_neighbors
          UNWIND neighbors_b AS node_b
          UNWIND shared_neighbors AS shared_node
          OPTIONAL MATCH (node_b)-[existing:Wire]-(shared_node) 
          FOREACH (_ IN CASE WHEN existing IS NOT NULL THEN [1] ELSE [] END | 
            DELETE existing ) 
          FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END | 
            CREATE (node_b)-[:Wire {t: 2}]->(shared_node) )
        }
            
        // 6. Update phases on the neighbor nodes. 
        // Correct Pivot Logic:
        // neighbors_a (only connected to a) should get b.phase
        // neighbors_b (only connected to b) should get a.phase
        
        FOREACH (n IN neighbors_a |
          SET n.phase = coalesce(n.phase, 0.0) + b.phase
        ) 

        FOREACH (n IN neighbors_b |
          SET n.phase = coalesce(n.phase, 0.0) + a.phase
        ) 
          
        FOREACH (shared_neighbor IN shared_neighbors | 
          SET shared_neighbor.phase = coalesce(shared_neighbor.phase, 0) + a.phase + b.phase + 1
        )

        // 7. Delete the original pivot nodes
        WITH a, b
        DETACH DELETE a, b

        RETURN COUNT(*) AS pivot_operations_performed;
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
          AND (center.phase = 0.5 OR center.phase = -0.5)
        
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
        LIMIT 1  // Process one at a time
        
        // Toggle edges between all neighbor pairs (local complement)
        // ... rest is same
        WITH center, neighbors, range(0, size(neighbors)-2) AS indices_i
        UNWIND indices_i AS i
        WITH center, neighbors, i, range(i+1, size(neighbors)-1) AS indices_j
        UNWIND indices_j AS j
        WITH center, neighbors, neighbors[i] AS n1, neighbors[j] AS n2
        
        // Toggle Hadamard edge: create if missing, delete if present
        
        // Check existence of edge explicitly
        // If multiple edges exist, delete all. If 0, create one.
        
        OPTIONAL MATCH (n1)-[e:Wire]-(n2)
        // No WHERE clause to ensure we catch everything
        
        WITH center, neighbors, n1, n2, collect(e) as found_edges
        
        // Decide action
        WITH center, neighbors, 
             found_edges,
             CASE WHEN size(found_edges) = 0 THEN size(found_edges) ELSE -1 END as debug_val,
             CASE WHEN size(found_edges) = 0 THEN true ELSE false END as do_create
        
        // Deletions: Delete found edges
        FOREACH (edge IN found_edges | DELETE edge)
        
        // Creations: Create one edge if needed
        FOREACH (x IN CASE WHEN do_create THEN [1] ELSE [] END | 
            MERGE (n1)-[:Wire {t: 2, graph_id: $graph_id}]-(n2)
        )
        
        // 5. Update phases (once per center)
        WITH center, neighbors
        FOREACH (n IN neighbors |
          SET n.phase = coalesce(n.phase, 0) - coalesce(center.phase, 0)
        )
        
        // Remove the center
        DETACH DELETE center
        
        RETURN 1 AS num_processed
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
        //ORDER BY id(n)
        WITH p, x, COLLECT(id(n)) AS neighbor_key

        // 6. For each group (identified by neighbor_key), collect the phase spiders and their corresponding X-spiders.
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
        // 1. Find pivot candidates: two t=1 nodes connected by t=2 edge, where one has integer phase
        MATCH (z_j:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(z_alpha:Node {t: 1})
        WHERE z_j.graph_id = $graph_id AND z_alpha.graph_id = $graph_id
          AND z_j.phase IS NOT NULL AND z_alpha.phase IS NOT NULL
          // Check if z_j's phase is an integer multiple of pi.
          AND z_j.phase = round(z_j.phase)
          // NEW: Ensure both are interior spiders (no simple wires of type t=1).
          AND NOT EXISTS((z_j)-[:Wire {t: 1}]-())
          AND NOT EXISTS((z_alpha)-[:Wire {t: 1}]-())

        // 1b. Out of all candidates, keep only the one with the largest z_j.phase
        WITH z_j, z_alpha
        ORDER BY z_j.phase DESC
        //LIMIT 1

        // 2. Collect the three disjoint sets of neighbors.
        // N_j: Neighbors of z_j only.
        WITH z_j, z_alpha
        OPTIONAL MATCH (z_j)-[:Wire {t: 2}]-(n_j:Node {t: 1})
        WHERE NOT EXISTS((n_j)-[:Wire]-(z_alpha)) AND n_j <> z_alpha
        WITH z_j, z_alpha, COLLECT(DISTINCT n_j) AS neighbors_j

        // N_alpha: Neighbors of z_alpha only.
        OPTIONAL MATCH (z_alpha)-[:Wire {t: 2}]-(n_alpha:Node {t: 1})
        WHERE NOT EXISTS((n_alpha)-[:Wire]-(z_j)) AND n_alpha <> z_j
        WITH z_j, z_alpha, neighbors_j, COLLECT(DISTINCT n_alpha) AS neighbors_alpha

        // N_shared: Neighbors of both.
        OPTIONAL MATCH (z_j)-[:Wire {t: 2}]-(n_shared:Node {t: 1})-[:Wire {t: 2}]-(z_alpha)
        WHERE n_shared <> z_j AND n_shared <> z_alpha
        WITH z_j, z_alpha, neighbors_j, neighbors_alpha, COLLECT(DISTINCT n_shared) AS shared_neighbors

        // 3. Create the two new central nodes for the rewritten structure.
        CREATE (z_new_phaseless:Node {t: 1, phase: 1.0, graph_id: z_j.graph_id, id: z_j.id, qubit: z_j.qubit, row: z_j.row}),
               (z_new_phased:Node {t: 1, phase: (CASE z_j.phase % 2 WHEN 0 THEN -1 ELSE 1 END) * z_alpha.phase, graph_id: z_j.graph_id, id: z_alpha.id, qubit: z_alpha.qubit, row: z_alpha.row})
        CREATE (z_new_phaseless)-[:Wire {t: 2}]->(z_new_phased)

        // 4. Connect the new central nodes to all neighbors.
        // Connect z_new_phaseless to N_j and shared
        FOREACH (n IN neighbors_j | CREATE (z_new_phaseless)-[:Wire {t: 2}]->(n))
        FOREACH (n IN shared_neighbors | CREATE (z_new_phaseless)-[:Wire {t: 2}]->(n))

        // 5. Create the 3-partite clique between the neighbor sets.
        FOREACH (n_j IN neighbors_j |
            FOREACH (n_alpha IN neighbors_alpha |
                CREATE (n_j)-[:Wire {t: 2}]->(n_alpha)
            )
        )
        FOREACH (n_j IN neighbors_j |
            FOREACH (n_shared IN shared_neighbors |
                CREATE (n_j)-[:Wire {t: 2}]->(n_shared)
            )
        )
        FOREACH (n_alpha IN neighbors_alpha |
            FOREACH (n_shared IN shared_neighbors |
                CREATE (n_alpha)-[:Wire {t: 2}]->(n_shared)
            )
        )

        // 6. Update phases on the neighbor nodes.
        FOREACH (n IN neighbors_alpha |
            SET n.phase = coalesce(n.phase, 0.0) + z_j.phase
        )
        FOREACH (n IN shared_neighbors |
            SET n.phase = coalesce(n.phase, 0.0) + z_j.phase + 1
        )

        // 7. Finally, remove the original two central spiders.
        WITH z_j, z_alpha
        DETACH DELETE z_j, z_alpha

        RETURN count(*) AS pivot_operations_performed;
        """

    def _pivot_boundary(self):
        return """
        // 1. Find pivot candidates: interior spider (z_j) and boundary-connected spider (z_alpha).
        MATCH (z_j:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(z_alpha:Node {t: 1})
        MATCH (z_alpha)-[boundary_wire:Wire {t: 1}]-(boundary_node:Node {t: 0})
        WHERE z_j.graph_id = $graph_id AND z_alpha.graph_id = $graph_id
          AND z_j.phase = round(z_j.phase)

        // Ensure that z_j is not connected to a simple wire 
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node
        OPTIONAL MATCH (z_j)-[simple_edge:Wire {t: 1}]-()
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node, count(simple_edge) AS num_simple
        WHERE num_simple = 0

        // Ensure that z_j is not connected to a boundary node
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node
        OPTIONAL MATCH (z_j)-[w:Wire]-(n:Node {t: 0})
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node, count(w) AS w_count
        WHERE w_count = 0

        // Ensure that all neighbors of z_j have degree > 1 (not lonely Z-spiders)
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node
        OPTIONAL MATCH (z_j)-[w:Wire]-(n:Node {t: 1})
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node, collect(n) AS neighbors
        WHERE ALL(neigh IN neighbors WHERE degree(neigh) > 1)

        // Ensure z_alpha has ONLY ONE t=1 wire (the one to the boundary).
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node
        OPTIONAL MATCH (z_alpha)-[w:Wire {t:1}]-()
        WITH z_j, z_alpha, pivot_edge, boundary_wire, boundary_node, count(w) AS num_simple_wires
        WHERE num_simple_wires = 1

        // Return only those z_j, z_alpha pairs that satisfy all conditions
        //RETURN z_j, z_alpha, pivot_edge

        WITH z_j, z_alpha, boundary_node, boundary_wire
        ORDER BY z_j.phase DESC
        LIMIT 1

        // 2. Collect the three disjoint sets of neighbors (connected via Hadamard edges).
        WITH z_j, z_alpha, boundary_node, boundary_wire
        OPTIONAL MATCH (z_j)-[:Wire {t: 2}]-(n_j:Node {t: 1})
        WHERE NOT EXISTS((n_j)-[:Wire]-(z_alpha)) AND n_j <> z_alpha
        WITH z_j, z_alpha, boundary_node, boundary_wire, COLLECT(DISTINCT n_j) AS neighbors_j

        OPTIONAL MATCH (z_alpha)-[:Wire {t: 2}]-(n_alpha:Node {t: 1})
        WHERE NOT EXISTS((n_alpha)-[:Wire]-(z_j)) AND n_alpha <> z_j
        WITH z_j, z_alpha, boundary_node, boundary_wire, neighbors_j, COLLECT(DISTINCT n_alpha) AS neighbors_alpha

        OPTIONAL MATCH (z_j)-[:Wire {t: 2}]-(n_shared:Node {t: 1})-[:Wire {t: 2}]-(z_alpha)
        WHERE n_shared <> z_j AND n_shared <> z_alpha
        WITH z_j, z_alpha, boundary_node, boundary_wire, neighbors_j, neighbors_alpha, COLLECT(DISTINCT n_shared) AS shared_neighbors

        // RETURN z_j, z_alpha, boundary_node, boundary_wire, neighbors_j, neighbors_alpha, shared_neighbors
        // 3. Create the THREE new central spiders for the rewritten structure.
        CREATE (z_new_phaseless:Node {t: 1, phase: 1.0, graph_id: z_j.graph_id}),
               (z_new_phased:Node {t: 1, graph_id: z_j.graph_id, phase: (CASE z_j.phase % 2 WHEN 0 THEN -1 ELSE 1 END) * z_alpha.phase}),
               (z_j_replacement:Node {t: 1, phase: z_j.phase, graph_id: z_j.graph_id})
        CREATE (z_new_phaseless)-[:Wire {t: 2}]->(z_new_phased)

        // 4. Perform the boundary rewiring and connect the new spiders.
        // Connect the boundary to the new j*pi spider.
        CREATE (boundary_node)-[:Wire {t: 2}]->(z_j_replacement)

        // 5. Connect the new spiders to the neighbor sets.
        // Connect z_new_phaseless to N_alpha, and N_shared.
        FOREACH (n IN neighbors_j | CREATE (z_new_phaseless)-[:Wire {t: 2}]->(n))
        FOREACH (n IN shared_neighbors | CREATE (z_new_phaseless)-[:Wire {t: 2}]->(n))
        // Connect z_j_replacement to N_alpha, and N_shared.
        FOREACH (n IN neighbors_j | CREATE (z_j_replacement)-[:Wire {t: 2}]->(n))
        FOREACH (n IN shared_neighbors | CREATE (z_j_replacement)-[:Wire {t: 2}]->(n))

        // 6. Create the 3-partite clique between the neighbor sets.
        FOREACH (n_j IN neighbors_j |
            FOREACH (n_alpha IN neighbors_alpha |
                CREATE (n_j)-[:Wire {t: 2}]->(n_alpha)
            )
        )
        FOREACH (n_j IN neighbors_j |
            FOREACH (n_shared IN shared_neighbors |
                CREATE (n_j)-[:Wire {t: 2}]->(n_shared)
            )
        )
        FOREACH (n_alpha IN neighbors_alpha |
            FOREACH (n_shared IN shared_neighbors |
                CREATE (n_alpha)-[:Wire {t: 2}]->(n_shared)
            )
        )

        // 6. Update phases on the neighbor nodes.
        FOREACH (n IN neighbors_alpha |
            SET n.phase = coalesce(n.phase, 0.0) + z_j.phase
        )
        FOREACH (n IN shared_neighbors |
            SET n.phase = coalesce(n.phase, 0.0) + z_j.phase + 1
        )

        // 8. Finally, remove the original two central spiders.
        WITH z_j, z_alpha, boundary_wire
        DELETE boundary_wire
        DETACH DELETE z_j, z_alpha

        RETURN count(*) AS pivot_operations_performed;
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
        // Find local complementation pattern: Z-spider with ±π/2 phase, all neighbors via Hadamard
        MATCH (center:Node)
        WHERE center.graph_id = $graph_id
          AND center.t = 1
          AND (center.phase = 0.5 OR center.phase = -0.5 OR center.phase = 1.5)

        // Find neighbors and ensure all are Z-spiders connected via Hadamard edges
        MATCH (center)-[w:Wire {t:2}]-(nbr:Node {t:1})
        WITH center, collect(distinct nbr) as neighbors
        
        // Only proceed if ALL incident edges were Hadamard and neighbors are Z-spiders
        // (The match above enforces w:Wire{t:2} and nbr:Node{t:1}. We need to ensure
        // center has NO OTHER connections)
        WHERE size(neighbors) > 0 AND degree(center) = size(neighbors)
        
        // Limit to 1 match for safety/determinism per iteration
        WITH center, neighbors LIMIT 1
        
        // 1. Update neighbors' phases
        WITH center, neighbors
        FOREACH (n IN neighbors | 
            SET n.phase = n.phase - center.phase
        )
        
        // 2. Delete the center node immediately to ensure execution
        DETACH DELETE center
        
        // 3. Toggle edges between all pairs of neighbors
        WITH neighbors, center
        UNWIND range(0, size(neighbors)-2) as i
        UNWIND range(i+1, size(neighbors)-1) as j
        WITH neighbors, center, neighbors[i] as n1, neighbors[j] as n2
        
        // Force delete using explicit match?
        OPTIONAL MATCH (n1)-[e:Wire]-(n2)
        
        // If e matched, delete it.
        // Use separate clause to be sure.
        FOREACH (dummy IN CASE WHEN e IS NOT NULL THEN [1] ELSE [] END | DELETE e)
        
        // Create if didn't exist
        FOREACH (dummy IN CASE WHEN e IS NULL THEN [1] ELSE [] END |
             MERGE (n1)-[:Wire {t: 2, graph_id: $graph_id}]-(n2)
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
        //ORDER BY id(n)
        WITH p, center, edge_type, COLLECT(id(n)) AS neighbor_key

        // 6. Group by (edge_type, neighbor_key) to separate Z-gadgets from X-gadgets
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

        // Step 3: Create the new merged node with summed phase
        CREATE (merged:Node {
          phase: coalesce(u.phase, 0) + coalesce(v.phase, 0),
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

        DETACH DELETE v, w

        WITH 1 AS applied, copy_type, v_phase, neighbor_nodes, neighbor_edge_types
        UNWIND range(0, size(neighbor_nodes) - 1) AS idx
        WITH applied, copy_type, v_phase, neighbor_nodes[idx] AS n, neighbor_edge_types[idx] AS et
        CREATE (u:Node {
          t: copy_type,
          phase: v_phase,
          graph_id: $graph_id
        })
        CREATE (u)-[:Wire {t: et, graph_id: $graph_id}]->(n)

        RETURN max(applied) AS rewrites_applied
        """

    def _supplementarity_simp(self):
        return """
        // Supplementarity rule for non-Clifford Z-spiders with identical neighborhoods.
        MATCH (v:Node {t: 1})
        WHERE v.graph_id = $graph_id
          AND v.phase IS NOT NULL
          AND v.phase <> 0
          AND v.phase * 2 <> round(v.phase * 2)

        MATCH (w:Node {t: 1})
        WHERE w.graph_id = $graph_id
          AND id(v) < id(w)
          AND w.phase IS NOT NULL
          AND w.phase <> 0
          AND w.phase * 2 <> round(w.phase * 2)

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
             coalesce(v.phase, 0) AS alpha,
             coalesce(w.phase, 0) AS beta

        WITH v, w, neighbors, supp_type,
             abs((alpha + beta) % 2) AS sum_mod2,
             abs((alpha - beta) % 2) AS diff_mod2

        WHERE (supp_type = 1 AND (sum_mod2 = 1 OR diff_mod2 = 1))
           OR (supp_type = 2 AND (sum_mod2 = 0 OR diff_mod2 = 1))

        WITH v, w, neighbors, supp_type, sum_mod2
        LIMIT 1

        FOREACH (n IN neighbors |
          FOREACH (_ IN CASE
            WHEN (supp_type = 1 AND sum_mod2 = 1) OR (supp_type = 2 AND sum_mod2 = 0)
            THEN [1] ELSE [] END |
            SET n.phase = coalesce(n.phase, 0) + 1
          )
        )

        DETACH DELETE v, w

        RETURN 1 AS rewrites_applied
        """