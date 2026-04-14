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

**Parameters**

- `uri`: `str`  
  Neo4j connection URI (e.g., `bolt://neo4j:<port>`) from `.env.pyzx`.
- `user`: `str`  
  Neo4j username from `.env.pyzx`.
- `password`: `str`  
  Neo4j password from `.env.pyzx`.
- `graph_id`: `str`  
  Unique identifier for this graph instance.
- `database`: `str`  
  Neo4j database name from `.env.pyzx`.

## Methods

### depth

**Full method signature:**

```
g.depth() -> int
```

Returns the maximum depth of the graph from the database.

**Behaviour**

- Queries the Neo4j database for the maximum row value across all vertices in the graph.
- Returns the maximum depth found, or `-1` if unsure (NULL nodes, no rows, or query failure).

**Parameters**

- None

**Returns**

- `int`  
  The maximum depth of the graph, or `-1` on failure.

**Example**

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

depth = g.depth()
print(depth)  # e.g. 5

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### add_vertices

**Full method signature:**

```
g.add_vertices(amount: int) -> List[VT]
```

Adds `amount` new vertices to the graph and returns a list of the created vertex IDs.

**Behaviour**

- Creates `amount` vertices in Neo4j as `(:Node {graph_id, id, t, phase, qubit, row})`.
- Vertex ids are allocated consecutively starting from the current internal vertex index (`self._vindex`).
- After insertion, `self._vindex` is incremented by `amount`.
- All created vertices use default values:
  - `t`: `VertexType.BOUNDARY`
  - `phase`: `"0"`
  - `qubit`: `-1`
  - `row`: `-1`

**Parameters**

- `amount`: `int`  
  Number of vertices to create. Must be `>= 0`.
  - If `amount == 0`, returns empty list and performs no database writes.
  - If `amount < 0`, raises `ValueError`.

**Returns**

- `List[VT]`  
  A list of the new vertex ids, e.g., `[0, 1, 2]`.

**Example**

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

---

### set_qubit

**Full method signature:**

```
g.set_qubit(vertex: VT, q: FloatInt) -> None
```

Sets the `qubit` value associated with a vertex.

**Behaviour**

- Updates the `qubit` property of the vertex in Neo4j.
- The qubit value represents the layout wire index for this vertex.

**Parameters**

- `vertex`: `VT`  
  The id of the vertex to modify.
- `q`: `FloatInt`  
  The qubit value to set.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

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

v = g.add_vertices(1)[0]
g.set_qubit(v, 1)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### qubit

**Full method signature:**

```
g.qubit(vertex: VT) -> FloatInt
```

Returns the `qubit` value associated with a vertex.

**Behaviour**

- Queries the Neo4j database for the qubit property of the specified vertex.
- If no qubit has been set, returns `-1`.

**Parameters**

- `vertex`: `VT`  
  The id of the vertex.

**Returns**

- `FloatInt`  
  The qubit value for this vertex, or `-1` if not set.

**Example**

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

v = g.add_vertices(1)[0]
g.set_qubit(v, 2)
qubit_value = g.qubit(v)
print(qubit_value)  # 2

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### remove_isolated_vertices

**Full method signature:**

```
g.remove_isolated_vertices() -> None
```

Deletes isolated vertices and isolated vertex pairs from the graph, updating the graph scalar according to ZX-calculus rules.

**Behaviour**

This method mirrors the semantics of `BaseGraph.remove_isolated_vertices` and operates as a **graph simplification step**. It identifies vertices (or pairs of vertices) that do not meaningfully connect to the rest of the diagram and removes them, while correctly accumulating their contribution into the graph's scalar.

The method iterates over all vertices and applies the following rules:

**1. Completely isolated vertices (degree = 0)**

- **Boundary vertex**  
  → Raises `TypeError` (A ZX-diagram with an isolated boundary vertex is ill-typed).
- **H-box vertex**  
  → The vertex is removed and its phase is added to the scalar via `scalar.add_phase`.
- **Z or X vertex**  
  → The vertex is removed and its phase is added to the scalar via `scalar.add_node`.

**2. Isolated vertex pairs (degree = 1 on both vertices)**

A pair of vertices `v` and `w` is removed if:
- `v` and `w` are only connected to each other.
- Neither vertex is a boundary vertex.

The contribution to the scalar depends on:
- The vertex types (Z / X / H-box).
- The edge type (`EdgeType.SIMPLE` or `EdgeType.HADAMARD`).

H-boxes of degree 1 are treated as Z-spiders, in accordance with pyzx semantics.

**3. Vertices that are part of larger connected components**

