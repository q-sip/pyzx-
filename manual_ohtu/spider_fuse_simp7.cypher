MATCH (n:Node)-[r:Wire]->(m:Node)
  WHERE n.t = m.t AND r.t = 1
DELETE r
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase


//Create the new node
//CREATE (n2:Node)
//SET n2 = n, n2.phase = totalPhase, n2.kala="maded"
SET n.phase = totalPhase, n.kala="maded"
WITH *

//OPTIONAL MATCH (n:Node)-[r2:Wire]->(other2:Node)
//OPTIONAL MATCH (other3:Node)-[r3:Wire]->(n:Node)
OPTIONAL MATCH (m:Node)-[r4:Wire]->(other4:Node)
OPTIONAL MATCH (other5:Node)-[r5:Wire]->(m:Node)
WITH *


//FOREACH (_ IN CASE WHEN r2 IS NOT NULL THEN [1] ELSE [] END |
//CREATE (n2)-[kala2:Wire]->(other2)
//SET kala2 = r2, kala2.kala = "made2"
//)
//WITH *
//FOREACH (_ IN CASE WHEN r3 IS NOT NULL THEN [1] ELSE [] END |
//CREATE (other3)-[kala3:Wire]->(n2)
//SET kala3 = r3, kala3.kala = "made3"
//)
WITH *
FOREACH (_ IN CASE WHEN r4 IS NOT NULL THEN [1] ELSE [] END |
CREATE (n)-[kala4:Wire]->(other4)
set kala4 = r4, kala4.kala = "made4"
)
WITH *
FOREACH (_ IN CASE WHEN r5 IS NOT NULL THEN [1] ELSE [] END |
CREATE (other5)-[kala5:Wire]->(n)
SET kala5 = r5, kala5.kala = "made5"
)

WITH *
//DELETE r2, r3, r4, r5
//WITH *
DETACH DELETE m;


//WITH *
//return *;


