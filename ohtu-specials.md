
## Docker and devops

Now there is posibility to use docker and docker compose. You can choose between Neo4j database and PosgresSQL Age.  

### Neo4j Database
With ```docker compose up --build``` you get both neo4j and the pyzx running.  
The PyZX will run the neo4j_functionality_test.py and be done.  
After that you should be able to see the small demo graph in side neo4j.
The neo4j will start on http://localhost:7474/.  
On addition you will need the the .env.neo4j and .env.pyzx.

The .env.pyzx should be like:
<pre>
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testkala
</pre>
Note: neo4j requires at least 8 char password, otherwise it will not use it.

The .env.neo4j should be like:
<pre>
NEO4J_AUTH=neo4j/testkala
</pre>

The information in neo4j determines what you should put in to the .env.pyzx values.
<pre>
docker compose --profile neo4j up
</pre>
<pre>
docker compose up --watch test-dev
</pre>
Runs the tests with hot reload

<pre>
docker compose up --watch pyzx-dev 
</pre>
Runs the tests again if PyZX changes

### PostgreSQL + Age

WIP!!! Database starts but the dependencies need to be fixed.

<pre>
docker compose --profile age up
</pre>

The .env.PSQL file should be something like the following:

<pre>
DB_TYPE=age

DB_HOST=age
DB_PORT=5432

# Database credentials
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=age_db

# App-level connection string (recommended)
DATABASE_URL=postgresql://postgres:password@age:5432/age_db

</pre>

Currently the database leaves orphans. You can remove them with:
<pre>
docker compose down --remove-orphans
</pre>  
  
  
# Super env  
Here is singular env that should work on all envs at the same time.
It should be called .env

<pre>
# PyZX part:
DB_USER=runner
DB_PASSWORD=testkala
BACKEND_NAME=memgraph

# Comment out the one you dont want to be running
#COMMAND="python -m unittest discover -v -s tests"
COMMAND="python -m manual_ohtu.main_switch"

#Here the commands if you want to keep them alive:
#COMMAND="python -m manual_ohtu.main_switch; echo 'Finished main_switch. Sleeping...'; sleep 600"
#COMMAND="python -m unittest discover -v -s tests; echo 'Finished tests. Sleeping...'; sleep 600"


# Neo4j part:
MEMGRAPH_AUTH=runner/testkala

# Neo4j part:
NEO4J_AUTH=neo4j/testkala


# Postgres part:
POSTGRES_USER=runner
POSTGRES_PASSWORD=testkala
POSTGRES_DB=age_db
</pre>

> [!NOTE]  
> Since we use community neo4j we cannot change the username in it...  
> Thus even if every other login info is changed, that needs to remain.
> The code also currently does often assume or overwrite the neo4j login username for this reason.

## Precommit hooks

Inside your virtual environment, do (one time):
```
python -m pip install pre-commit
pre-commit install
```
To commit, you can commit just normally.
If you want to bypass pylint or tests manually, you can use
```
git commit --no-verify -m "commit msg"
```



## Mutation Testing
Cool, they are indeed.

So we have mutmut as our mutation framework.

First you need to run
```
mutmut run
```
but that is really really slow, due big code base.

So I recommend running it in specific part only, such as:
```
mutmut run pyzx.graph.graph_neo4j
```

Mutmut requires passing test suite.
Once you manage to run the mutmut, you can browse the results using:
```
mutmut browse
```

There you can see all the killed and survived mutants and some additional commands.


One additional command is
```
mutmut export-cicd-stats
```
this makes simple json to the mutants folder allowing you to see the results in simple view.


