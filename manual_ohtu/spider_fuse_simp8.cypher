MATCH (n:Node)-[r:Wire]->(m:Node)
  WHERE n.t = m.t AND r.t = 1
DELETE r

//Set the new phase
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase
SET n.phase = totalPhase
WITH *

//Find the original connections
OPTIONAL MATCH (m:Node)-[r4:Wire]->(other4:Node)
OPTIONAL MATCH (other5:Node)-[r5:Wire]->(m:Node)
WITH *

//Join the from our node to other relationships
FOREACH (_ IN CASE WHEN r4 IS NOT NULL THEN [1] ELSE [] END |
CREATE (n)-[kala4:Wire]->(other4)
set kala4 = r4
)
WITH *

//Join the from other to our node relationships
FOREACH (_ IN CASE WHEN r5 IS NOT NULL THEN [1] ELSE [] END |
CREATE (other5)-[kala5:Wire]->(n)
SET kala5 = r5
)

//Delete the second node
WITH *
DETACH DELETE m;


