
## Docker and DevOps

### PostgreSQL + Age

> **Work in Progress:** The database starts successfully, but dependencies still need to be fixed.

**1. Start the Database**
To spin up the database using the `age` profile, run:
```bash
docker compose --profile age up
```

**2. Configure `.env.PSQL`**
Ensure your `.env.PSQL` file contains the following configuration:
```env
DB_TYPE=age
DB_HOST=age
DB_PORT=5432

# Database credentials
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=age_db

# App-level connection string (recommended)
DATABASE_URL=postgresql://postgres:password@age:5432/age_db
```

**3. Stop and Clean Up**
Because this database setup can leave orphaned containers behind, use the following command to stop services and clean them up:
```bash
docker compose down --remove-orphans
```

---

## Environment Variables (.env)

Below is the standard `.env` configuration for the project's various services:

```env
# PyZX
DB_USER=customer
DB_PASSWORD=testkala
BACKEND_NAME=memgraph

# Memgraph
MEMGRAPH_AUTH=customer/testkala
MEMGRAPH_URI="bolt://localhost:7445"

# Neo4j
NEO4J_AUTH=neo4j/testkala
NEO4J_ADMIN=neo4j

# PostgreSQL
POSTGRES_USER=runner
POSTGRES_PASSWORD=testkala
POSTGRES_DB=age_db
```

> **Note on Neo4j:** Because we use the Community Edition of Neo4j, the default username cannot be changed. Even if other login credentials are updated, the username must remain the same. The codebase frequently assumes or hardcodes this default username for this reason.

## Pre-commit Hooks

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


## Mutation Testing with Mutmut

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


