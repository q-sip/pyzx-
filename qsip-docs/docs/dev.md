# Extra information for developers

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