Vertices that have degree ≥ 2, are connected to boundary vertices, or are part of nontrivial subgraphs are **not removed**.

After analysis, all removable vertices are deleted from the Neo4j database in a single operation.

**Parameters**

- None

**Returns**

- `None`  
  Mutates the graph in-place.

**Raises**

- `TypeError`  
  If the graph contains an isolated boundary vertex.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from fractions import Fraction

g = GraphNeo4j(
    uri=os.getenv("NEO4J_URI", ""),
    user=os.getenv("NEO4J_USER", ""),
    password=os.getenv("NEO4J_PASSWORD", ""),
    graph_id=gid,
    database=os.getenv("NEO4J_DATABASE"),
)

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

**Notes**

- This method is typically used during normalization or simplification passes.
- It performs multiple read queries to Neo4j and should be considered a **logical transformation**, not a cheap structural edit.
- The scalar updates happen purely on the Python side (`self.scalar`) and are not stored in the database.

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### add_vertex_indexed

**Full method signature:**

```
g.add_vertex_indexed(v: VT) -> None
```

Adds a vertex with a guaranteed explicit vertex id.

**Behaviour**

- Checks whether a node already exists with `(:Node {graph_id: self.graph_id, id: v})`.
  - If it exists, raises `ValueError`.
- Otherwise creates the node with defaults:
  - `t`: `VertexType.BOUNDARY`
  - `phase`: `"0"`
  - `qubit`: `-1`
  - `row`: `-1`
- Updates the internal vertex allocator:
  - If `v >= self._vindex`, sets `self._vindex = v + 1`.
  - If `v < self._vindex`, `self._vindex` is unchanged.

**Parameters**

- `v`: `VT`  
  The explicit vertex id to allocate. Must be unused within the current `graph_id`.

**Returns**

- `None`  
  Mutates the graph in-place.

**Raises**

- `ValueError`  
  If the index `v` is already in use for this graph (`graph_id`).

**Example**

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

g.add_vertex_indexed(5)  # creates Node with id=5
# g.add_vertex_indexed(5)  # would raise ValueError

g.close()
```

**Notes**

- Created vertex uses backend defaults; customize with `set_type`, `set_phase`, `set_qubit`, `set_row` after creation.
- This method only creates the vertex and reserves the id; it does not set inputs/outputs or edges.
- Useful when ids must stay stable across graph reconstruction.

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### set_outputs

**Full method signature:**

```
g.set_outputs(outputs: Tuple[VT, ...]) -> None
```

Sets the outputs of the graph.

**Behaviour**

- Updates the in-memory output tuple: `self._outputs = tuple(outputs)`.
- Synchronizes Neo4j labels for the current `graph_id`:
  1. Clears all existing output markers by removing label `:Output` from any node currently labeled `:Output`.
  2. Marks the new output nodes by setting label `:Output` on each vertex id in `outputs`.
- Passing an empty tuple clears all output labels for the graph.

**Parameters**

- `outputs`: `Tuple[VT, ...]`  
  Tuple of vertex ids that should be treated as the outputs of this ZX-diagram.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

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

g.add_vertices(4)          # ids: 0, 1, 2, 3
g.set_outputs((1, 3))      # marks nodes 1 and 3 as outputs
g.set_outputs(tuple())     # clears outputs

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### outputs

**Full method signature:**

```
g.outputs() -> Tuple[VT, ...]
```

Gets the outputs of the graph.

**Behaviour**

- If `self._outputs` is already set and non-empty, returns it without querying Neo4j.
- Otherwise reads output vertices from Neo4j using the `:Output` label for the current `graph_id`:
  - Matches `(:Output {graph_id})`
  - Returns their `id` values ordered by `id`
- Caches the result by setting `self._outputs` to the returned tuple.
- If there are no output labels (and `self._outputs` is empty), returns an empty tuple.

**Parameters**

- None

**Returns**

- `Tuple[VT, ...]`  
  The output vertex ids, e.g., `(1, 4)`.

**Example**

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

g.add_vertices(5)
g.set_outputs((4, 1))

print(g.outputs())  # (1, 4)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### set_inputs

**Full method signature:**

```
g.set_inputs(inputs: Tuple[VT, ...]) -> None
```

Sets the inputs of the graph.

**Behaviour**

- Updates the in-memory input tuple: `self._inputs = tuple(inputs)`.
- Synchronizes Neo4j labels for the current `graph_id`:
  1. Clears all existing input markers by removing label `:Input` from any node currently labeled `:Input`.
  2. Marks the new input nodes by setting label `:Input` on each vertex id in `inputs`.
- Passing an empty tuple clears all input labels for the graph.

**Parameters**

- `inputs`: `Tuple[VT, ...]`  
  Tuple of vertex ids that should be treated as the inputs of this ZX-diagram.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

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

g.add_vertices(4)          # ids: 0, 1, 2, 3
g.set_inputs((0, 2))       # marks nodes 0 and 2 as inputs
g.set_inputs(tuple())      # clears inputs

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### inputs

**Full method signature:**

```
g.inputs() -> Tuple[VT, ...]
```

Gets the inputs of the graph.

**Behaviour**

- If `self._inputs` is already set and non-empty, returns it without querying Neo4j.
- Otherwise reads input vertices from Neo4j using the `:Input` label for the current `graph_id`:
  - Matches `(:Input {graph_id})`
  - Returns their `id` values ordered by `id`
- Caches the result by setting `self._inputs` to the returned tuple.
- If there are no input labels (and `self._inputs` is empty), returns an empty tuple.

**Parameters**

- None

**Returns**

- `Tuple[VT, ...]`  
  The input vertex ids, e.g., `(0, 2)`.

**Example**

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

g.add_vertices(5)
g.set_inputs((2, 0))

print(g.inputs())  # (0, 2)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### clone

**Full method signature:**

```
g.clone() -> GraphNeo4j
```

Creates a complete independent copy of the graph.

**Behaviour**

- Creates a new GraphNeo4j instance with a new unique `graph_id`.
- Copies all vertices from the current graph to the new graph, preserving:
  - Vertex ids (uses `add_vertex_indexed`)
  - Vertex types (`t`)
  - Phase values
  - Qubit and row assignments
- Copies all edges from the current graph to the new graph, preserving edge types.
- Copies the input and output specifications to the new graph.
- Returns the new independent graph instance.

**Parameters**

- None

**Returns**

- `GraphNeo4j`  
  A new GraphNeo4j instance containing all data from the original graph.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType
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

g.add_vertices(3)

g_copy = g.clone()

print(g.graph_id, g_copy.graph_id)  # Different ids
print(list(g.vertices()), list(g_copy.vertices()))  # Same vertex ids

g.close()
g_copy.close()
```

