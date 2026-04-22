## Architecture

`pyzx-db-addon` is a drop-in layer on top of [PyZX](https://github.com/Quantomatic/pyzx)
that replaces PyZX's in-memory graph representation with one backed by a
graph database. The public API mirrors PyZX's `Graph`, so existing PyZX
code can run against a database backend with minimal changes.

### High-level layout

```
┌────────────────────────────────────┐
│   user code / PyZX algorithms      │   pyzx.simplify, pyzx.generate, ...
└─────────────────┬──────────────────┘
                  │ BaseGraph interface
┌─────────────────▼──────────────────┐
│           pyzx_db_addon            │   Graph factory + backend registry
│  ┌──────────┬─────────┬─────────┐  │
│  │ Memgraph │  Neo4j  │   AGE   │  │   per-backend BaseGraph subclasses
│  └─────┬────┴────┬────┴────┬────┘  │
└────────┼─────────┼─────────┼───────┘
         │         │         │
         ▼         ▼         ▼
     Memgraph    Neo4j    Postgres        (run via compose.yaml)
     bolt        bolt     + AGE
```

### Package structure

```
pyzx_db_addon/
├── __init__.py                   # Registry, create_graph, force_backend
├── graph_AGE.py                  # Apache AGE / Postgres backend
├── graph_neo4j.py                # Neo4j backend
├── graph_memgraph.py             # Memgraph backend
├── graph_db_rewrite_runner.py    # Runs rewrite queries on DB graphs
├── zxdb/                         # High-level layer for bolt backends
│   ├── zxdb.py                   # ZXdb class
│   ├── pyzx_utils.py
│   ├── generate.py
│   └── query_collections/        # Cypher rewrite bundles (JSON)
└── zxdb_age/                     # AGE-specific ZXdb variant
    ├── zxdb_age.py
    └── query_collections/        # SQL / cypher-on-AGE bundles
```

### Two layers

**1. BaseGraph backends (`graph_AGE.py`, `graph_neo4j.py`, `graph_memgraph.py`)**

Each file defines a subclass of `pyzx.graph.base.BaseGraph` whose vertex
and edge operations read and write the underlying database instead of
Python dicts. Every mutation (`add_vertex`, `add_edge`, phase/type
updates) is translated into Cypher (Neo4j / Memgraph) or SQL-over-AGE
(Postgres) and executed against the configured connection.

Because the subclasses satisfy the `BaseGraph` contract, any PyZX
algorithm that accepts a `BaseGraph` — `full_reduce`, `cliffordT`,
simplifiers, extractors — works unchanged.

**2. ZXdb (`zxdb/`, `zxdb_age/`)**

A higher-level wrapper that bundles rewrite rules as parameterised
queries. Rules are stored as JSON in `query_collections/` and executed
via `graph_db_rewrite_runner.py`. This lets a whole rewrite (e.g.
spider fusion) run inside the database as a single Cypher statement
rather than as many round-trips through the BaseGraph API.

`zxdb_age` is a parallel implementation for AGE because AGE's Cypher
dialect differs enough from Memgraph / Neo4j that the queries are not
portable.

### Backend selection — how `force_backend` works

PyZX code typically calls `pyzx.Graph()` or, indirectly, helpers like
`pyzx.generate.cliffordT(...)` that internally reference a
module-level `Graph` symbol. To redirect those call sites without
forking PyZX, `pyzx_db_addon` offers two mechanisms
(`pyzx_db_addon/__init__.py`):

- `create_graph(backend)` — direct factory; returns a `GraphAGE`,
  `GraphNeo4j`, `GraphMemgraph`, or falls back to vanilla `pyzx.Graph`.
- `force_backend(backend)` — walks every loaded `pyzx.*` module,
  finds attributes that still point at PyZX's original `Graph`, and
  rebinds them to the chosen backend class. Returns an *undo list*
  that `restore_backend(undo)` replays to put the old bindings back.

This monkey-patch approach is why `force_backend` must be called
*after* the relevant `pyzx.*` submodules are imported: only attributes
on already-loaded modules get rebound. `__init__.py` preloads
`pyzx.generate`, `pyzx.simplify`, and `pyzx.circuit` for this reason.

### Configuration

All backends read connection details from environment variables (via
`python-dotenv`), so a single `.env` at the project root drives both
`compose.yaml` and the addon:

| Variable            | Backend  |
|---------------------|----------|
| `DB_HOST`, `DB_PORT`, `POSTGRES_*` | AGE |
| `DB_URI_NEO4J`, `DB_USER_NEO4J`, `DB_PASSWORD_NEO4J` | Neo4j |
| `DB_URI_MEMGRAPH`, `DB_USER_MEMGRAPH`, `DB_PASSWORD_MEMGRAPH` | Memgraph |

Each graph instance is namespaced inside its database by a `graph_id`
(auto-generated as a UUID / timestamp suffix if not supplied), so
multiple graphs can coexist in one database without collision.

### Rewrite execution model

```
user calls PyZX simplifier
        │
        ▼
BaseGraph method on GraphNeo4j / GraphMemgraph / GraphAGE
        │   (one Cypher/SQL statement per mutation)
        ▼
database executes + persists
```

For the ZXdb layer the picture changes — a whole rule fires as one
server-side query:

```
user calls ZXdb.run_rule("spider_fusion_rewrite")
        │
        ▼
graph_db_rewrite_runner loads Cypher from query_collections/*.json
        │
        ▼
session.run(cypher, graph_id=...)   # single round-trip
```

This is the main performance lever versus vanilla PyZX: rewrites that
touch many vertices amortise into one query plan instead of thousands
of Python-to-DB hops.

### Testing

Tests live in `tests/` and are split into three tiers:

- `test_graph_*_contract.py` — per-backend BaseGraph contract tests;
  same assertions across AGE, Neo4j, Memgraph.
- `test_graph_age/`, `test_graph_neo4j/` — backend-specific unit tests
  for dialect quirks.
- `integration/` — runs the upstream PyZX test suite against each
  database backend, catching any divergence from vanilla semantics.
