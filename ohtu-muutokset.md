# GraphNeo4j

GraphNeo4j is a class that implements graph database functionality to pyzx, using Neo4j as the backend.

It is initialized like this:

## Initialization
```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from dotenv import load_dotenv
import os, uuid

load_dotenv(".env.pyzx")
gid = f"example_{uuid.uuid4().hex}"

g = GraphNeo4j(
    uri=os.getenv("NEO4J_URI", ""),
    user=os.getenv("NEO4J_USER", ""),
    password=os.getenv("NEO4J_PASSWORD", ""),
    graph_id=gid,
    database=os.getenv("NEO4J_DATABASE"),
)
```
### Parameters
- URI: ``bolt://neo4j:<port>`` from .env.pyzx
- USER: <username> from .env.pyzx
- PASSWORD: <neo4j password> from .env.pyzx
- graph_id: unique id for the graph
- DATABASE: 

It has many methods, outlined below in this document.


## GraphNeo4j.depth() -> int

### Returns
- the maximum depth of a GraphNeo4j object from the database.
- -1, if it is unsure about depth (NULL nodes or no rows) or it fails.

### Parameters
- No parameters

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.add_vertices(amount: int) -> List[VT]

Adds `amount` number new vertices to the graph in Neo4j and returns a list of containing the created vertex IDs.

Vertices are created as `(:Node {graph_id, id, t, phase, qubit, row})` with the following defaults:

- t: `VertexType.BOUNDARY`
- phase: `"0"`
- qubit: `-1`
- row: `-1`

Vertex ids are allocated consecutively starting from the current internal vertex index (`self._vindex`). After insertion, `self._vindex` is incremented by `amount`.

### Parameters

- amount: `int`  
  Number of vertices to create. Must be `>= 0`.  
  - If `amount == 0`, the method returns an empty list and performs no database writes.  
  - If `amount < 0`, the method raises `ValueError`.

### Returns

- `List[VT]`  
  A list of the new vertex ids, e.g. `[0, 1, 2]`.

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from dotenv import load_dotenv
import os, uuid

load_dotenv(".env.pyzx")
gid = f"example_{uuid.uuid4().hex}"

g = GraphNeo4j(
    uri=os.getenv("NEO4J_URI", ""),
    user=os.getenv("NEO4J_USER", ""),
    password=os.getenv("NEO4J_PASSWORD", ""),
    graph_id=gid,
    database=os.getenv("NEO4J_DATABASE"),
)

vs = g.add_vertices(3)
print(vs)  # e.g. [0, 1, 2]

g.close()
```
See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.set_qubit(self, vertex: VT, q: FloatInt) -> None:

Sets the `qubit` value associated to the vertex.

Vertices are created as `(:Node {graph_id, id, t, phase, qubit, row})` with the following defaults:

- t: `VertexType.BOUNDARY`
- phase: `"0"`
- qubit: `-1`
- row: `-1`

Vertex ids are allocated consecutively starting from the current internal vertex index (`self._vindex`). After insertio>

### Parameters

- vertex: id of the vertex `int`
- q: qubit `float`

### Returns

  Sets qubit value in the database for an index. Does not return anything.

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from dotenv import load_dotenv
import os, uuid

load_dotenv(".env.pyzx")
gid = f"example_{uuid.uuid4().hex}"

g = GraphNeo4j(
    uri=os.getenv("NEO4J_URI", ""),
    user=os.getenv("NEO4J_USER", ""),
    password=os.getenv("NEO4J_PASSWORD", ""),
    graph_id=gid,
    database=os.getenv("NEO4J_DATABASE"),
)

g.set_qubit(3, 1)

g.close()
```
See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.set_qubit(self, vertex: VT) -> None:

Returns the `qubit` value associated to the vertex. If no index has been set, returns -1.

Vertices are created as `(:Node {graph_id, id, t, phase, qubit, row})` with the following defaults:

- t: `VertexType.BOUNDARY`
- phase: `"0"`
- qubit: `-1`
- row: `-1`

Vertex ids are allocated consecutively starting from the current internal vertex index (`self._vindex`). After insertio>

### Parameters

- vertex: id of the vertex `int`

### Returns

  Returns qubit value in the database for an index. Does not return anything.

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from dotenv import load_dotenv
import os, uuid

load_dotenv(".env.pyzx")
gid = f"example_{uuid.uuid4().hex}"

g = GraphNeo4j(
    uri=os.getenv("NEO4J_URI", ""),
    user=os.getenv("NEO4J_USER", ""),
    password=os.getenv("NEO4J_PASSWORD", ""),
    graph_id=gid,
    database=os.getenv("NEO4J_DATABASE"),
)

qubit_value = g.qubit(3)
print(qubit_value)
g.close()
```
See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)


## GraphNeo4j.remove_isolated_vertices() -> None

Deletes isolated vertices and isolated vertex pairs from the graph, updating the graph scalar according to ZX-calculus rules.

This method mirrors the semantics of `BaseGraph.remove_isolated_vertices` in pyzx and operates as a **graph simplification step**. It identifies vertices (or pairs of vertices) that do not meaningfully connect to the rest of the diagram and removes them, while correctly accumulating their contribution into the graph’s scalar.

### Behaviour

The method iterates over all vertices in the graph and applies the following rules:

#### 1. Completely isolated vertices (degree = 0)

* **Boundary vertex**
  → Raises `TypeError`
  (A ZX-diagram with an isolated boundary vertex is ill-typed.)
* **H-box vertex**
  → The vertex is removed and its phase is added to the scalar via `scalar.add_phase`.
* **Z or X vertex**
  → The vertex is removed and its phase is added to the scalar via `scalar.add_node`.

#### 2. Isolated vertex pairs (degree = 1 on both vertices)

A pair of vertices `v` and `w` is removed if:

* `v` and `w` are only connected to each other,
* neither vertex is a boundary vertex.

The contribution to the scalar depends on:

* the vertex types (Z / X / H-box),
* the edge type (`EdgeType.SIMPLE` or `EdgeType.HADAMARD`).

H-boxes of degree 1 are treated as Z-spiders, in accordance with pyzx semantics.

#### 3. Vertices that are part of larger connected components

Vertices that:

* have degree ≥ 2, or
* are connected to boundary vertices, or
* are part of nontrivial subgraphs

are **not removed**.

After analysis, all removable vertices are deleted from the Neo4j database in a single operation.

### Parameters

* None

### Returns

* `None`
  The method mutates the graph in-place.

### Raises

* `TypeError`
  If the graph contains an isolated boundary vertex.

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from fractions import Fraction

# Graph with two Z-spiders only connected to each other
nodes = [
    {"ty": VertexType.Z, "phase": Fraction(1, 4)},
    {"ty": VertexType.Z, "phase": Fraction(1, 4)},
]
edges = [((0, 1), EdgeType.SIMPLE)]

g.create_graph(nodes, edges)

g.remove_isolated_vertices()

# Both vertices are removed; their phases are absorbed into the scalar
```

### Notes

* This method is typically used during normalization or simplification passes.
* It performs multiple read queries to Neo4j and should be considered a **logical transformation**, not a cheap structural edit.
* The scalar updates happen purely on the Python side (`self.scalar`) and are not stored in the database.

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)




## Seuraava metodi / luokka

```
koodiesimerkki
```


### Parametrit

- eka: ``highlight`` 
- toka: ``highlight`` 
- kolmas: ``highlight`` 
- neljäs:
- viides: 


See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)
(en löytäny miten sais permalinkin joka päivittyis esim. rivinumeroiden muuttuessa, joten tää on se millä mennään toistaseks)