**Notes**

- The cloned graph has a new unique `graph_id` and is stored separately in the database.
- All vertex and edge data is duplicated; modifications to the clone do not affect the original.

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### row

**Full method signature:**

```
g.row(vertex: VT) -> FloatInt
```

Returns the `row` value associated with a vertex.

**Behaviour**

- Queries the Neo4j database for the row property of the specified vertex.
- If no row has been set, returns `-1`.

**Parameters**

- `vertex`: `VT`  
  The id of the vertex.

**Returns**

- `FloatInt`  
  The row value for this vertex, or `-1` if not set.

**Example**

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

v = g.add_vertices(1)[0]
g.set_row(v, 5)
row_value = g.row(v)
print(row_value)  # 5

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### set_row

**Full method signature:**

```
g.set_row(vertex: VT, r: FloatInt) -> None
```

Sets the `row` value associated with a vertex.

**Behaviour**

- Updates the `row` property of the vertex in Neo4j.
- The row value represents the layout/order position for this vertex.

**Parameters**

- `vertex`: `VT`  
  The id of the vertex to modify.
- `r`: `FloatInt`  
  The row value to set.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

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

v = g.add_vertices(1)[0]
g.set_row(v, 5)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### create_graph

**Full method signature:**

```
g.create_graph(vertices_data, edges_data, inputs=(), outputs=()) -> List[VT]
```

Creates a complete graph structure from vertices and edges specifications.

**Behaviour**

- Takes lists of vertex data and edge data and constructs a graph in Neo4j.
- Vertices are created with all specified properties.
- Edges are created between vertices with the specified edge types.
- Input and output specifications are applied to mark boundary vertices.
- Returns the list of vertex ids created.

**Parameters**

- `vertices_data`: `List[dict]`  
  List of vertex specifications. Each dict should contain:
  - `ty`: `VertexType` — vertex type
  - `phase`: `Optional[FractionLike]` — phase value
  - `qubit`: `FloatInt` — qubit assignment
  - `row`: `FloatInt` — row assignment
- `edges_data`: `List[tuple]`  
  List of edge specifications as tuples: `((source, target), edge_type)`
- `inputs`: `Tuple[VT, ...]`  
  Vertex ids to mark as graph inputs (optional).
- `outputs`: `Tuple[VT, ...]`  
  Vertex ids to mark as graph outputs (optional).

**Returns**

- `List[VT]`  
  List of created vertex ids.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
from fractions import Fraction
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

