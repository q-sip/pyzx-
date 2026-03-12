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

## GraphNeo4j.add_vertex_indexed(self, v: VT) -> None

Adds a vertex that is guaranteed to have the chosen index (i.e. vertex “name” / id).

This mirrors the semantics of `BaseGraph.add_vertex_indexed` and is primarily used by the editor / ZXLive undo stack: undo requires that re-created vertices preserve their original id.

### Behaviour

- Checks whether a node already exists with `(:Node {graph_id: self.graph_id, id: v})`.
  - If it exists, raises `ValueError`.
- Otherwise creates the node as:

  `(:Node {graph_id, id, t, phase, qubit, row})`

  with defaults:

  - t: `VertexType.BOUNDARY`
  - phase: `"0"`
  - qubit: `-1`
  - row: `-1`

- Updates the internal vertex allocator:
  - If `v >= self._vindex`, then sets `self._vindex = v + 1`.
  - If `v < self._vindex`, `self._vindex` is unchanged.

### Parameters

- v: `VT`  
  The explicit vertex id to allocate. Must be unused within the current `graph_id`.

### Returns

- `None`  
  Mutates the graph in-place.

### Raises

- `ValueError`  
  If the index `v` is already in use for this graph (`graph_id`).

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

g.add_vertex_indexed(5)  # creates Node with id=5
# g.add_vertex_indexed(5)  # would raise ValueError

g.close()
```



## GraphNeo4j.set_outputs(self, outputs: Tuple[VT, ...])

Sets the outputs of the graph.

This mirrors the semantics of `BaseGraph.set_outputs` and updates both the in-memory output tuple (`self._outputs`) and the Neo4j labels used to mark output boundary nodes.

### Behaviour

- Updates the in-memory output tuple:

  `self._outputs = tuple(outputs)`

- Synchronizes Neo4j labels for the current `graph_id`:

  1) Clears all existing output markers:
     - removes label `:Output` from any node currently labeled `:Output`.

  2) Marks the new output nodes:
     - for each vertex id in `outputs`, matches `(:Node {graph_id, id})` and sets label `:Output`.

Passing an empty tuple clears all output labels for the graph.

### Parameters

- outputs: `Tuple[VT, ...]`  
  Tuple of vertex ids that should be treated as the outputs of this ZX-diagram.

### Returns

- `None`  
  Mutates the graph in-place.

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

g.add_vertices(4)          # ids: 0,1,2,3
g.set_outputs((1, 3))      # marks nodes 1 and 3 as outputs
g.set_outputs(tuple())     # clears outputs

g.close()
```

## GraphNeo4j.outputs(self) -> Tuple[VT, ...]

Gets the outputs of the graph.

### Behaviour

- If `self._outputs` is already set and non-empty, returns it without querying Neo4j.
- Otherwise reads output vertices from Neo4j using the `:Output` label for the current `graph_id`:

  - matches `(:Output {graph_id})`
  - returns their `id` values ordered by `id`

- Caches the result by setting `self._outputs` to the returned tuple.

If there are no output labels (and `self._outputs` is empty), returns an empty tuple.

### Parameters

- None

### Returns

- `Tuple[VT, ...]`  
  The output vertex ids, e.g. `(1, 4)`.

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

g.add_vertices(5)
g.set_outputs((4, 1))

print(g.outputs())  # (1, 4)

g.close()
```

## GraphNeo4j.set_inputs(self, inputs: Tuple[VT, ...])

Sets the inputs of the graph.

This mirrors the semantics of `BaseGraph.set_inputs` and updates both the in-memory input tuple (`self._inputs`) and the Neo4j labels used to mark input boundary nodes.

### Behaviour

- Updates the in-memory input tuple:

  `self._inputs = tuple(inputs)`

- Synchronizes Neo4j labels for the current `graph_id`:

  1) Clears all existing input markers:
     - removes label `:Input` from any node currently labeled `:Input`.

  2) Marks the new input nodes:
     - for each vertex id in `inputs`, matches `(:Node {graph_id, id})` and sets label `:Input`.

Passing an empty tuple clears all input labels for the graph.

### Parameters

- inputs: `Tuple[VT, ...]`  
  Tuple of vertex ids that should be treated as the inputs of this ZX-diagram.

### Returns

- `None`  
  Mutates the graph in-place.

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

g.add_vertices(4)         # ids: 0,1,2,3
g.set_inputs((0, 2))      # marks nodes 0 and 2 as inputs
g.set_inputs(tuple())     # clears inputs

g.close()
```

