## General instructions for usage


Example usage:

```
import pyzx
import pyzx_db_addon

g = pyzx.Graph(backend="memgraph")
```

After this, you can use the backend just like you would use PyZX normally, but everything is saved to memgraph.

You can find and edit each of the queries in xxx

This is the status of the queries currently:

| Query  | Status |   Description   |
|--------|--------|-----------------|
| query1 |  ✅ | Proven valid |
| query2 | ⚠️   |  Sometimes fails   |
| query3 | ❌ | Does not work |
