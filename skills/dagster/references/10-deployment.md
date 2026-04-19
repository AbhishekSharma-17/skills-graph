# Dagster — Deployment

> Source: [docs.dagster.io/deployment](https://docs.dagster.io/deployment/oss/deployment-options)

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Local Development](#local-development)
- [Docker Compose](#docker-compose)
- [Kubernetes with Helm](#kubernetes-with-helm)
- [Dagster Cloud](#dagster-cloud)
- [dagster.yaml Configuration](#dagsteryaml-configuration)
- [Run Launchers and Executors](#run-launchers-and-executors)

---

## Architecture Overview

Three long-running services for production:

```
[dagster-webserver]  ←→  [PostgreSQL]  ←→  [dagster-daemon]
  (UI + GraphQL)          (metadata)       (schedules, sensors,
       |                                    run queuing)
       v
[Code Location Server(s)]  ← gRPC →  [Run Workers]
  (port 4000/4266)                     (one per run)
```

1. **dagster-webserver** — serves UI, handles GraphQL queries, launches runs (supports multiple replicas)
2. **dagster-daemon** — manages schedules, sensors, run queue (singleton — no replicas)
3. **Code Location Server** — exposes Definitions via gRPC (one per code location)

## Local Development

```bash
# Modern CLI (recommended)
dg dev
# Starts webserver + daemon on port 3000

# Legacy direct commands
dagster-webserver -h 0.0.0.0 -p 3000
dagster-daemon run  # separate process
```

## Docker Compose

### Dockerfile for webserver/daemon

```dockerfile
FROM python:3.12-slim
RUN pip install dagster dagster-graphql dagster-webserver dagster-postgres dagster-docker
ENV DAGSTER_HOME=/opt/dagster/dagster_home/
RUN mkdir -p $DAGSTER_HOME
COPY dagster.yaml workspace.yaml $DAGSTER_HOME
WORKDIR $DAGSTER_HOME
```

### Dockerfile for user code

```dockerfile
FROM python:3.12-slim
RUN pip install dagster dagster-postgres dagster-docker
COPY my_project/ /opt/dagster/app/
WORKDIR /opt/dagster/app
EXPOSE 4000
HEALTHCHECK CMD dagster api grpc-health-check -p 4000
CMD ["dagster", "code-server", "start", "-h", "0.0.0.0", "-p", "4000", "-m", "my_project.definitions"]
```

### workspace.yaml

```yaml
load_from:
  - grpc_server:
      host: docker_example_user_code
      port: 4000
      location_name: "my_code_location"
```

### docker-compose.yaml

```yaml
services:
  postgresql:
    image: postgres:16
    environment:
      POSTGRES_USER: dagster
      POSTGRES_PASSWORD: dagster
      POSTGRES_DB: dagster
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dagster"]

  user_code:
    build:
      context: .
      dockerfile: Dockerfile_user_code
    environment:
      - DAGSTER_POSTGRES_USER=dagster
      - DAGSTER_POSTGRES_PASSWORD=dagster
      - DAGSTER_POSTGRES_DB=dagster
      - DAGSTER_CURRENT_IMAGE=user_code_image

  webserver:
    build:
      context: .
      dockerfile: Dockerfile_dagster
    entrypoint: ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      postgresql: { condition: service_healthy }
      user_code: { condition: service_healthy }

  daemon:
    build:
      context: .
      dockerfile: Dockerfile_dagster
    entrypoint: ["dagster-daemon", "run"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    restart: on-failure
```

```bash
docker compose up
```

## Kubernetes with Helm

### Setup

```bash
helm repo add dagster https://dagster-io.github.io/helm
helm repo update
helm show values dagster/dagster > values.yaml
```

### Key values.yaml

```yaml
dagster-user-deployments:
  enabled: true
  deployments:
    - name: "my-code-location"
      image:
        repository: "my-registry/my-dagster-project"
        tag: "latest"
        pullPolicy: Always
      dagsterApiGrpcArgs:
        - "--python-file"
        - "/opt/dagster/app/definitions.py"
      port: 3030

postgresql:
  enabled: true  # false for external DB

runLauncher:
  type: K8sRunLauncher  # or CeleryK8sRunLauncher
```

### Install

```bash
helm upgrade --install dagster dagster/dagster -f values.yaml
kubectl get pods
kubectl port-forward <webserver-pod> 8080:80
```

### Per-job K8s resources via tags

```python
@dg.job(tags={
    "dagster-k8s/config": {
        "container_config": {
            "resources": {"limits": {"cpu": "2", "memory": "4Gi"}},
        },
        "job_spec_config": {"ttl_seconds_after_finished": 7200},
    }
})
def resource_intensive_job(): ...
```

## Dagster Cloud

### Serverless deployment

Fully managed — no infrastructure to provision.

- Resource limits: 4 vCPU, 16 GB RAM, 128 GB disk per run
- 4500 step-minutes per day
- Deploy via GitHub, GitLab, or CLI
- US and EU regions

### Hybrid deployment

Dagster-hosted backend + customer-managed agent:

```
[Dagster+ Control Plane]         [Customer Infrastructure]
+---------------------+         +-------------------------+
| Web UI / GraphQL    |  HTTPS  | Agent (K8s/ECS/Docker)  |
| Metadata Database   |  <--->  |   ├── Code Server(s)    |
| Scheduler / Sensor  |         |   └── Run Worker(s)     |
+---------------------+         +-------------------------+
```

Agent types: **Kubernetes** (recommended), **AWS ECS**, **Docker**, **Local**.

User code never leaves customer environment. SOC 2 Type II certified.

## dagster.yaml Configuration

```yaml
# Run storage (PostgreSQL recommended for production)
storage:
  postgres:
    postgres_db:
      hostname: localhost
      username: dagster
      password: dagster
      db_name: dagster

# Run coordinator (queued execution)
run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator

# Run launcher
run_launcher:
  module: dagster_docker
  class: DockerRunLauncher
  config:
    env_vars:
      - DAGSTER_POSTGRES_USER
      - DAGSTER_POSTGRES_PASSWORD
    network: dagster_network

# Scheduler
scheduler:
  module: dagster.core.scheduler
  class: DagsterDaemonScheduler
```

## Run Launchers and Executors

### Run Launchers (instance-level)

| Launcher | Description |
|----------|-------------|
| `DefaultRunLauncher` | Runs in the same process (dev only) |
| `DockerRunLauncher` | One Docker container per run |
| `K8sRunLauncher` | One Kubernetes Job per run |
| `CeleryK8sRunLauncher` | Celery workers for distributed step execution |

### Executors (per-job)

| Executor | Description |
|----------|-------------|
| `in_process_executor` | All steps in one process (low overhead) |
| `multiprocess_executor` | Each step in a separate process (default) |
| `k8s_job_executor` | Each step in a separate K8s pod |
| `celery_k8s_job_executor` | Each step via Celery + K8s |

Execution flow: Run Coordinator → queues runs → Run Launcher → creates workers → Executor → runs steps.