## GraphNeo4j.inputs(self) -> Tuple[VT, ...]

Gets the inputs of the graph.

### Behaviour

- If `self._inputs` is already set and non-empty, returns it without querying Neo4j.
- Otherwise reads input vertices from Neo4j using the `:Input` label for the current `graph_id`:

  - matches `(:Input {graph_id})`
  - returns their `id` values ordered by `id`

- Caches the result by setting `self._inputs` to the returned tuple.

If there are no input labels (and `self._inputs` is empty), returns an empty tuple.

### Parameters

- None

### Returns

- `Tuple[VT, ...]`  
  The input vertex ids, e.g. `(1, 4)`.

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

g.add_vertices(5)
g.set_inputs((4, 1))

print(g.inputs())  # (1, 4)

g.close()
```


## GraphNeo4j.clone(self) -> GraphNeo4j

Creates an identical copy of the graph in Neo4j **without any relabeling** (vertex ids and edge properties are preserved), stored under a **new `graph_id` namespace**.

### Behaviour

* Allocates a new graph namespace by creating a fresh `graph_id` of the form:

  `"<old_graph_id>_clone_<random_hex>"`

* Reads a snapshot of the current graph from Neo4j for the current `graph_id`:

  * all nodes `(:Node {graph_id})`, including:

    * all node properties via `properties(n)`
    * all labels via `labels(n)` (used to detect `:Input` and `:Output`)
  * all directed edges `(:Node {graph_id})-[r:Wire]->(:Node {graph_id})`, including:

    * all relationship properties via `properties(r)`

* Writes the copy into Neo4j under the new `graph_id`:

  * recreates nodes as `(:Node)` and sets their full property maps (with `graph_id` rewritten to the new value)
  * recreates relationships as directed `[:Wire]` and sets their full property maps

* Preserves **vertex ids** (the `id` property of each node) exactly; no remapping/reindexing is performed.

* Preserves input/output markers:

  * If `self._inputs` / `self._outputs` are set in memory, those are used as the authoritative order.
  * Otherwise the clone derives inputs/outputs from `:Input` and `:Output` labels found in Neo4j.
  * The clone sets `:Input` / `:Output` labels on the copied nodes accordingly and stores the same tuples in memory.

* Copies Python-side `BaseGraph` state that is not stored in Neo4j:

  * `scalar` (copied, not shared)
  * phase-tracking fields if enabled (`track_phases`, `phase_index`, `phase_mult`, `max_phase_index`, `phase_master`)
  * backend bookkeeping such as `_vindex` and `_maxr`

### Parameters

* None

### Returns

* `GraphNeo4j`
  A new `GraphNeo4j` instance pointing to the copied graph (new `graph_id`), with identical structure and metadata.

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
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

# Build a simple graph
vertices_data = [
    {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
    {"ty": VertexType.Z, "row": 1, "qubit": 0, "phase": 0},
    {"ty": VertexType.BOUNDARY, "row": 2, "qubit": 0},
]
edges_data = [
    ((0, 1), EdgeType.SIMPLE),
    ((1, 2), EdgeType.SIMPLE),
]
g.create_graph(vertices_data=vertices_data, edges_data=edges_data, inputs=[0], outputs=[2])

# Add custom metadata (will be preserved by clone)
g.set_vdata(1, "tag", "middle")
g.set_edata((0, 1), "weight", 123)

g2 = g.clone()

print(g.graph_id)   # original graph namespace
print(g2.graph_id)  # new graph namespace (different)

print(g.inputs(), g.outputs())    # (0,) (2,)
print(g2.inputs(), g2.outputs())  # (0,) (2,)

# Vertex ids are preserved (no relabeling)
print(sorted(g.vertices()))   # [0, 1, 2]
print(sorted(g2.vertices()))  # [0, 1, 2]

g.close()
g2.close()
```
## GraphNeo4j.row(vertex: VT) -> FloatInt

Returns the `row` value associated to the vertex. If no row has been set, returns `-1`.

Vertices in Neo4j are stored as `(:Node {graph_id, id, t, phase, qubit, row})` with the following defaults:

- t: `VertexType.BOUNDARY`
- phase: `"0"`
- qubit: `-1`
- row: `-1`

