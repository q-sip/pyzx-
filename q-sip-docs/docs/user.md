## Backend selection

...

## Installation

...


## Usage


Example usage:

```
import pyzx
import pyzx_db_addon

g = pyzx.Graph(backend="memgraph")
```

After this, you can use the backend just like you would use PyZX normally, but everything is saved to memgraph.


## Errors

..

## Performance tips

As memgraph and Age stay in memory, it is very performant.
For both of the backends, all the ZX query rewrite implementations are not yet done(?).
Thus any workflow that uses heavily a ZX calculus logic that is not implemented, will see least improvements, and vice versa.

## Transitioning from vanilla PyZX

Transitioning should be as easy as adding the import line `import pyzx_db_addon`, and initializing the graph with the backend parameter being `memgraph`, `neo4j` or `age`
