
## Docker and DevOps

### PostgreSQL + Age

**1. Start the Database**
To spin up the database using the `age` profile, run:
```bash
docker compose --profile age up
```

**2. Inspect the database contents by going to http://localhost:8080/?pgsql=age&username=postgres&db=postgres**
- password is ``postgres``


**3. Stop and Clean Up**
Because this database setup can leave orphaned containers behind, use the following command to stop services and clean them up:
```bash
docker compose down --remove-orphans
```

---

### Memgraph + Memlab

**1. Start the Database**
To spin up the database using the `mem` profile, run:
```bash
docker compose --profile mem up
```

**2. Inspect the database contents by going to http://localhost:3000**
First time:
Manual connect --> New connection --> Memgraph instance
--> Fill field "Host" with ``memgraph``
--> Connect

After first time:
Click ``Connect now``

**3. Stop and Clean Up**
Because this database setup can leave orphaned containers behind, use the following command to stop services and clean them up:
```bash
docker compose down --remove-orphans
```

---

### Memgraph + postgres at the same time

**1. Start the Database**
To spin up the database using the `all` profile, run:
```bash
docker compose --profile all up
```

**2. Refer to previous section step 2 for UI access**
Both adminer and memlab are up, so you can use either or both at the same time.


**3. Stop and Clean Up**
Because this database setup can leave orphaned containers behind, use the following command to stop services and clean them up:
```bash
docker compose down --remove-orphans
```



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

----

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