### Parameters

- vertex: `VT` (int)  
  The id of the vertex whose row value is to be retrieved.

### Returns

- `FloatInt` (float or int)  
  The row index of the vertex, or `-1` if not set.

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

vs = g.add_vertices(1)
r = g.row(vs[0])
print(r)  # -1 (default)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.set_row(vertex: VT, r: FloatInt) -> None

Sets the `row` value associated to the vertex.

Vertices in Neo4j are stored as `(:Node {graph_id, id, t, phase, qubit, row})`. The row property is used to determine the depth/layer of the vertex in the circuit layout.

### Parameters

- vertex: `VT` (int)  
  The id of the vertex whose row is to be set.
- r: `FloatInt` (float or int)  
  The row index to assign to the vertex.

### Returns

- `None`  
  Updates the row value in the database. Does not return anything.

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

vs = g.add_vertices(1)
g.set_row(vs[0], 2)
print(g.row(vs[0]))  # 2

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.create_graph(vertices_data, edges_data, inputs, outputs) -> List[VT]

Creates a complete graph with given vertices and edges in a single transaction. This is an efficient way to construct a full graph structure at once.

### Behaviour

- Allocates consecutive vertex IDs starting from `self._vindex`
- Creates all vertices as `(:Node {graph_id, id, t, phase, qubit, row})` with default values
- Creates directed `[:Wire]` relationships between specified vertex pairs
- Marks input vertices with `:Input` label
- Marks output vertices with `:Output` label
- Updates `self._vindex`, `self._inputs`, and `self._outputs`
- Returns empty list if `vertices_data` is empty

### Parameters

- vertices_data: `List[dict]`  
  List of vertex specifications. Each dict may contain:
  - `ty`: `VertexType` (default: `VertexType.BOUNDARY`)
  - `phase`: phase value (default: `0`)
  - `qubit`: qubit index (default: `-1`)
  - `row`: row index (default: `-1`)

- edges_data: `List[Tuple[Tuple[int, int], EdgeType]]`  
  List of edges as `((source_index, target_index), edge_type)` where indices refer to positions in `vertices_data`

- inputs: `Optional[List[int]]`  
  Indices in `vertices_data` to mark as inputs (default: `None`)

- outputs: `Optional[List[int]]`  
  Indices in `vertices_data` to mark as outputs (default: `None`)

### Returns

- `List[VT]`  
  List of the created vertex IDs

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
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

# Create a simple 3-vertex graph
vertices_data = [
    {"ty": VertexType.BOUNDARY, "row": 0, "qubit": 0},
    {"ty": VertexType.Z, "row": 1, "qubit": 0, "phase": 0.5},
    {"ty": VertexType.BOUNDARY, "row": 2, "qubit": 0},
]
edges_data = [
    ((0, 1), EdgeType.SIMPLE),
    ((1, 2), EdgeType.SIMPLE),
]

vertex_ids = g.create_graph(
    vertices_data=vertices_data,
    edges_data=edges_data,
    inputs=[0],
    outputs=[2]
)

print(vertex_ids)  # e.g. [0, 1, 2]

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.add_edge(edge_pair, edgetype) -> ET

Adds a single edge between two vertices with the specified type and returns the edge identifier.

### Behaviour

- Handles self-loops on ZX-like vertices (Hadamard self-loops add π to the phase)
- If vertices are already connected, applies ZX-calculus fusion rules:
  - Same-colored spiders with fusing edge: no change
  - Same-colored spiders with opposite edge types: converts to fusing edge, adds π to phase, updates scalar
  - Same-colored spiders with double Hopf edge: removes edge, updates scalar
- For Z-like/H-box combinations with simple edges: returns existing edge
- Creates new edge if vertices are not connected
- Updates scalar according to ZX-calculus rules when appropriate

### Parameters

- edge_pair: `Tuple[VT, VT]`  
  Pair of vertex IDs to connect

- edgetype: `EdgeType` (default: `EdgeType.SIMPLE`)  
  Type of edge: `EdgeType.SIMPLE` (regular) or `EdgeType.HADAMARD`

### Returns

- `ET` (edge tuple)  
  The edge identifier as `(source, target)` tuple

### Raises

- `ValueError`  
  If attempting self-loop on non-ZX vertex or parallel edges on incompatible vertex types

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
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

