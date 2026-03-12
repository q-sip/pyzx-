# GraphAGE

GraphAGE is a class that implements graph database functionality to pyzx, using ApacheAGE as the backend.

It is initialized like this:

## Initialization
```python
from pyzx.graph.graph_AGE import GraphAGE
from dotenv import load_dotenv
import os, uuid

load_dotenv(".env.pyzx")
gid = f"example_{uuid.uuid4().hex}"

g = GraphAGE()
```

## GraphAGE.add_vertices(amount: int) -> List[VT]

Adds `amount` number new vertices to the graph in Neo4j and returns a list of containing the created vertex IDs.

Vertices are created as `(:Node {graph_id, id, t, phase, qubit, row})` with the following defaults:

- t: `VertexType.BOUNDARY`
- phase: `"0"`
- qubit: `-1`
- row: `-1`

Vertex ids are allocated consecutively starting from the current internal vertex index (`self._vindex`). After insertio>

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
from pyzx.graph.graph_age import GraphAGE
from dotenv import load_dotenv
import os, uuid

load_dotenv(".env")

g = GraphAGE()

vs = g.add_vertices(3)

print(vs)  # e.g. [0, 1, 2]

```
See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.remove_vertices(vertices) -> None

Removes multiple vertices from the graph in a single database operation.

When vertices are deleted, all edges connected to them are automatically removed as well (using `DETACH DELETE` in the Cypher query).

### Behaviour

- Takes an iterable of vertex IDs
- Early returns if the list is empty (optimization)
- Uses a WHERE clause with `IN` to match multiple vertex IDs efficiently
- Deletes all matching vertices and their incident edges in a single Cypher query
- Does not return anything; modifies the graph in-place

### Parameters

- `vertices`: Iterable of `VT`  
  The vertex IDs to remove. Can be a list, tuple, set, or any iterable.

### Returns

- `None`

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_remove")

# Create some vertices
vs = g.add_vertices(5)  # [0, 1, 2, 3, 4]

# Add some edges
g.add_edge((vs[0], vs[1]))
g.add_edge((vs[1], vs[2]))
g.add_edge((vs[3], vs[4]))

print(f"Before: {g.num_vertices()} vertices")  # 5

# Remove vertices 1 and 3 (and their connected edges)
g.remove_vertices([vs[1], vs[3]])

print(f"After: {g.num_vertices()} vertices")  # 3

g.close()
```

### Notes

