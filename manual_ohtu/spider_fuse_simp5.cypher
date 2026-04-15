MATCH (n:Node)-[r:Wire]->(m:Node)
  WHERE n.t = m.t AND r.t = 1
DELETE r
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase, n as nCarry, m as mCarry


//Create the new node
CREATE (n2:Node)
SET n2 = n, n2.phase = totalPhase, n2.kala="maded"
WITH *

//Connect the starting relationships
OPTIONAL MATCH (n:Node)-[r2:Wire]->(other2:Node)
WITH *
CREATE (n2)-[kala2:Wire]->(other2)
set kala2 = r2, kala2.kala = "made2"

// If n was the end node
WITH *
OPTIONAL MATCH (other3:Node)-[r3:Wire]->(n:Node)
WITH *
CREATE (other3)-[kala3:Wire]->(n2)
SET kala3 = r3, kala3.kala = "made3"



//Connect the end relationships
WITH *
OPTIONAL MATCH (m:Node)-[r4:Wire]->(other4:Node)
WITH *
CREATE (n2)-[kala4:Wire]->(other4)
set kala4 = r4, kala4.kala = "made4"

// If n was the end node
WITH *
OPTIONAL MATCH (other5:Node)-[r5:Wire]->(m:Node)
WITH *
CREATE (other5)-[kala5:Wire]->(n2)
SET kala5 = r5, kala5.kala = "made5"

//WITH *
DELETE r2, r3, r4, r5, n, m
WITH *
//DETACH DELETE nCarry, mCarry


WITH *
return *;


