BIALGEBRA_SIMPLIFICATION_MUTANT = """
CALL () {
    // Work on exactly one marked pattern
    MATCH (a:Node)
    WHERE a.pattern_id IS NOT NULL
    WITH DISTINCT a.pattern_id AS pid, a.graph_id AS graph_id
    ORDER BY pid
    LIMIT 1

    // Collect the two sides
    MATCH (a1:Node {pattern_id: pid, t: 1, graph_id: graph_id})
    WITH pid, graph_id, collect(a1) AS A
    MATCH (b1:Node {pattern_id: pid, t: 2, graph_id: graph_id})
    WITH pid, graph_id, A, collect(b1) AS B
    WHERE size(A) + size(B) > 2

    // Fresh node ids
    MATCH (n:Node {graph_id: graph_id})
    WITH pid, graph_id, A, B, coalesce(max(n.id), -1) AS max_node_id

    // Fresh wire ids
    OPTIONAL MATCH ()-[w:Wire]-()
    WITH pid, graph_id, A, B, max_node_id, coalesce(max(w.id), -1) AS max_wire_id

    // Collect A external connections
    UNWIND A AS oldA
    OPTIONAL MATCH (oldA)-[r:Wire]-(other:Node {graph_id: graph_id})
    WHERE other.pattern_id IS NULL
    WITH pid, graph_id, A, B, max_node_id, max_wire_id,
        [x IN collect(
            CASE
            WHEN other IS NULL THEN NULL
            ELSE {
                other: other,
                props: properties(r),
                dir: CASE WHEN startNode(r) = oldA THEN 'out' ELSE 'in' END
            }
            END
        ) WHERE x IS NOT NULL] AS a_conns

    // Collect B external connections
    UNWIND B AS oldB
    OPTIONAL MATCH (oldB)-[r:Wire]-(other:Node {graph_id: graph_id})
    WHERE other.pattern_id IS NULL
    WITH pid, graph_id, A, B, max_node_id, max_wire_id, a_conns,
        [x IN collect(
            CASE
            WHEN other IS NULL THEN NULL
            ELSE {
                other: other,
                props: properties(r),
                dir: CASE WHEN startNode(r) = oldB THEN 'out' ELSE 'in' END
            }
            END
        ) WHERE x IS NOT NULL] AS b_conns

    // Create replacement nodes with backend ids
    CREATE (newA:Node {
    t: 2,
    graph_id: graph_id,
    id: max_node_id + 1
    })
    CREATE (newB:Node {
    t: 1,
    graph_id: graph_id,
    id: max_node_id + 2
    })

    WITH pid, graph_id, A, B, newA, newB, a_conns, b_conns, max_wire_id

    // Reconnect A-side external wires
    CALL (newA, a_conns, graph_id, max_wire_id) {
    WITH newA, a_conns, graph_id, max_wire_id
    UNWIND range(0, size(a_conns) - 1) AS i
    WITH newA, a_conns[i] AS conn, graph_id, max_wire_id, i
    WITH newA, conn.other AS other, conn.props AS props, conn.dir AS dir, graph_id, max_wire_id, i

    FOREACH (_ IN CASE WHEN dir = 'out' THEN [1] ELSE [] END |
        CREATE (newA)-[r2:Wire]->(other)
        SET r2 = props
        SET r2.id = max_wire_id + i + 1,
            r2.graph_id = graph_id
    )

    FOREACH (_ IN CASE WHEN dir = 'in' THEN [1] ELSE [] END |
        CREATE (other)-[r2:Wire]->(newA)
        SET r2 = props
        SET r2.id = max_wire_id + i + 1,
            r2.graph_id = graph_id
    )

    RETURN count(*) AS _
    }

    WITH pid, graph_id, A, B, newA, newB, a_conns, b_conns, max_wire_id

    // Reconnect B-side external wires
    CALL (newB, a_conns, b_conns, graph_id, max_wire_id) {
    WITH newB, a_conns, b_conns, graph_id, max_wire_id
    UNWIND range(0, size(b_conns) - 1) AS j
    WITH newB, b_conns[j] AS conn, size(a_conns) AS a_sz, graph_id, max_wire_id, j
    WITH newB, conn.other AS other, conn.props AS props, conn.dir AS dir, a_sz, graph_id, max_wire_id, j

    FOREACH (_ IN CASE WHEN dir = 'out' THEN [1] ELSE [] END |
        CREATE (newB)-[r2:Wire]->(other)
        SET r2 = props
        SET r2.id = max_wire_id + a_sz + j + 1,
            r2.graph_id = graph_id
    )

    FOREACH (_ IN CASE WHEN dir = 'in' THEN [1] ELSE [] END |
        CREATE (other)-[r2:Wire]->(newB)
        SET r2 = props
        SET r2.id = max_wire_id + a_sz + j + 1,
            r2.graph_id = graph_id
    )

    RETURN count(*) AS _
    }

    WITH pid, graph_id, A, B, newA, newB, a_conns, b_conns, max_wire_id

    // DELIBERATE BUG: should be t:1, but we use t:2
    CREATE (newA)-[:Wire {
    t: 2,
    graph_id: graph_id,
    id: max_wire_id + size(a_conns) + size(b_conns) + 1
    }]->(newB)

    // Remove old nodes
    FOREACH (n IN A + B | DETACH DELETE n)

    RETURN pid, newA, newB
}
CALL () {
    MATCH (n:Node)
    WHERE n.pattern_id IS NOT NULL
    REMOVE n.pattern_id
}
RETURN pid, newA, newB;
"""

