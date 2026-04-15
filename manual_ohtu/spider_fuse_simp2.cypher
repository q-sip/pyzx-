MATCH (n:Node)-[r:Wire]->(m:Node)
  WHERE n.t = m.t AND r.t = 1
DELETE r
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase


//Create the new node
CREATE (n2:Node)
SET n2 = n, n2.phase = totalPhase
WITH n, n2, m

//Connect the starting points
MATCH (n:Node)-[r2:Wire]-(other:Node)
WITH n, n2, m, r2, other
FOREACH (_ IN CASE WHEN id(startNode(r2)) = n THEN [1] ELSE [] END |
CREATE (n2)-[kala:Wire]->(other)
SET kala.t = r2.t, kala.id = r2.id
)
// If n was the end node
FOREACH (_ IN CASE WHEN id(startNode(r2)) <> n THEN [1] ELSE [] END |
CREATE (other)-[kala2:Wire]->(n2)
SET kala2.t = r2.t, kala2.id = r2.id
)


//Connect the end relationships
WITH n, n2, m, r2, other
MATCH (m:Node)-[r3:Wire]-(other2:Node)
WITH n, n2, m, r2, other, other2, r3

FOREACH (_ IN CASE WHEN id(startNode(r3)) = m THEN [1] ELSE [] END |
CREATE (n2)-[kala3:Wire]->(other2)
SET kala3.t = r3.t, kala3.id = r3.id
)
FOREACH (_ IN CASE WHEN id(startNode(r3)) <> m THEN [1] ELSE [] END |
CREATE (other2)-[kala4:Wire]->(n2)
SET kala4.t = r3.t, kala4.id = r3.id
)


RETURN *;


