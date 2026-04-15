MATCH (n:Node)-[r:Wire]->(m:Node)
  WHERE n.t = m.t AND r.t = 1
DELETE r
WITH n, m, (coalesce(n.phase, 0) + coalesce(m.phase, 0)) AS totalPhase
//ON CREATE SET node.phase = totalPhase

CREATE (n2:Node)
SET n2 = n, n2.phase = totalPhase
WITH n, n2, m
MATCH (n:Node)-[r2:Wire]-(other:Node)
//WITH n, id(n) as n_id,n2, id(n2) as n2_id, r2, id(startNode(r2)) as r2_start, id(endNode(r2)) as r2_end, other, m
WITH n, n2, m, r2

//WITH n, id(n) as n_id,n2, id(n2) as n2_id, r2, id(startNode(r2)) as r2_start, id(endNode(r2)) as r2_end, other, m
//SET startNode(r2) = n2

//CREATE (other)-[kala:Wire]->(n2)
//CASE
//WHEN r2_start = n_id
//THEN
//CREATE (n2)-[kala:Wire]->(other)
//SET kala.t = r2.t
//ELSE
//CREATE (other)-[kala2:Wire]->(n2)
//SET kala2.t = r2.t
//END

// 3. Conditional Creation using FOREACH
// If n was the start node
FOREACH (_ IN CASE WHEN r2_start = n THEN [1] ELSE [] END |
CREATE (n2)-[kala:Wire]->(other)
SET kala.t = r2.t, kala.id = r2.id
)
// If n was the end node
FOREACH (_ IN CASE WHEN r2_start <> n THEN [1] ELSE [] END |
CREATE (other)-[kala2:Wire]->(n2)
SET kala2.t = r2.t, kala2.id = r2.id
)
//Hererreererer
WITH n, id(n) as n_id,n2, id(n2) as n2_id, r2, id(startNode(r2)) as r2_start, id(endNode(r2)) as r2_end, other, m
MATCH (m:Node)-[r3:Wire]-(other2:Node)
WITH m, id(m) as m_id,n2, r3, id(startNode(r3)) as r3_start, id(endNode(r3)) as r3_end, other2

// 3. Conditional Creation using FOREACH
// If n was the start node
FOREACH (_ IN CASE WHEN r3_start = m THEN [1] ELSE [] END |
CREATE (n2)-[kala3:Wire]->(other2)
SET kala3.t = r3.t, kala3.id = r3.id
)
// If n was the end node
FOREACH (_ IN CASE WHEN r3_start <> m THEN [1] ELSE [] END |
CREATE (other2)-[kala4:Wire]->(n2)
SET kala4.t = r3.t, kala4.id = r3.id
)


RETURN *;


//CREATE (c1:Country {name: 'Belgium'}), (c2:Country {name: 'Netherlands'})
//CREATE (c1)-[r:BORDERS_WITH]->(c2)
//RETURN r;


//MATCH (a:Person {name: "Ana", age: 22, id:0})
//CALL refactor.clone_nodes([a], False, ["age", "id"])
//YIELD input, output
//RETURN input, output;




//MATCH ()-[r:Wire]->()
//RETURN
//    id(startNode(r)) AS startId,
//    startNode(r).phase AS startPhase,
//    id(endNode(r)) AS endId,
//    endNode(r).phase AS endPhase;
