## Development

### Initial setup

Clone the repo and install the package in editable mode with the optional
dependency groups you need. `test`, `dev`, and `docs` are declared in
`pyproject.toml`:

```bash
git clone https://github.com/q-sip/pyzx-.git
cd pyzx-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,dev,docs]"
```

- `test` — pytest, coverage, mutmut
- `dev` — mypy, pre-commit, pylint
- `docs` — mkdocs, pymdown-extensions

Install only the subset you need, e.g. `pip install -e ".[dev]"` if you
aren't touching docs or running mutation tests.

### Pre-commit Hooks

**1. Installation (One-time setup)**
Ensure your virtual environment is active, then install and configure the pre-commit hooks:
```bash
python -m pip install pre-commit
pre-commit install
```

**2. Committing Changes**
Standard `git commit` commands will automatically trigger the hooks. To manually bypass the hooks (e.g., to skip `pylint` or tests temporarily), use the `--no-verify` flag:
```bash
git commit --no-verify -m "Your commit message"
```

----

### Mutation Testing with Mutmut

> **Note:** `mutmut` requires a passing test suite before you can begin.

**1. Run Mutation Tests**
Running `mutmut run` against a large codebase is extremely slow. It is highly recommended to target specific modules instead. For example:
```bash
mutmut run paths_to_mutate=pyzx/graph/graph_neo4j.py
```

**2. Browse Results**
Once the tests are complete, you can view the killed and survived mutants, along with additional commands, by running:
```bash
mutmut browse
```

**3. Export Statistics**
To generate a simple JSON file in the mutants folder for an easy overview of your results, use:
```bash
mutmut export-cicd-stats
```

### Adding a new backend

Make a new branch for development. 
You should structure new backend implementations similarly to current implementations.

### Adding/modifying queries

You can edit any queries in `.json` files in `zxdb/query_collections/` or `zxdb_age/query_collections/`.

### Project structure overview

```
pyzx-/
├── compose.yaml              # DB services (AGE, Memgraph+Lab, Neo4j+Neodash)
├── .env                      # DB URIs / credentials
├── pyproject.toml            # Package + deps
├── mypy.ini, setup.cfg       # Lint / type config
├── example.py, testing.py    # Demos; testing.py runs every backend
│
├── pyzx_db_addon/            # The addon
│   ├── __init__.py           # Registry, create_graph, force_backend
│   ├── graph_AGE.py          # Apache AGE backend
│   ├── graph_neo4j.py        # Neo4j backend
│   ├── graph_memgraph.py     # Memgraph backend
│   ├── graph_db_rewrite_runner.py  # Rewrite rules on DB graphs
│   ├── zxdb/                 # High-level layer: queries + rule runner
│   │   ├── zxdb.py           # ZXdb class
│   │   ├── query_collections/  # Cypher/SQL JSON bundles
│   │   └── circuits/         # Example graphs (JSON)
│   └── zxdb_age/             # AGE-specific ZXdb variant
│
├── tests/                    # Test suite
│   ├── test_graph_*_contract.py  # Per-backend contract
│   ├── test_graph_age/       # AGE unit tests
│   ├── test_graph_neo4j/     # Neo4j unit tests
│   └── integration/          # PyZX suite run on each backend
│
└── q-sip-docs/               # MkDocs site
```

### Running without Docker

Possible, but you would have to run the databases on your host.
This should work as long as you configure all the parameters correctly in your `.env` file in the project root.
Check the `compose.yaml` to see the most relevant parameters and `pyzx_db_addon/graph_*.py`

### Code quality

- Formatting: Black
- Style: pylint score >= 9.5
- Testing requirements: unittests