- All edges connected to the removed vertices are automatically deleted.
- This is a bulk operation; removing many vertices at once is more efficient than removing them one by one.
- The method is safe to call with an empty list (it's a no-op).

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.remove_edges(edges) -> None

Removes multiple edges from the graph in a single database operation.

Unlike `remove_vertices()`, this method only deletes `Wire` relationships. The endpoint vertices stay in the graph.

### Behaviour

- Takes an iterable of edge tuples like `(source, target)`
- Early returns if the iterable is empty
- Builds a Cypher list of edge endpoint pairs
- Uses `UNWIND` to process all requested edges in one query
- Matches `:Wire` relationships between the given vertex IDs and deletes them
- Does not return anything; modifies the graph in-place

### Parameters

- `edges`: Iterable of `ET`  
  The edges to remove. Each edge is expected to be a tuple `(s, t)`.

### Returns

- `None`

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_remove_edges")

# Create vertices
vs = g.add_vertices(4)  # [0, 1, 2, 3]

# Add edges
e1 = g.add_edge((vs[0], vs[1]))
e2 = g.add_edge((vs[1], vs[2]))
e3 = g.add_edge((vs[2], vs[3]))

print(f"Before: {g.num_edges()} edges")  # 3

# Remove two edges
g.remove_edges([e1, e3])

print(f"After: {g.num_edges()} edges")  # 1
print(f"Vertices still exist: {g.num_vertices()}")  # 4

g.close()
```

### Notes

- The query uses an undirected edge match, so the order of the edge tuple does not matter for deletion.
- This is a bulk operation; deleting many edges at once is more efficient than deleting them one by one.
- The method is safe to call with an empty iterable (it is a no-op).
- Only edges are removed. No vertices are deleted.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.num_vertices() -> int

Returns the total number of vertices currently stored in the graph.

### Behaviour

- Runs a Cypher query that matches all `Node` vertices
- Uses `count(n)` to compute the total number of vertices
- Converts the AGE `agtype` result into a Python `int`
- Returns `0` if no row is returned

### Parameters

- None

### Returns

- `int`  
  The total number of vertices in the graph.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_num_vertices")

print(g.num_vertices())  # 0

g.add_vertices(4)
print(g.num_vertices())  # 4

g.remove_vertices([1])
print(g.num_vertices())  # 3

g.close()
```

### Notes

- This method counts only vertices, not edges.
- It reflects the current database state of the graph.
- It is useful for quick sanity checks after graph mutations.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.vindex() -> int

Returns the next fresh vertex index.

This method does not query the database. It simply returns the current value of the internal vertex allocator, `self._vindex`.

### Behaviour

- Returns the next vertex id that would be used for automatically created vertices
- Reads the value directly from the Python object
- Does not inspect the database state
- Does not modify the graph

### Parameters

- None

### Returns

- `int`  
  The next fresh vertex index.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_vindex")

print(g.vindex())  # 0

g.add_vertices(3)
print(g.vindex())  # 3

g.add_vertex_indexed(10)
print(g.vindex())  # 11

g.close()
```

### Notes

- This is the internal allocator value used by methods like `add_vertex()` and `add_vertices()`.
- It may differ from the actual maximum vertex id in the database if vertices were removed.
- It is mainly useful for debugging, backend logic, and understanding how fresh ids are assigned.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.num_edges(s: Optional[VT] = None, t: Optional[VT] = None, et: Optional[EdgeType] = None) -> int

Returns the number of edges in the graph.

This method can either count all edges in the graph, or count only the edges between two specific vertices. If an edge type is provided, it can further restrict the count to edges of that type.

### Behaviour

- If called with no arguments, counts all `Wire` relationships in the graph
- If called with both `s` and `t`, counts only edges between those two vertices
- If `et` is also provided, counts only edges of that specific type between `s` and `t`
- Normalizes `(s, t)` so the smaller vertex id comes first before querying
- Converts the AGE `agtype` count result into a Python `int`
- Returns `0` if no row is returned

### Parameters

- `s`: `Optional[VT]`  
  Source vertex ID. Must be provided together with `t` to count edges between two vertices.
- `t`: `Optional[VT]`  
  Target vertex ID. Must be provided together with `s`.
- `et`: `Optional[EdgeType]`  
  Optional edge type filter. Only used when both `s` and `t` are given.

### Returns

- `int`  
  The number of matching edges.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType

g = GraphAGE(graph_id="example_num_edges")

vs = g.add_vertices(3)  # [0, 1, 2]

g.add_edge((vs[0], vs[1]), EdgeType.SIMPLE)
g.add_edge((vs[1], vs[2]), EdgeType.HADAMARD)

print(g.num_edges())        # 2
print(g.num_edges(vs[0], vs[1]))  # 1
print(g.num_edges(vs[1], vs[2], EdgeType.HADAMARD))  # 1

g.close()
```

### Notes

- When counting between two vertices, the method assumes the internal edge storage uses canonical direction, which matches how `add_edge()` inserts edges.
- If only one of `s` or `t` is given, the method falls back to counting all edges.
- This method counts only graph edges (`Wire` relationships), not vertices.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.depth() -> int

Returns the maximum non-negative row index in the graph.

In practice, this gives the largest layer position (`row`) currently assigned to any vertex. If the graph has no valid non-negative row values, it returns `-1`.

### Behaviour

- Runs a Cypher query that matches all vertices with `row >= 0`
- Computes `max(n.row)` in AGE
- Converts the returned `agtype` value to a Python integer
- Stores the result in `self._maxr`
- Returns `-1` when no valid row value is available

### Parameters

- None

### Returns

- `int`  
  The maximum non-negative row index, or `-1` if unavailable.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_depth")

print(g.depth())  # -1 (no rows set yet)

v0 = g.add_vertex(row=0)
v1 = g.add_vertex(row=5)
v2 = g.add_vertex(row=3)

print(g.depth())  # 5

g.set_row(v1, 2)
print(g.depth())  # 3

g.close()
```

### Notes

- Only non-negative rows are considered (`row >= 0`).
- Vertices with `row` missing, null, or negative are ignored by this query.
- `depth()` reflects the current database state each time it is called.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.remove_isolated_vertices() -> None

Deletes isolated vertices and isolated vertex pairs, while updating the ZX scalar correctly.

This is a semantic simplification step: it removes components that are disconnected (or effectively disconnected) from the rest of the diagram and folds their contribution into `self.scalar`.

### Behaviour

The method iterates over vertices and applies two main rules:

#### 1. Isolated single vertices (`degree == 0`)

- If the vertex is `BOUNDARY`, it raises `TypeError` (diagram is ill-typed).
- If the vertex is `H_BOX`, it is removed and its phase is added via `self.scalar.add_phase(...)`.
- Otherwise (ZX-like node), it is removed and added via `self.scalar.add_node(...)`.

#### 2. Isolated pairs (`degree == 1` on both ends)

For a vertex `v` with degree 1, let `w` be its only neighbor:

- Skip if `v` is already marked for removal.
- Skip if `v` or `w` is a boundary vertex.
- Skip if `w` has degree greater than 1 (not an isolated pair).

If valid, both vertices are removed, and scalar update depends on:

- edge type (`SIMPLE` vs `HADAMARD`)
- effective spider types

`H_BOX` is treated as `Z` for this local pair rule before deciding scalar updates.

After collecting all removable vertices, it performs one bulk `remove_vertices(rem)` call.

### Parameters

- None

### Returns

- `None`

### Raises

- `TypeError`  
  If an isolated boundary vertex is found.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import VertexType, EdgeType
from fractions import Fraction

g = GraphAGE(graph_id="example_remove_isolated")

# Create an isolated Z vertex
v_iso = g.add_vertex(ty=VertexType.Z, phase=Fraction(1, 4))

# Create an isolated pair
v1 = g.add_vertex(ty=VertexType.Z, phase=Fraction(1, 4))
v2 = g.add_vertex(ty=VertexType.Z, phase=Fraction(1, 4))
g.add_edge((v1, v2), EdgeType.SIMPLE)

before = g.num_vertices()
g.remove_isolated_vertices()
after = g.num_vertices()

print(before, after)  # after is smaller; scalar updated internally

g.close()
```

### Notes

- This method updates `self.scalar` as part of simplification semantics.
- It is not a plain structural delete; scalar math is part of the operation.
- For isolated pairs, the scalar contribution depends on both edge type and spider types.
- Removal happens in bulk at the end, not immediately per vertex.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.vertices() -> Iterable[VT]

Returns all vertex IDs currently in the graph.

Internally, this method queries AGE for all node ids and converts each returned AGType value into a Python integer.

### Behaviour

- Runs a Cypher query matching all `Node` vertices with a non-null `id`
- Fetches all rows through the backend read helper (`_fetchall`)
- Converts each returned AGType value to `int`
- Returns a Python list of vertex ids (typed as `Iterable[VT]`)

### Parameters

- None

### Returns

- `Iterable[VT]`  
  The vertex IDs currently in the graph.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_vertices")

g.add_vertices(4)  # [0, 1, 2, 3]

verts = g.vertices()
print(verts)            # e.g. [0, 1, 2, 3]
print(list(verts))      # can be iterated like any iterable

g.remove_vertices([1])
print(g.vertices())     # e.g. [0, 2, 3]

g.close()
```

### Notes

- In this backend implementation, the method currently returns a concrete Python list.
- Ordering is determined by query results and should not be relied on as a strict sorted guarantee unless explicitly sorted by caller.
- Useful as a snapshot of current vertex ids before bulk graph transformations.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.edges(s: Optional[VT] = None, t: Optional[VT] = None) -> Iterable[ET]

Returns edges from the graph, either globally or only between a specific vertex pair.

### Behaviour

- If both `s` and `t` are provided:
  - Returns edges that connect exactly those two vertices
  - Uses an undirected match in Cypher (`-[r:Wire]-`)
- If `s` and `t` are not both provided:
  - Returns all edges in the graph
  - Applies `WHERE n1.id <= n2.id` to avoid duplicate reversed pairs
- Converts AGType endpoint values to Python `int`
- Returns edge tuples as `(source, target)` pairs

### Parameters

- `s`: `Optional[VT]`  
  First vertex for pair-specific edge query.
- `t`: `Optional[VT]`  
  Second vertex for pair-specific edge query.

### Returns

- `Iterable[ET]`  
  Iterable of edge tuples.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_edges")

v0, v1, v2 = g.add_vertices(3)
g.add_edge((v0, v1))
g.add_edge((v1, v2))

# All edges
print(g.edges())

# Only edges between two specific vertices
print(g.edges(v0, v1))
print(g.edges(v0, v2))  # usually []

g.close()
```

### Notes

- In this backend, the result is currently a concrete Python list.
- For all-edge queries, duplicate reverse edge tuples are filtered with `n1.id <= n2.id`.
- For pair-specific queries, orientation in storage does not matter because matching is undirected.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.edge(s: VT, t: VT, et: EdgeType = EdgeType.SIMPLE) -> ET

Returns the canonical edge tuple for two vertices.

This method does not query the database and does not create or validate an edge. It only returns the normalized edge identifier used by the backend.

### Behaviour

- Takes two vertex ids `s` and `t`
- Ignores the `et` argument in this backend implementation
- Returns a canonical tuple ordered by vertex id
  - `(s, t)` if `s < t`
  - `(t, s)` otherwise

### Parameters

- `s`: `VT`  
  First vertex id.
- `t`: `VT`  
  Second vertex id.
- `et`: `EdgeType`  
  Edge type parameter from the shared interface. Present for compatibility; not used by this method.

### Returns

- `ET`  
  Canonical edge tuple `(min(s, t), max(s, t))`.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType

g = GraphAGE(graph_id="example_edge")

print(g.edge(5, 2))                       # (2, 5)
print(g.edge(2, 5))                       # (2, 5)
print(g.edge(7, 7, EdgeType.HADAMARD))    # (7, 7)

g.close()
```

### Notes

- This is a pure helper for canonicalizing edge ids.
- It does not check whether vertices exist.
- It does not check whether an actual edge is present in the graph.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.edge_st(edge: ET) -> Tuple[VT, VT]

Returns the source/target tuple representation of an edge.

In this backend, edge identifiers are already stored as tuples, so `edge_st()` is a direct identity mapping.

### Behaviour

- Takes an edge identifier `edge`
- Returns the same tuple unchanged
- Performs no database access
- Performs no validation of edge existence

### Parameters

- `edge`: `ET`  
  Edge identifier tuple.

### Returns

- `Tuple[VT, VT]`  
  The edge endpoints as `(source, target)` in the backend's stored order.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_edge_st")

e = g.edge(9, 3)      # (3, 9)
st = g.edge_st(e)

print(e)   # (3, 9)
print(st)  # (3, 9)

g.close()
```

### Notes

- In GraphAGE, `edge_st(edge)` currently returns `edge` as-is.
- This method exists mainly for backend interface consistency across implementations.
- Use `edge_s()` / `edge_t()` when you specifically need one endpoint.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.edge_s(edge: ET) -> VT

Returns the source endpoint (first element) of an edge tuple.

In GraphAGE, this method delegates to `edge_st(edge)` and returns index `0`.

### Behaviour

- Accepts an edge identifier tuple
- Calls `edge_st(edge)`
- Returns the first endpoint of that tuple
- Performs no database access
- Does not validate that the edge exists in the graph

### Parameters

- `edge`: `ET`  
  Edge identifier tuple.

### Returns

- `VT`  
  The source endpoint (first item in the backend edge tuple).

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_edge_s")

e = g.edge(8, 3)   # canonicalized to (3, 8)
print(g.edge_s(e)) # 3

g.close()
```

### Notes

- In this backend, edges are canonicalized as ordered tuples, so `edge_s` returns the smaller endpoint id for canonical edges.
- This is a lightweight tuple helper for interface consistency.
- Use `edge_t(edge)` to get the second endpoint.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.edge_t(edge: ET) -> VT

Returns the target endpoint (second element) of an edge tuple.

In GraphAGE, this method delegates to `edge_st(edge)` and returns index `1`.

### Behaviour

- Accepts an edge identifier tuple
- Calls `edge_st(edge)`
- Returns the second endpoint of that tuple
- Performs no database access
- Does not validate that the edge exists in the graph

### Parameters

- `edge`: `ET`  
  Edge identifier tuple.

### Returns

- `VT`  
  The target endpoint (second item in the backend edge tuple).

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_edge_t")

e = g.edge(8, 3)   # canonicalized to (3, 8)
print(g.edge_t(e)) # 8

g.close()
```

### Notes

- In this backend, edges are canonicalized as ordered tuples, so `edge_t` returns the larger endpoint id for canonical edges.
- This is a lightweight tuple helper for interface consistency.
- Use `edge_s(edge)` to get the first endpoint.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.connected(v1: VT, v2: VT) -> bool

Returns whether two vertices share at least one edge.

The method queries AGE for `Wire` relationships between `v1` and `v2` and returns `True` if the relationship count is greater than zero.

### Behaviour

- Runs a Cypher query matching `:Wire` edges between `v1` and `v2`
- Uses an undirected pattern (`-[r:Wire]-`), so edge orientation does not matter
- Computes `count(r)`
- Returns `False` if no row is returned
- Otherwise returns `True` when count is greater than `0`

### Parameters

- `v1`: `VT`  
  First vertex id.
- `v2`: `VT`  
  Second vertex id.

### Returns

- `bool`  
  `True` if at least one edge exists between `v1` and `v2`, else `False`.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_connected")

v0, v1, v2 = g.add_vertices(3)
g.add_edge((v0, v1))

print(g.connected(v0, v1))  # True
print(g.connected(v0, v2))  # False

g.close()
```

### Notes

- This method checks existence, not edge type.
- It is unaffected by stored edge direction due to undirected matching.
- If multiple parallel edges existed, any positive count still returns `True`.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.neighbors(vertex: VT) -> Sequence[VT]

Returns all neighboring vertices connected to the given vertex.

The method queries all `Wire` edges touching `vertex`, collects neighbor ids, removes duplicates, and returns them as a list.

### Behaviour

- Runs a Cypher query with an undirected edge pattern: `(n)-[r:Wire]-(m)`
- Filters by `n.id = vertex`
- Returns the ids of adjacent vertices `m.id`
- Converts AGType values to Python integers
- Uses a set internally to remove duplicate neighbor ids
- Returns the neighbors as a Python list

### Parameters

- `vertex`: `VT`  
  Vertex id whose neighbors should be returned.

### Returns

- `Sequence[VT]`  
  Neighbor vertex ids.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_neighbors")

v0, v1, v2, v3 = g.add_vertices(4)
g.add_edge((v0, v1))
g.add_edge((v0, v2))
g.add_edge((v3, v0))

n = g.neighbors(v0)
print(n)  # e.g. [1, 2, 3] (order may vary)

g.close()
```

### Notes

- Result order is not guaranteed because deduplication is done with a set.
- Returns an empty list when no neighbors exist.
- Matching is undirected, so stored edge direction does not affect results.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.vertex_degree(vertex: VT) -> int

Returns the degree of a vertex (the number of incident `Wire` edges).

The method runs a count query in AGE over all `Wire` relationships touching the given vertex id.

### Behaviour

- Matches edges using an undirected pattern: `(n)-[r:Wire]-()`
- Filters by `n.id = vertex`
- Computes `count(r)`
- Converts the AGType count value into a Python integer
- Returns `0` when no row is returned

### Parameters

- `vertex`: `VT`  
  Vertex id whose degree should be computed.

### Returns

- `int`  
  Number of incident edges.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_vertex_degree")

v0, v1, v2 = g.add_vertices(3)
g.add_edge((v0, v1))
g.add_edge((v0, v2))

print(g.vertex_degree(v0))  # 2
print(g.vertex_degree(v1))  # 1
print(g.vertex_degree(v2))  # 1

g.close()
```

### Notes

- Degree is purely edge-count based and does not depend on edge type.
- Uses undirected matching, so storage direction does not matter.
- For isolated vertices, this returns `0`.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.incident_edges(vertex: VT) -> Sequence[ET]

Returns all edges incident to the given vertex.

The method queries all `Wire` relationships touching `vertex` and returns endpoint tuples for each matched edge.

### Behaviour

- Matches edges with an undirected pattern: `(n)-[r:Wire]-(m)`
- Filters by `n.id = vertex`
- Returns endpoint ids `(n.id, m.id)` for each match
- Converts AGType values to Python integers
- Returns a list of edge tuples

### Parameters

- `vertex`: `VT`  
  Vertex id whose incident edges should be listed.

### Returns

- `Sequence[ET]`  
  Edge tuples incident to `vertex`.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE

g = GraphAGE(graph_id="example_incident_edges")

v0, v1, v2 = g.add_vertices(3)
g.add_edge((v0, v1))
g.add_edge((v2, v0))

ie = g.incident_edges(v0)
print(ie)  # e.g. [(0, 1), (0, 2)] or equivalent orientation

g.close()
```

### Notes

- Because matching is undirected, tuple orientation may vary by query result.
- Unlike `edges()`, this method does not explicitly canonicalize tuple order.
- Returns an empty list if the vertex has no incident edges.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.edge_type(e: ET) -> EdgeType

Returns the edge type of a given edge.

This method looks up the `t` property on the matched `Wire` relationship and converts it to a PyZX `EdgeType`.

### Behaviour

- Matches a `Wire` relationship between the two endpoints in `e`
- Reads `r.t` from AGE
- If no matching edge is found, raises `KeyError`
- If `r.t` is missing or null, defaults to `EdgeType.SIMPLE`
- Otherwise converts the numeric value to `EdgeType`

### Parameters

- `e`: `ET`  
  Edge tuple whose type should be returned.

### Returns

- `EdgeType`  
  The edge type (typically `SIMPLE` or `HADAMARD`).

### Raises

- `KeyError`  
  If the specified edge is not found.

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType

g = GraphAGE(graph_id="example_edge_type")

v0, v1 = g.add_vertices(2)
g.add_edge((v0, v1), EdgeType.HADAMARD)

print(g.edge_type((v0, v1)))  # EdgeType.HADAMARD

try:
    print(g.edge_type((v0, 99)))
except KeyError as e:
    print(e)

g.close()
```

### Notes

- Query matching is undirected, so endpoint order in `e` does not matter.
- Missing edge-type property is treated as `SIMPLE`.
- This method reads one edge at a time; bulk type inspection should use backend-specific batching patterns if needed.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)

---

## GraphAGE.set_edge_type(e: ET, t: EdgeType) -> None

Sets the type of a given edge.

This method updates the `t` property of the matched `Wire` relationship in AGE.

### Behaviour

- Matches a `Wire` relationship between the two endpoints in `e`
- Sets `r.t` to `t.value`
- Executes the update directly in AGE
- Does not return a value

### Parameters

- `e`: `ET`  
  Edge tuple to update.
- `t`: `EdgeType`  
  New edge type to store (for example `EdgeType.SIMPLE` or `EdgeType.HADAMARD`).

### Returns

- `None`

### Example

```python
from pyzx.graph.graph_AGE import GraphAGE
from pyzx.utils import EdgeType

g = GraphAGE(graph_id="example_set_edge_type")

v0, v1 = g.add_vertices(2)
g.add_edge((v0, v1), EdgeType.SIMPLE)

print(g.edge_type((v0, v1)))  # EdgeType.SIMPLE

g.set_edge_type((v0, v1), EdgeType.HADAMARD)
print(g.edge_type((v0, v1)))  # EdgeType.HADAMARD

g.close()
```

### Notes

- Endpoint order in `e` is not important because the relationship is matched undirected.
- If no matching edge exists, AGE updates zero rows; this method does not raise by itself.
- Type validation is expected from the `EdgeType` enum passed by caller code.

See source [/pyzx/graph/graph_AGE.py](https://github.com/q-sip/pyzx-/blob/dev/pyzx/graph/graph_AGE.py)