BIALGEBRA_SIMPLIFICATION = """
CALL () {
  // Pick exactly one marked pattern for this execution.
  MATCH (a:Node)
  WHERE a.pattern_id IS NOT NULL
  WITH DISTINCT a.pattern_id AS pid, a.graph_id AS graph_id
  ORDER BY pid
  LIMIT 1

  // Collect the two bipartite sides for this pattern.
  MATCH (a1:Node {pattern_id: pid, t: 1, graph_id: graph_id})
  WITH pid, graph_id, collect(a1) AS A
  MATCH (b1:Node {pattern_id: pid, t: 2, graph_id: graph_id})
  WITH pid, graph_id, A, collect(b1) AS B
  WHERE size(A) + size(B) > 2

  // Allocate fresh node ids.
  MATCH (n:Node {graph_id: graph_id})
  WITH pid, graph_id, A, B, coalesce(max(n.id), -1) AS max_node_id

  // Allocate a starting wire id.
  OPTIONAL MATCH ()-[w:Wire {graph_id: graph_id}]-()
  WITH pid, graph_id, A, B, max_node_id, coalesce(max(w.id), -1) AS max_wire_id

  // Collect A-side external connections, preserving direction.
  UNWIND A AS oldA
  OPTIONAL MATCH (oldA)-[r:Wire]-(other:Node {graph_id: graph_id})
  WHERE other.pattern_id IS NULL
  WITH pid, graph_id, A, B, max_node_id, max_wire_id,
       [x IN collect(
          CASE
            WHEN other IS NULL THEN NULL
            ELSE {
              other: other,
              props: properties(r),
              dir: CASE WHEN startNode(r) = oldA THEN 'out' ELSE 'in' END
            }
          END
       ) WHERE x IS NOT NULL] AS a_conns

  // Collect B-side external connections, preserving direction.
  UNWIND B AS oldB
  OPTIONAL MATCH (oldB)-[r:Wire]-(other:Node {graph_id: graph_id})
  WHERE other.pattern_id IS NULL
  WITH pid, graph_id, A, B, max_node_id, max_wire_id, a_conns,
       [x IN collect(
          CASE
            WHEN other IS NULL THEN NULL
            ELSE {
              other: other,
              props: properties(r),
              dir: CASE WHEN startNode(r) = oldB THEN 'out' ELSE 'in' END
            }
          END
       ) WHERE x IS NOT NULL] AS b_conns

  // Create new supernodes with fresh ids.
  CREATE (newA:Node {
    t: 2,
    pattern_id: pid,
    graph_id: graph_id,
    id: max_node_id + 1
  })
  CREATE (newB:Node {
    t: 1,
    pattern_id: pid,
    graph_id: graph_id,
    id: max_node_id + 2
  })

  WITH pid, graph_id, A, B, newA, newB, a_conns, b_conns, max_wire_id

  // Reconnect A external edges with original direction.
  CALL {
    WITH newA, a_conns, graph_id, max_wire_id
    UNWIND range(0, size(a_conns) - 1) AS i
    WITH newA, a_conns[i] AS conn, graph_id, max_wire_id, i
    WITH newA,
         conn.other AS other,
         conn.props AS props,
         conn.dir AS dir,
         graph_id,
         max_wire_id,
         i

    FOREACH (_ IN CASE WHEN dir = 'out' THEN [1] ELSE [] END |
      CREATE (newA)-[r2:Wire]->(other)
      SET r2 = props
      SET r2.id = max_wire_id + i + 1,
          r2.graph_id = graph_id
    )

    FOREACH (_ IN CASE WHEN dir = 'in' THEN [1] ELSE [] END |
      CREATE (other)-[r2:Wire]->(newA)
      SET r2 = props
      SET r2.id = max_wire_id + i + 1,
          r2.graph_id = graph_id
    )

    RETURN count(*) AS _
  }

  WITH pid, graph_id, A, B, newA, newB, a_conns, b_conns, max_wire_id

  // Reconnect B external edges with original direction.
  CALL {
    WITH newB, a_conns, b_conns, graph_id, max_wire_id
    UNWIND range(0, size(b_conns) - 1) AS j
    WITH newB, b_conns[j] AS conn, size(a_conns) AS a_sz, graph_id, max_wire_id, j
    WITH newB,
         conn.other AS other,
         conn.props AS props,
         conn.dir AS dir,
         a_sz,
         graph_id,
         max_wire_id,
         j

    FOREACH (_ IN CASE WHEN dir = 'out' THEN [1] ELSE [] END |
      CREATE (newB)-[r2:Wire]->(other)
      SET r2 = props
      SET r2.id = max_wire_id + a_sz + j + 1,
          r2.graph_id = graph_id
    )

    FOREACH (_ IN CASE WHEN dir = 'in' THEN [1] ELSE [] END |
      CREATE (other)-[r2:Wire]->(newB)
      SET r2 = props
      SET r2.id = max_wire_id + a_sz + j + 1,
          r2.graph_id = graph_id
    )

    RETURN count(*) AS _
  }

  WITH pid, graph_id, A, B, newA, newB, a_conns, b_conns, max_wire_id

  // Connect the two new supernodes.
  CREATE (newA)-[:Wire {
    t: 1,
    graph_id: graph_id,
    id: max_wire_id + size(a_conns) + size(b_conns) + 1
  }]->(newB)

  // Delete the old pattern nodes.
  FOREACH (n IN A + B | DETACH DELETE n)

  RETURN pid, newA, newB
}
CALL () {
  MATCH (n:Node)
  WHERE n.pattern_id IS NOT NULL
  REMOVE n.pattern_id
}
RETURN pid, newA, newB;
"""
