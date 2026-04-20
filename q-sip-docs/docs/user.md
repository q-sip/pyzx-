## Backend selection

If you aren't familiar with PyZX beforehand, try first using the vanilla pyzx backend to get yourself familiar.
Then after that, you can select your backend. Neo4j is the slowest, and x is the fastests.

## General instructions for usage

As the project implements database backends for use with PyZX, you need to run a database in the background.
For most use cases, we recommend using Docker so that the DB environment is cleanly isolated.
You can also use Podman instead if you prefer that over Docker.

You should install first docker and docker compose on your device.
Additionally, on some Linux distributions, you should add a docker user to your computer so that you don't need to use `sudo` with each docker related command.
But as always, do not run `sudo` on commands and code you do not understand and/or trust.
The below commands need `sudo` permissions on some machines to work.

Below are brief instructions on installing Docker/docker-compose and the required dependencies:


<details markdown="1">
  <summary>Linux</summary>

  **A) Install Docker**

  Use the command that matches your distro family:

  **Ubuntu / Debian (apt)**
  
```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

**Fedora / RHEL / CentOS Stream (dnf)**

```bash
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

**Older RHEL / CentOS systems (yum)**

```bash
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

------

**B) Verify Docker Compose**

```bash
docker compose version
```

------

**C) Check whether Docker requires sudo**

```bash
docker ps
```

If that works, you're done.

If you get a permission error, add your user to the `docker` group:

```bash
sudo groupadd docker 2>/dev/null || true
sudo usermod -aG docker $USER
newgrp docker
```

Then test again:

```bash
docker ps
```

If it still fails, log out and back in, then rerun:

```bash
docker ps
```

</details>


<details markdown="1">
  <summary>macOS</summary>

  **A) Install Docker**

  **Option 1: Manual install**
  Download Docker Desktop for Mac from [Docker](https://docs.docker.com/desktop/setup/install/mac-install/) and follow the instructions there.

  **Option 2: Homebrew (optional)**
  
```
brew install --cask docker-desktop
open -a Docker
```

---

**B) Verify Docker and Docker Compose**

Docker Compose is included with Docker Desktop, so no separate Compose install is needed.

```bash
docker --version
docker compose version
```

---

**C) Check whether Docker requires sudo**

On macOS, Docker normally works without `sudo`.

```bash
docker ps
```

If that works, you're done.

If it fails:

1. Make sure Docker Desktop is running:

```bash
open -a Docker
```

2. Wait for Docker Desktop to finish starting.

3. Then test again:

```bash
docker ps
```

If this is your first launch, complete the Docker Desktop setup prompts and rerun:

```bash
docker ps
```

</details>


<details markdown="1">
  <summary>Windows</summary>

  **A) Install Docker**

  Download Docker Desktop for Windows from [Docker](https://docs.docker.com/desktop/setup/install/windows-install/).

  ------

  **B) Verify Docker and Docker Compose**

  Docker Compose is included with Docker Desktop, so no separate Compose install is needed.

```powershell
docker --version
docker compose version
```

---

**C) Check whether Docker requires Administrator privileges**

On Windows, Docker normally works without running your terminal as Administrator after installation.

```powershell
docker ps
```

If that works, you're done.

If it fails:

1. Make sure **Docker Desktop** is running.
2. Wait for Docker Desktop to finish starting.
3. Then test again:

```powershell
docker ps
```

If you get a permissions or access error, ask an Administrator to add your user to the `docker-users` group, then sign out and sign back in.

Example command for an Administrator shell:

```powershell
net localgroup docker-users "%USERNAME%" /add
```

</details>

<br>
In the section below, all Docker commands are run in the project's root directory.

-------

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



## Usage

See `example.py` in the project root:

Example usage:

```
def build_small_graph(g):
    v0 = g.add_vertex(VertexType.Z, qubit=0, row=0)
    v1 = g.add_vertex(VertexType.X, qubit=0, row=1)
    v2 = g.add_vertex(VertexType.Z, qubit=1, row=1)
    g.add_edge((v0, v1), EdgeType.SIMPLE)
    g.add_edge((v1, v2), EdgeType.HADAMARD)
    return g



#Vanilla
print("\n=== Vanilla ===")
g = pyzx.Graph()
build_small_graph(g)
print(f"small graph: {g.num_vertices()}v / {g.num_edges()}e")

g_rand = pyzx.generate.cliffordT(3, 15)
before = (g_rand.num_vertices(), g_rand.num_edges())
pyzx.simplify.full_reduce(g_rand)
after = (g_rand.num_vertices(), g_rand.num_edges())
print(f"cliffordT full_reduce: {before[0]}v/{before[1]}e -> {after[0]}v/{after[1]}e")
print(f"backend reported by graph: {getattr(g_rand, 'backend', '?')}")

#Custom backends
BACKENDS = ["age", "neo4j", "memgraph"]

for backend in BACKENDS:
  print(f"\n=== {backend} ===")
  is_vanilla = backend == "vanilla"
  undo = [] if is_vanilla else pyzx_db_addon.force_backend(backend)
  try:
      g = pyzx_db_addon.create_graph(backend)
      build_small_graph(g)
      print(f"small graph: {g.num_vertices()}v / {g.num_edges()}e")

      g_rand = pyzx.generate.cliffordT(3, 15)
      before = (g_rand.num_vertices(), g_rand.num_edges())
      pyzx.simplify.full_reduce(g_rand)
      after = (g_rand.num_vertices(), g_rand.num_edges())
      print(f"cliffordT full_reduce: {before[0]}v/{before[1]}e -> {after[0]}v/{after[1]}e")
      print(f"backend reported by graph: {getattr(g_rand, 'backend', '?')}")
  finally:
      pyzx_db_addon.restore_backend(undo)

```

After this, you can use the backend just like you would use PyZX normally, but everything is saved to memgraph.


## Performance tips

As memgraph and Age stay in memory, it is very performant.
For both of the backends, all the ZX query rewrite implementations are not yet done(?).
Thus any workflow that uses heavily a ZX calculus logic that is not implemented, will see least improvements, and vice versa.

## Transitioning from vanilla PyZX

Transitioning should be as easy as adding the import line `import pyzx_db_addon`, and initializing calling `pyzx_db_addon.force_backend(backend)`, `pyzx_db_addon.create_graph(backend)`, doing everything like you are used to, and then calling `pyzx_db_addon.restore_backend(undo)`.
See the snippet above, and the file example.py in repo root.
