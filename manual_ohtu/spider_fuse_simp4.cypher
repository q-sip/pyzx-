MATCH (n:Node)-[r:Wire]->(m:Node)
WHERE n.t = m.t AND r.t = 1
DELETE r
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase


//Create the new node
CREATE (n2:Node)
SET n2 = n, n2.phase = totalPhase
//WITH n, n2, m
WITH *

//Connect the starting relationships
MATCH (n:Node)-[r2:Wire]->(other:Node)
//WITH n, n2, m, r2, other
WITH *
CREATE (n2)-[kala2:Wire]->(other)
set kala2 = r2

// If n was the end node
//WITH n, n2, m, r2, other
WITH *
MATCH (other:Node)-[r3:Wire]->(n:Node)
//WITH n, n2, m, r3, other, r2
WITH *
CREATE (other)-[kala3:Wire]->(n2)
SET kala3 = r3



//Connect the end relationships
//WITH n, n2, m, r2, r3, other
WITH *
MATCH (m:Node)-[r4:Wire]->(other:Node)
//WITH n, n2, m, r2, r3, other, r4
WITH *
CREATE (n2)-[kala4:Wire]->(other)
set kala4 = r4

// If n was the end node
//WITH n, n2, m, r2, r3, other, r4
WITH *
MATCH (other:Node)-[r5:Wire]->(m:Node)
//WITH n, n2, m, r3, other, r2, r4, r5
WITH *
CREATE (other)-[kala5:Wire]->(n2)
SET kala5 = r5


//WITH n, n2, m, r3, other, r2, r4, r5
WITH *

return *;
//MATCH (m:Node)-[r3:Wire]-(other2:Node)
//WITH n, n2, m, r2, other, other2, r3
//
//FOREACH (_ IN CASE WHEN id(startNode(r3)) = m THEN [1] ELSE [] END |
//CREATE (n2)-[kala3:Wire]->(other2)
////SET kala3.t = r3.t, kala3.id = r3.id
//SET kala3 = r3
//)
//FOREACH (_ IN CASE WHEN id(startNode(r3)) <> m THEN [1] ELSE [] END |
//CREATE (other2)-[kala4:Wire]->(n2)
////SET kala4.t = r3.t, kala4.id = r3.id
//SET kala4 = r3
//)
//WITH n, n2, m, r2, other, other2, r3
////DETACH DELETE m
////DELETE r3
////WITH n, n2, m, r2, other, other2
////DELETE m;
//RETURN *;


