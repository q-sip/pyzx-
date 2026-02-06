class CypherRewrites:
    HADAMARD_EDGE_CANCELLATION = """
    // Find all marked patterns
    MATCH (s)
    WHERE s.pattern_id IS NOT NULL

    // Reconstruct the full path for each pattern
    WITH DISTINCT s.pattern_id AS pattern_id
    MATCH path = (start)-[:Wire*2..6]-(end)
    WHERE ALL(edge IN relationships(path) WHERE edge.pattern_id = pattern_id)
    AND start.pattern_id IS NULL AND end.pattern_id IS NULL AND id(start) < id(end)

    WITH start, end, pattern_id,
         [node IN nodes(path)[1..-1] WHERE node.pattern_id = pattern_id] as nodes_to_delete

    // Create direct connection
    WITH DISTINCT start, end, nodes_to_delete, pattern_id
    CREATE (start)-[newWire:Wire {t: 1}]->(end)

    // Delete the nodes with the corresponding Hadamard edges
    WITH nodes_to_delete, pattern_id
    UNWIND nodes_to_delete AS node
    DETACH DELETE node

    // Return something to ensure changes were made
    WITH pattern_id
    RETURN COUNT(DISTINCT pattern_id) as patterns_processed
    """

    SPIDER_FUSION = """
    CALL {
      // Find all marked patterns
      MATCH ()-[s:Wire]-()
      WHERE s.pattern_id IS NOT NULL

      // Reconstruct the full path for each pattern
      WITH DISTINCT s.pattern_id AS pattern_id
      MATCH path = (start)-[:Wire*1..3]-(end)
      WHERE ALL(edge IN relationships(path) WHERE edge.pattern_id = pattern_id)
        AND ALL(n IN nodes(path) WHERE n.pattern_id = pattern_id)
        AND id(start) < id(end)
        AND start.pattern_id = pattern_id
        AND end.pattern_id = pattern_id

      
      WITH start, end, path, pattern_id,
           nodes(path) AS path_nodes,
           relationships(path) AS path_edges
      // Identify endpoints based on having exactly one edge with this pattern_id
      MATCH (start)-[r1:Wire]-()
      WHERE r1.pattern_id = pattern_id
      WITH start, end, path_nodes, path_edges, pattern_id, COUNT(r1) AS start_deg
      MATCH (end)-[r2:Wire]-()
      WHERE r2.pattern_id = pattern_id AND start <> end
      WITH start, end, path_nodes, path_edges, pattern_id, start_deg, COUNT(r2) AS end_deg
      WHERE start_deg = 1 AND end_deg = 1
      // Calculate sum of phases from all nodes in the path
      WITH start, end, path_nodes, path_edges, pattern_id,
           reduce(phase_sum = 0, node IN path_nodes | phase_sum + coalesce(node.phase, 0)) AS total_phase
      //LIMIT 1
      //RETURN total_phase
      // Find all external edges connected to any node in the path (excluding path edges)
      MATCH (external)-[ext_edge:Wire]-(path_node)
      WHERE path_node IN path_nodes
        AND NOT external IN path_nodes
        AND NOT ext_edge IN path_edges

      // Collect all data needed before any modifications
      WITH start, end, path_nodes, path_edges, total_phase, pattern_id,
           COLLECT(DISTINCT {
             external_node: external,
             edge_type: ext_edge.t,
             connected_to: path_node,
             edge_props: properties(ext_edge)
           }) AS external_connections

      // Update start node with summed phase (non-destructive operation)
      SET start.phase = total_phase
      CREATE (fused:Node)
      SET fused = properties(start)
      
      // Create all new external connections BEFORE deleting anything
      WITH start, end, path_nodes, external_connections, total_phase, pattern_id, path_edges, fused
      UNWIND external_connections AS conn
      WITH start, end, conn.external_node AS external, conn.edge_type AS edge_type, 
           conn.edge_props AS edge_props, conn.connected_to AS connected_to,
           total_phase, pattern_id, path_nodes, path_edges, fused
      
      CREATE (fused)-[new_edge:Wire]->(external)
      SET new_edge = edge_props

      // Collect all the data we need for deletion after all creations are done
      WITH start, path_nodes, total_phase, pattern_id, COUNT(DISTINCT external) AS connections_created

      // Delete all path nodes except start
      UNWIND path_nodes AS node_to_delete
      DETACH DELETE node_to_delete

      // Return results
      WITH DISTINCT pattern_id, total_phase, connections_created
      RETURN COUNT(DISTINCT pattern_id) AS patterns_processed, 
             COLLECT(DISTINCT total_phase) AS summed_phases,
             SUM(connections_created) AS total_connections_created
    }
    CALL {
      MATCH (n)
      REMOVE n.pattern_id
    }
    CALL{
      MATCH ()-[r]-()
      REMOVE r.pattern_id
    }
    RETURN patterns_processed;
    """

    PIVOT_TWO_INTERIOR_PAULI = """
    // Find pivot candidates: two t=1 nodes with integer phases connected by t=2 edge
    MATCH (a {t: 1})-[pivot_edge:Wire {t: 2}]-(b {t: 1})
    WHERE id(a) < id(b)  // Process each pair once
      AND a.phase IS NOT NULL 
      AND b.phase IS NOT NULL
      // Check if phases are integer multiples of pi (phase = k for integer k)
      AND a.phase = round(a.phase) 
      AND b.phase = round(b.phase)

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

    // neighbors_a × neighbors_b
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

    // neighbors_a × shared_neighbors
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
    FOREACH (n IN neighbors_a |
      SET n.phase = coalesce(n.phase, 0.0) + a.phase
    ) 

    FOREACH (n IN neighbors_b |
      SET n.phase = coalesce(n.phase, 0.0) + b.phase
    ) 
      
    FOREACH (shared_neighbor IN shared_neighbors | 
      SET shared_neighbor.phase = coalesce(shared_neighbor.phase, 0) + a.phase + b.phase + 1
    )

    // 7. Delete the original pivot nodes
    WITH a, b
    DETACH DELETE a, b

    RETURN COUNT(*) AS pivot_operations_performed;
    """

    PIVOT_SINGLE_INTERIOR_PAULI = """
    // Interior Pauli spider removal rule - Memgraph compatible
    MATCH (a {t: 1})-[:Wire {t : 2}]-(b {t: 1})
    WHERE a.phase = round(a.phase) 
      AND b.phase = round(b.phase)
      //AND id(a) < id(b)
    //RETURN a.id, b.id
    // Check b's connectivity: exactly one boundary (t=0) and one non-boundary
    //WITH a, b

    MATCH (b)-[:Wire]-(b_neighbor)
    WITH a, b, 
         COUNT(CASE WHEN b_neighbor.t = 0 THEN 1 END) as boundary_count,
         COUNT(CASE WHEN b_neighbor.t <> 0 THEN 1 END) as non_boundary_count,
         COLLECT(CASE WHEN b_neighbor.t = 0 THEN b_neighbor END)[0] as boundary_vertex

    WHERE boundary_count = 1 AND non_boundary_count = 1
    //RETURN a.id, b.id, boundary_vertex.id
    // Check that a is connected to at least one t=1 vertex with t=2 edge
    WITH a, b, boundary_vertex
    MATCH (a)-[a_edge:Wire {t: 2}]-(a_neighbor {t: 1})
    WITH a, b, boundary_vertex, COUNT(a_neighbor) as t1_neighbors_via_t2
    WHERE t1_neighbors_via_t2 > 0

    // Check that ALL edges from/to a have t=2
    WITH a, b, boundary_vertex
    MATCH (a)-[all_a_edges:Wire]-()
    WITH a, b, boundary_vertex,
         COUNT(CASE WHEN all_a_edges.t <> 2 THEN 1 END) as non_t2_edges
    WHERE non_t2_edges = 0

    // Take only the first match
    WITH a, b, boundary_vertex
    //LIMIT 1

    // Get the boundary edge type
    WITH a, b, boundary_vertex
    MATCH (b)-[boundary_edge:Wire]-(boundary_vertex)

    // Find all neighbors of a (excluding b) and update their phases
    WITH a, b, boundary_vertex, boundary_edge
    OPTIONAL MATCH (a)-[:Wire]-(a_neighbor)
    WHERE a_neighbor <> b AND a_neighbor.graph_id = a.graph_id

    // Use FOREACH to update phases (handles empty collections automatically)
    WITH a, b, boundary_vertex, boundary_edge, COLLECT(a_neighbor) as a_neighbors
    FOREACH (neighbor IN a_neighbors |
      SET neighbor.phase = (coalesce(neighbor.phase, 0) + b.phase) % 2
    )

    // Connect a to boundary with opposite edge type
    WITH a, b, boundary_vertex, boundary_edge,
         CASE boundary_edge.t WHEN 1 THEN 2 ELSE 1 END as new_edge_type

    CREATE (a)-[new_connection:Wire]->(boundary_vertex)
    SET new_connection.t = new_edge_type,
        new_connection.graph_id = a.graph_id

    // Remove b
    DETACH DELETE b

    RETURN COUNT(*) as interior_pauli_removed
    """

    LOCAL_COMPLEMENT = """
    // Complement each labeled pattern, add center phase to neighbors, then delete center
    MATCH (n) 
    WHERE n.pattern_id IS NOT NULL
    WITH n.pattern_id AS pid, COLLECT(DISTINCT n) AS nodes

    // Count nodes per pattern
    //UNWIND nodes AS tmp
    //WITH pid, nodes, COUNT(tmp) AS total_nodes

    // Find center: node connected to all others in this pattern
    UNWIND nodes AS c
    MATCH (c)-[:Wire]-(cn)
    WHERE cn.pattern_id = pid AND degree(c) = size(nodes) - 1
    WITH pid, nodes, c AS center, collect(DISTINCT c) AS centers

    // Neighbors = pattern nodes except center
    MATCH (center)-[:Wire]-(nbr)
    WHERE nbr.pattern_id = pid
    WITH pid, center, COLLECT(DISTINCT nbr) AS neighbors

    // Enumerate neighbor pairs and toggle: create missing edges first
    UNWIND range(0, size(neighbors)-2) AS i
    UNWIND range(i+1, size(neighbors)-1) AS j
    WITH pid, center, neighbors, neighbors[i] AS n1, neighbors[j] AS n2
    //WHERE id(n1) < id(n2)
    OPTIONAL MATCH (n1)-[e:Wire]-(n2)
    FOREACH (_ IN CASE WHEN e IS NULL THEN [1] ELSE [] END |
      CREATE (n1)-[:Wire {t: 2}]->(n2)
    )
    FOREACH (_ IN CASE WHEN e IS NOT NULL THEN [1] ELSE [] END |
      DELETE e
    )
    // Collect edges that existed to delete later (no UNWIND after this point)
    WITH pid, center, neighbors, COLLECT(e) AS edges_to_delete

    // Add center's phase to all neighbors
    FOREACH (n IN neighbors |
      SET n.phase = coalesce(n.phase, 0) + coalesce(-center.phase, 0)
    )

    // Delete existing edges between neighbors to finish the complement
    //FOREACH (ed IN edges_to_delete |
    //  FOREACH (_ IN CASE WHEN ed IS NOT NULL THEN [1] ELSE [] END |
    //    DELETE ed))

    // Remove the center and clear labels
    DETACH DELETE center
    FOREACH (n IN neighbors | SET n.pattern_id = NULL)

    RETURN COUNT(DISTINCT pid) AS num_processed
    """

    GADGET_FUSION_RED_GREEN = """
    // 1. Find all t=1 nodes and explicitly calculate their degree.
    PROFILE MATCH (p:Node {t: 1})//-[r:Wire]-(neighbor)
    WHERE degree(p) = 1
    WITH p //, count(r) AS degree

    // 2. Filter for nodes that have a degree of exactly 1. These are our phase spiders.
    //WHERE degree = 1

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

    GADGET_FUSION_HADAMARD = """
    // 1. Find all t=1 nodes and explicitly calculate their degree.
    MATCH (p:Node {t: 1})-[r:Wire]-(neighbor)
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

    PIVOT_GADGET = """
    // 1. Find pivot candidates: two t=1 nodes connected by a t=2 edge, where one has an integer phase.
    MATCH (z_j:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(z_alpha:Node {t: 1})
    // Process each pair once, ensure phases exist, and check they are interior spiders.
    WHERE z_j.phase IS NOT NULL AND z_alpha.phase IS NOT NULL
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
    CREATE (z_new_phaseless:Node {t: 1, phase: 1.0, graph_id: z_j.graph_id}),
           (z_new_phased:Node {t: 1, phase: (CASE z_j.phase % 2 WHEN 0 THEN -1 ELSE 1 END) * z_alpha.phase, graph_id: z_j.graph_id})
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

    PIVOT_BOUNDARY = """
    // 1. Find pivot candidates: a t=1 interior spider (z_j) and a t=1 boundary-connected spider (z_alpha).
    MATCH (z_j:Node {t: 1})-[pivot_edge:Wire {t: 2}]-(z_alpha:Node {t: 1})
    MATCH (z_alpha)-[boundary_wire:Wire {t: 1}]-(boundary_node {t: 0})
    WHERE z_j.phase = round(z_j.phase)

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

    BIALGEBRA_RED_GREEN = """
    // Rewriting: For each labeled pattern, perform the bialgebra rewrite
    MATCH (n1:Node {pattern_id})-[w:Wire {pattern_id}]->(n2:Node {pattern_id})
    WHERE n1.t = 1 AND n2.t = 2

    // Gather n1's neighbors (except n2), and the relationship types
    OPTIONAL MATCH (n1)-[edge1]-(nb1)
    WHERE id(nb1) <> id(n2)
    WITH n1, n2, w, collect(nb1) AS n1_neighs, collect(edge1) AS n1_edges

    // Gather n2's neighbors (except n1), and the relationship types
    OPTIONAL MATCH (n2)-[edge2]-(nb2)
    WHERE id(nb2) <> id(n1)
    WITH n1, n2, w, n1_neighs, n1_edges, collect(nb2) AS n2_neighs, collect(edge2) AS n2_edges

    // Prepare to multiply nodes
    WITH n1, n2, w, n1_neighs, n1_edges, n2_neighs, n2_edges,
         range(0, size(n1_neighs)-1) AS n1_idx,
         range(0, size(n2_neighs)-1) AS n2_idx

    // Create new nodes for n1 (t:2)
    UNWIND n1_idx AS i1
    CREATE (new_n1:Node {t:2, uuid: randomUUID(), original: id(n1)})
    WITH n1, n2, w, n1_neighs, n1_edges, n2_neighs, n2_edges, collect(new_n1) AS new_n1s, n2_idx

    // Create new nodes for n2 (t:1)
    UNWIND n2_idx AS i2
    CREATE (new_n2:Node {t:1, uuid: randomUUID(), original: id(n2)})
    WITH n1, n2, w, n1_neighs, n1_edges, n2_neighs, n2_edges, new_n1s, collect(new_n2) AS new_n2s

    // Reconnect previous edges for new_n1 nodes (index-safe)
    UNWIND range(0, size(new_n1s)-1) AS i
    WITH n1_neighs[i] AS nb, n1_edges[i] AS edge, new_n1s[i] AS new_n1, n1, n2, w, n2_neighs, n2_edges, new_n2s
    CREATE (new_n1)-[:Wire {t: edge.t}]->(nb)
    WITH n1, n2, w, n2_neighs, n2_edges, new_n2s, collect(new_n1) AS new_n1s

    // Reconnect previous edges for new_n2 nodes (index-safe)
    UNWIND range(0, size(new_n2s)-1) AS j
    WITH n2_neighs[j] AS nb, n2_edges[j] AS edge, new_n2s[j] AS new_n2, new_n1s, n1, n2
    CREATE (new_n2)-[:Wire {t: edge.t}]->(nb)
    WITH new_n1s, collect(new_n2) AS new_n2s, n1, n2

    // Create all-to-all connections between the new nodes
    UNWIND new_n1s AS n1x
    UNWIND new_n2s AS n2x
    CREATE (n1x)-[:Wire {t:1}]->(n2x)

    // Remove the original nodes and their connecting edge
    WITH n1, n2
    DETACH DELETE n1, n2
    """

    BIALGEBRA_HADAMARD = """
    // Rewriting: For each labeled pattern, perform the bialgebra rewrite
    MATCH (n1:Node {pattern_id})-[w:Wire {pattern_id}]->(n2:Node {pattern_id})
    WHERE n1.t = 1 AND n2.t = 1 AND w.t = 2

    // Gather n1's neighbors (except n2), and the relationship types
    OPTIONAL MATCH (n1)-[edge1]-(nb1)
    WHERE id(nb1) <> id(n2)
    WITH n1, n2, w, collect(nb1) AS n1_neighs, collect(edge1) AS n1_edges

    // Gather n2's neighbors (except n1), and the relationship types
    OPTIONAL MATCH (n2)-[edge2]-(nb2)
    WHERE id(nb2) <> id(n1)
    WITH n1, n2, w, n1_neighs, n1_edges, collect(nb2) AS n2_neighs, collect(edge2) AS n2_edges

    // Prepare to multiply nodes
    WITH n1, n2, w, n1_neighs, n1_edges, n2_neighs, n2_edges,
         range(0, size(n1_neighs)-1) AS n1_idx,
         range(0, size(n2_neighs)-1) AS n2_idx

    // Create new nodes for n1 (t:2)
    UNWIND n1_idx AS i1
    CREATE (new_n1:Node {t:2})
    WITH n1, n2, w, n1_neighs, n1_edges, n2_neighs, n2_edges, collect(new_n1) AS new_n1s, n2_idx

    // Create new nodes for n2 (t:1)
    UNWIND n2_idx AS i2
    CREATE (new_n2:Node {t:1})
    WITH n1, n2, w, n1_neighs, n1_edges, n2_neighs, n2_edges, new_n1s, collect(new_n2) AS new_n2s

    // Reconnect previous edges for new_n1 nodes (index-safe)
    UNWIND range(0, size(new_n1s)-1) AS i
    WITH n1_neighs[i] AS nb, n1_edges[i] AS edge, new_n1s[i] AS new_n1, n1, n2, w, n2_neighs, n2_edges, new_n2s
    CREATE (new_n1)-[:Wire {t: edge.t}]->(nb)
    WITH n1, n2, w, n2_neighs, n2_edges, new_n2s, collect(new_n1) AS new_n1s

    // Reconnect previous edges for new_n2 nodes (index-safe)
    UNWIND range(0, size(new_n2s)-1) AS j
    WITH n2_neighs[j] AS nb, n2_edges[j] AS edge, new_n2s[j] AS new_n2, new_n1s, n1, n2
    CREATE (new_n2)-[:Wire {t: CASE edge.t WHEN 1 THEN 2 ELSE 1}]->(nb)
    WITH new_n1s, collect(new_n2) AS new_n2s, n1, n2

    // Create all-to-all connections between the new nodes
    UNWIND new_n1s AS n1x
    UNWIND new_n2s AS n2x
    CREATE (n1x)-[:Wire {t:1}]->(n2x)

    // Remove the original nodes and their connecting edge
    WITH n1, n2
    DETACH DELETE n1, n2
    """

    BIALGEBRA_SIMPLIFICATION = """
    CALL {
    // For each pattern
    MATCH (a)
    WHERE a.pattern_id IS NOT NULL
    WITH DISTINCT a.pattern_id AS pid, a.graph_id AS graph_id

    // Collect nodes in A and B for this pattern
    MATCH (a1 {pattern_id: pid, t: 1})
    WITH pid, collect(a1) AS A, graph_id
    MATCH (b1 {pattern_id: pid, t: 2})
    WITH pid, A, collect(b1) AS B, graph_id
    WHERE size(A) + size(B) > 2

    // Create new supernodes
    CREATE (newA:Node {t: 2, pattern_id: pid, graph_id: graph_id})
    CREATE (newB:Node {t: 1, pattern_id: pid, graph_id: graph_id})

    // Reconnect edges to the new nodes
    WITH A, B, pid, newA, newB
    UNWIND A AS oldA
    MATCH (oldA)-[r]-(other)
    WHERE other.pattern_id IS NULL
    CREATE (newA)-[r2:Wire]->(other)
    SET r2 += properties(r)
    WITH pid, B, newA, newB, collect(oldA) AS oldANodes

    UNWIND B AS oldB
    MATCH (oldB)-[r]-(other)
    WHERE other.pattern_id IS NULL
    CREATE (newB)-[r2:Wire]->(other)
    SET r2 += properties(r)
    WITH pid, newA, newB, oldANodes, collect(oldB) AS oldBNodes

    // Connect the new supernodes
    CREATE (newA)-[:Wire {t: 1, graph_id: newA.graph_id}]->(newB)

    // Delete the old nodes
    FOREACH (n IN oldANodes + oldBNodes | DETACH DELETE n)
    RETURN pid, newA, newB
    }
    CALL {
      MATCH (n)
      REMOVE n.pattern_id
    }
    RETURN pid, newA, newB;
    """

    LOCAL_COMPLEMENT_FULL = """
    // Find and rewrite local complementation patterns (green spider with ±0.5 phase and all-green Hadamard neighbors)
    MATCH (center:Node)
    WHERE center.t = 1
      AND (center.phase = 0.5 OR center.phase = -0.5)

    // Collect all neighbors
    MATCH (center)-[w:Wire {t:2}]-(nbr:Node {t:1})
    WITH center, COLLECT(DISTINCT nbr) AS neighbors, COLLECT(w) AS neighbor_edges
    WHERE size(neighbors) > 0 
      AND ALL(neigh IN neighbors WHERE neigh.t = 1)
      AND ALL(w in neighbor_edges WHERE w.t = 2)

    // Sort by some deterministic criteria to pick one center per query execution
    //WITH center, neighbors
    //ORDER BY id(center)
    //LIMIT 1

    // Complement: toggle all edges between neighbor pairs
    WITH center, neighbors, range(0, size(neighbors)-2) AS indices_i
    UNWIND indices_i AS i
    WITH center, neighbors, i, range(i+1, size(neighbors)-1) AS indices_j
    UNWIND indices_j AS j
    WITH center, neighbors, neighbors[i] AS n1, neighbors[j] AS n2

    // Toggle edge: create if missing, delete if present
    OPTIONAL MATCH (n1)-[e:Wire {t:2}]-(n2)
    FOREACH (_ IN CASE WHEN e IS NULL THEN [1] ELSE [] END |
      CREATE (n1)-[:Wire {t:2}]->(n2)
    )
    WITH center, neighbors, collect(e) AS edges_found
    FOREACH (e IN [ex IN edges_found WHERE ex IS NOT NULL] | DELETE e)

    // Add center's phase to all neighbors
    WITH center, neighbors
    FOREACH (n IN neighbors |
      SET n.phase = coalesce(n.phase, 0) - coalesce(center.phase, 0)
    )

    // Remove the center
    DETACH DELETE center

    RETURN 1 AS patterns_processed
    """

    GADGET_FUSION_BOTH = """
    // Combined Phase Gadget Fusion: handles both Z-gadgets (t=2 edges) and X-gadgets (t=1 edges)

    // 1. Find all degree-1 phase spiders (t=1, degree=1)
    MATCH (p:Node {t: 1})
    WHERE degree(p) = 1

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

    SPIDER_FUSION_2 = """
    // Match all candidate edges satisfying the condition
    MATCH (a:Node)-[r:Wire]->(b:Node)
    WHERE (a.t = 1 AND b.t = 1) OR (a.t = 2 AND b.t = 2) AND r.t = 1
    WITH collect(DISTINCT r) AS allEdges

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
      graph_id: u.graph_id

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