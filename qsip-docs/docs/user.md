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




<details>
  <summary>macOS</summary>

  Hidden content goes here.

  You can include **Markdown** here too.
</details>

<details>
  <summary>Windows</summary>

  Hidden content goes here.

  You can include **Markdown** here too.
</details>

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
