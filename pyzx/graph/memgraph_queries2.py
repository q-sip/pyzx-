class ZXQueryStore2:
    """
    Stores ZX-Calculus graph rewrite queries for Memgraph/Neo4j.
    """

    def __init__(self):
        # Mapping friendly snake_case names to the raw Cypher queries
        self._queries = {
            "remove_isolated_vertices": self._remove_isolated_vertices(),

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

    def _bialgebra_labeling(self):
        return """MATCH (seed)
        WHERE seed.t = 1
        OPTIONAL MATCH (seed)-[r]-(b)
        WHERE b.t = 2 AND r.t = 1
        WITH seed, collect(DISTINCT b) AS B
        WHERE size(B) > 0
        MATCH (x)
        WHERE x.t = 1
        OPTIONAL MATCH (x)-[r]-(b2)
        WHERE b2 IN B AND r.t = 1
        WITH B, x, count(DISTINCT b2) AS cnt_connected
        WHERE cnt_connected = size(B)
        WITH B, collect(DISTINCT x) AS A
        WHERE size(B) + size(A) > 2
        WITH A, B, A + B AS allNodes
        UNWIND allNodes AS n
        OPTIONAL MATCH (n)-[r1]-(m)
        WHERE r1.t = 1
        WITH A, B, allNodes, n, count(DISTINCT m) AS total_edges
        OPTIONAL MATCH (n)-[r2]-(m2)
        WHERE r2.t = 1 AND m2 IN allNodes
        WITH A, B, allNodes, n, total_edges, count(DISTINCT m2) AS clique_edges
        WITH A, B, allNodes, collect(
            CASE WHEN total_edges - clique_edges = 1 THEN n ELSE NULL END
            ) 
        AS valid_nodes
        WHERE size(valid_nodes) = size(allNodes)
        WITH [n IN (A + B) | id(n)] AS cliqueNodeIds
        WITH DISTINCT cliqueNodeIds AS cliqueNodeIds
        WITH collect(cliqueNodeIds) AS allCliquesIds
        UNWIND allCliquesIds AS cliqueIds
        UNWIND cliqueIds AS nid
        MATCH (n) WHERE id(n) = nid
        OPTIONAL MATCH (n)-[]-(nbr)
        WITH cliqueIds, collect(DISTINCT id(nbr)) AS allNbrs
        WITH cliqueIds, [x IN allNbrs WHERE NOT x IN cliqueIds] AS neighborIds
        WITH collect({nodes: cliqueIds, neighbors: neighborIds}) AS allCliques
        WITH allCliques
        WITH reduce(acc = {cliques: [], nodes: [], neigh: []}, clique IN allCliques |
        CASE
        WHEN            
        NONE (nid IN clique.nodes WHERE nid IN acc.nodes)
        AND
        NONE (nid IN clique.nodes WHERE nid IN acc.neigh)
        THEN
        {
            cliques: acc.cliques + [clique],
            nodes: acc.nodes + clique.nodes,
            neigh: acc.neigh + clique.neighbors
            }
        ELSE acc
        END
        ) 
        AS accFinal
        WITH accFinal.cliques AS disjointCliques
        UNWIND disjointCliques AS chosen
        WITH chosen, randomUUID() AS pid
        UNWIND chosen.nodes AS nid
        MATCH (n) WHERE id(n) = nid
        SET n.pattern_id = pid
        RETURN pid, size(chosen.nodes) AS pattern_size
        ORDER BY pattern_size DESC;
        //WITH collect(A + B) AS allCliques
        //RETURN allCliques
        // Assign pattern_id if all nodes satisfy the constraint
        //CALL {
        //  WITH A, B
        //  WITH A + B AS allNodes, randomUUID() AS pattern_id
        //  UNWIND allNodes AS n
        //  SET n.pattern_id = pattern_id
        //  RETURN pattern_id
        //  LIMIT 1
        //}
        //RETURN A, B, size(A) + size(B) AS area, pattern_id
        //ORDER BY area DESC;"""