nodes = [
    {"ty": VertexType.Z, "phase": Fraction(1, 4), "qubit": 0, "row": 0},
    {"ty": VertexType.X, "phase": Fraction(1, 2), "qubit": 1, "row": 1},
]
edges = [((0, 1), EdgeType.SIMPLE)]

vs = g.create_graph(nodes, edges)
print(vs)  # [0, 1]

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### add_edge

**Full method signature:**

```
g.add_edge(edge_pair, edgetype) -> ET
```

Adds a single edge between two vertices.

**Behaviour**

- Creates a `[:Wire]` relationship between the two vertices in Neo4j.
- The edge is attributed with the specified edge type.
- Returns the edge tuple.

**Parameters**

- `edge_pair`: `Tuple[VT, VT]`  
  Tuple of two vertex ids: `(source, target)`.
- `edgetype`: `EdgeType`  
  The type of edge to create (e.g., `EdgeType.SIMPLE` or `EdgeType.HADAMARD`).

**Returns**

- `ET`  
  The edge tuple `(source, target)`.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import EdgeType
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

vertices = g.add_vertices(2)
edge = g.add_edge((vertices[0], vertices[1]), EdgeType.SIMPLE)

print(edge)  # e.g. (0, 1)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### add_edges

**Full method signature:**

```
g.add_edges(edge_pairs, edgetype, edge_data=None) -> None
```

Adds multiple edges to the graph.

**Behaviour**

- Creates `[:Wire]` relationships for each edge pair in Neo4j.
- All edges are attributed with the specified edge type.
- Optionally associates edge data with each edge.

**Parameters**

- `edge_pairs`: `List[Tuple[VT, VT]]`  
  List of edge tuples: `[(source1, target1), (source2, target2), ...]`
- `edgetype`: `EdgeType`  
  The type for all edges (e.g., `EdgeType.SIMPLE` or `EdgeType.HADAMARD`).
- `edge_data`: `Optional[List[dict]]`  
  Optional list of data dictionaries, one per edge.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import EdgeType
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

vertices = g.add_vertices(3)
edges = [(vertices[0], vertices[1]), (vertices[1], vertices[2])]
g.add_edges(edges, EdgeType.SIMPLE)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### remove_edges

**Full method signature:**

```
g.remove_edges(edges) -> None
```

Removes multiple edges from the graph.

**Behaviour**

- Deletes the `[:Wire]` relationships for each specified edge from Neo4j.
- Does not affect vertex properties.

**Parameters**

- `edges`: `List[ET]`  
  List of edge tuples to remove: `[(source1, target1), (source2, target2), ...]`

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import EdgeType
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

vertices = g.add_vertices(3)
edges = [(vertices[0], vertices[1]), (vertices[1], vertices[2])]
g.add_edges(edges, EdgeType.SIMPLE)

g.remove_edges(edges)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### remove_vertices

**Full method signature:**

```
g.remove_vertices(vertices) -> None
```

Removes multiple vertices from the graph.

**Behaviour**

- Deletes the specified vertex nodes from Neo4j.
- Automatically removes all edges connected to the deleted vertices.

**Parameters**

- `vertices`: `List[VT]`  
  List of vertex ids to remove.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

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

vertices = g.add_vertices(5)
g.remove_vertices([vertices[1], vertices[3]])

print(list(g.vertices()))  # [0, 2, 4]

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### remove_vertex

**Full method signature:**

```
g.remove_vertex(vertex) -> None
```

Removes a single vertex from the graph.

**Behaviour**

- Delegates to `remove_vertices([vertex])`.
- Deletes the specified vertex node from Neo4j.
- Automatically removes all edges connected to the deleted vertex.

**Parameters**

- `vertex`: `VT`  
  The vertex id to remove.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

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

vertices = g.add_vertices(3)
g.remove_vertex(vertices[1])

print(list(g.vertices()))  # [0, 2]

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

---

### remove_edge

**Full method signature:**

```
g.remove_edge(edge) -> None
```

Removes a single edge from the graph.

**Behaviour**

- Delegates to `remove_edges([edge])`.
- Removes the `[:Wire]` relationship between the two vertices.
- Does not affect vertex properties.

**Parameters**

- `edge`: `ET`  
  Edge tuple `(source, target)` to remove.

**Returns**

- `None`  
  Mutates the graph in-place.

**Example**

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import EdgeType
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

vertices = g.add_vertices(2)
edge = g.add_edge((vertices[0], vertices[1]), EdgeType.SIMPLE)

g.remove_edge(edge)

print(g.connected(vertices[0], vertices[1]))  # False

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)
