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