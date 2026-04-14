# Extra information for developers


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

Example snippet:


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
