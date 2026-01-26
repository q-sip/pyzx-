# GraphNeo4j

GraphNeo4j is a class that implements graph database functionality to pyzx, using Neo4j as the backend.

It is initialized like this:

## Initialization
```
g = GraphNeo4j(
    uri=os.getenv("NEO4J_URI", ""),
    user=os.getenv("NEO4J_USER", ""),
    password=os.getenv("NEO4J_PASSWORD", ""),
    graph_id=unique_graph_id,
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
Returns the maximum depth of a GraphNeo4j object from the database.
If it is unsure about depth (NULL nodes or no rows) or it fails, it returns -1.

### Parameters
- No parameters

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
