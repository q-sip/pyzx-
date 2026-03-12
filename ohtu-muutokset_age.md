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