v1, v2 = g.add_vertices(2)
g.set_type(v1, VertexType.Z)
g.set_type(v2, VertexType.Z)

edge = g.add_edge((v1, v2), EdgeType.SIMPLE)
print(edge)  # (0, 1) or (1, 0)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.add_edges(edge_pairs, edgetype, edge_data) -> None

Adds multiple edges at once in a single transaction. More efficient than calling `add_edge` multiple times.

### Behaviour

- Processes each edge pair through ZX-calculus rules (self-loops, existing edges)
- Skips self-loops on non-Hadamard edges
- Updates existing edge types if edges already exist
- Creates new edges for unconnected vertex pairs
- Uses `MERGE` in Neo4j to handle concurrent modifications safely

### Parameters

- edge_pairs: `Iterable[tuple[int, int]]`  
  Iterable of `(source, target)` vertex ID pairs

- edgetype: `EdgeType` (default: `EdgeType.SIMPLE`)  
  Default edge type for all edges

- edge_data: `Optional[Iterable[EdgeType]]` (keyword-only)  
  Optional iterable of edge types, one per edge pair. Must match length of `edge_pairs` if provided.

### Returns

- `None`  
  Mutates the graph in-place

### Raises

- `ValueError`  
  If `edge_data` length doesn't match `edge_pairs` length

### Example

```python
from pyzx.graph.graph_neo4j import GraphNeo4j
from pyzx.utils import VertexType, EdgeType
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

vertices = g.add_vertices(4)

# Add multiple edges at once
g.add_edges(
    [(vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[3])],
    edgetype=EdgeType.SIMPLE
)

# Or with different types per edge
g.add_edges(
    [(vertices[0], vertices[2]), (vertices[1], vertices[3])],
    edge_data=[EdgeType.HADAMARD, EdgeType.SIMPLE]
)

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.remove_edges(edges) -> None

Removes multiple edges from the graph in a single transaction.

### Behaviour

- Deletes all `[:Wire]` relationships matching the specified edge pairs
- Uses undirected matching (removes regardless of edge direction in Neo4j)
- Does nothing if `edges` is empty
- Does not update vertex properties or labels

### Parameters

- edges: `List[ET]`  
  List of edge tuples `(source, target)` to remove

### Returns

- `None`  
  Mutates the graph in-place

### Example

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
g.add_edges([(vertices[0], vertices[1]), (vertices[1], vertices[2])])

# Remove multiple edges
g.remove_edges([(vertices[0], vertices[1]), (vertices[1], vertices[2])])

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.remove_vertices(vertices) -> None

Removes multiple vertices and their incident edges from the graph.

### Behaviour

- Uses `DETACH DELETE` to remove vertices and all connected relationships atomically
- Updates `self._inputs` to remove deleted vertices
- Updates `self._outputs` to remove deleted vertices
- Does nothing if `vertices` is empty

### Parameters

- vertices: iterable of `VT`  
  Vertex IDs to remove

### Returns

- `None`  
  Mutates the graph in-place

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

vertices = g.add_vertices(5)
g.set_inputs((vertices[0],))
g.set_outputs((vertices[4],))

# Remove middle vertices
g.remove_vertices([vertices[1], vertices[2], vertices[3]])

print(list(g.vertices()))  # [0, 4]

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.remove_vertex(vertex) -> None

Removes a single vertex and its incident edges from the graph. Convenience wrapper around `remove_vertices`.

### Behaviour

- Delegates to `remove_vertices([vertex])`
- Removes the vertex node and all connected edges atomically
- Updates inputs/outputs if the removed vertex was marked as input/output

### Parameters

- vertex: `VT`  
  Vertex ID to remove

### Returns

- `None`  
  Mutates the graph in-place

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

vertices = g.add_vertices(3)
g.remove_vertex(vertices[1])

print(list(g.vertices()))  # [0, 2]

g.close()
```

See source [/pyzx/graph/graph_neo4j.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_neo4j.py)

## GraphNeo4j.remove_edge(edge) -> None

Removes a single edge from the graph. Convenience wrapper around `remove_edges`.

### Behaviour

- Delegates to `remove_edges([edge])`
- Removes the `[:Wire]` relationship between the two vertices
- Does not affect vertex properties

### Parameters

- edge: `ET`  
  Edge tuple `(source, target)` to remove

### Returns

- `None`  
  Mutates the graph in-place

### Example

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
