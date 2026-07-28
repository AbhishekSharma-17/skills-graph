# Deployment

> Source: [airflow.apache.org/docs/…/docker-compose](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html) · v3.3.0

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Compose (Development)](#docker-compose-development)
- [Kubernetes with Helm](#kubernetes-with-helm)
- [Custom Docker Images](#custom-docker-images)
- [CLI Tools](#cli-tools)
- [Database Setup](#database-setup)
- [Logging Configuration](#logging-configuration)
- [Production Checklist](#production-checklist)

## Deployment Options

| Method | Complexity | Use For |
|--------|------------|---------|
| `pip install` + `airflow standalone` | Low | Learning, quick tests |
| Docker Compose | Medium | Development, small teams |
| Kubernetes Helm chart | High | Production, scaling |
| Managed service (Astronomer, MWAA, Cloud Composer) | Low | Production without ops overhead |

## Docker Compose (Development)

### Quick Start

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.3.0/docker-compose.yaml'
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
docker compose up airflow-init
docker compose up -d
```

### Services in docker-compose.yaml

| Service | Port | Role |
|---------|------|------|
| `airflow-api-server` | 8080 | Web UI + REST API |
| `airflow-scheduler` | — | Triggers task execution |
| `airflow-dag-processor` | — | Parses DAG files |
| `airflow-worker` | — | Executes tasks (Celery) |
| `airflow-triggerer` | — | Handles deferrable operators |
| `postgres` | 5432 | Metadata database |
| `redis` | 6379 | Celery message broker |
| `flower` (optional) | 5555 | Celery monitoring |

### Volume Mounts

```yaml
volumes:
  - ./dags:/opt/airflow/dags       # Your DAG files
  - ./logs:/opt/airflow/logs       # Task logs
  - ./plugins:/opt/airflow/plugins # Custom plugins
  - ./config:/opt/airflow/config   # airflow.cfg overrides
```

### Common Operations

```bash
# View logs
docker compose logs airflow-scheduler -f

# Run CLI commands
docker compose run airflow-worker airflow dags list
docker compose run airflow-worker airflow dags trigger my_dag

# Scale workers
docker compose up -d --scale airflow-worker=3

# Restart after config changes
docker compose restart

# Full cleanup
docker compose down --volumes --rmi all
```

### Environment Variables

Override any Airflow config via environment variables:

```yaml
environment:
  AIRFLOW__CORE__EXECUTOR: CeleryExecutor
  AIRFLOW__CORE__PARALLELISM: 32
  AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: 16
  AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL: 30
  AIRFLOW__CELERY__WORKER_CONCURRENCY: 16
```

## Kubernetes with Helm

### Install

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm install airflow apache-airflow/airflow \
    --namespace airflow \
    --create-namespace \
    --set executor=KubernetesExecutor \
    --set images.airflow.tag=3.3.0 \
    --set dags.gitSync.enabled=true \
    --set dags.gitSync.repo=https://github.com/org/airflow-dags.git \
    --set dags.gitSync.branch=main \
    --set dags.gitSync.subPath=dags
```

### Key Helm Values

```yaml
# values.yaml
executor: KubernetesExecutor

images:
  airflow:
    repository: my-registry/airflow
    tag: 3.3.0-custom

dags:
  gitSync:
    enabled: true
    repo: git@github.com:org/airflow-dags.git
    branch: main
    subPath: dags
    sshKeySecret: airflow-ssh-secret

webserver:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi

scheduler:
  replicas: 2  # HA scheduler
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi

workers:
  replicas: 4
  resources:
    requests:
      cpu: 2000m
      memory: 4Gi

postgresql:
  enabled: true
  persistence:
    size: 20Gi

redis:
  enabled: true

logs:
  persistence:
    enabled: true
    size: 50Gi

# Remote logging
config:
  logging:
    remote_logging: "True"
    remote_base_log_folder: "s3://airflow-logs/logs"
    remote_log_conn_id: "aws_default"
```

### Upgrade

```bash
helm upgrade airflow apache-airflow/airflow \
    --namespace airflow \
    -f values.yaml
```

## Custom Docker Images

### Adding Python Packages

```dockerfile
FROM apache/airflow:3.3.0

USER airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### requirements.txt

```
apache-airflow-providers-google==10.0.0
apache-airflow-providers-amazon==8.0.0
apache-airflow-providers-snowflake==5.0.0
apache-airflow-providers-slack==8.0.0
pandas==2.2.0
dbt-core==1.8.0
```

### Build and Push

```bash
docker build -t my-registry/airflow:3.3.0-custom .
docker push my-registry/airflow:3.3.0-custom
```

### Adding System Packages

```dockerfile
FROM apache/airflow:3.3.0

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

## CLI Tools

### airflow CLI (Local Development)

```bash
# DAG management
airflow dags list
airflow dags trigger my_dag --conf '{"key": "value"}'
airflow dags test my_dag 2024-01-01
airflow dags pause my_dag
airflow dags unpause my_dag
airflow dags backfill my_dag -s 2024-01-01 -e 2024-01-31

# Task management
airflow tasks list my_dag
airflow tasks test my_dag my_task 2024-01-01
airflow tasks run my_dag my_task 2024-01-01
airflow tasks clear my_dag -s 2024-01-01 -e 2024-01-31

# Connections
airflow connections list
airflow connections add my_conn --conn-type postgres --conn-host db.example.com
airflow connections delete my_conn
airflow connections export connections.json

# Variables
airflow variables list
airflow variables set my_key my_value
airflow variables get my_key
airflow variables import variables.json

# Database
airflow db migrate
airflow db check
airflow db clean --clean-before-timestamp "2024-01-01"

# Users
airflow users create -u admin -p admin -f Admin -l User -r Admin -e admin@example.com
airflow users list

# System
airflow info
airflow version
airflow config list
airflow cheat-sheet
```

### airflowctl (Airflow 3.x — Remote Operations)

```bash
airflowctl dags list --api-url https://airflow.example.com
airflowctl dags trigger my_dag --api-url https://airflow.example.com
```

## Database Setup

### PostgreSQL (Production)

```ini
[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:password@db.example.com:5432/airflow
sql_alchemy_pool_size = 5
sql_alchemy_max_overflow = 10
sql_alchemy_pool_recycle = 1800
```

```bash
# Initialize the database
airflow db migrate

# Check connectivity
airflow db check

# Clean old metadata (recommended monthly)
airflow db clean --clean-before-timestamp "$(date -d '90 days ago' +%Y-%m-%d)"
```

### Migrations on Upgrade

```bash
# Always backup before upgrading
pg_dump -h db.example.com -U airflow airflow > backup.sql

# Run migrations
airflow db migrate
```

## Logging Configuration

### Local Logging (Default)

```ini
[logging]
base_log_folder = /opt/airflow/logs
dag_processor_manager_log_location = /opt/airflow/logs/dag_processor_manager/dag_processor_manager.log
```

### Remote Logging (Production)

```ini
[logging]
remote_logging = True
remote_base_log_folder = s3://my-bucket/airflow-logs
remote_log_conn_id = aws_default

# OR Google Cloud Storage
remote_base_log_folder = gs://my-bucket/airflow-logs
remote_log_conn_id = google_cloud_default
```

```bash
pip install apache-airflow-providers-amazon  # For S3 logging
pip install apache-airflow-providers-google  # For GCS logging
```

## Production Checklist

### Security

- [ ] Change default admin credentials
- [ ] Enable HTTPS (reverse proxy with nginx/traefik)
- [ ] Configure secrets backend (Vault, AWS SM, GCP SM)
- [ ] Set `expose_config = False`
- [ ] Enable RBAC with appropriate roles
- [ ] Use Fernet key for connection encryption
- [ ] Rotate Fernet keys periodically

### Reliability

- [ ] Use PostgreSQL (never SQLite in production)
- [ ] Enable HA scheduler (multiple replicas)
- [ ] Configure health checks for all components
- [ ] Set up remote logging (S3/GCS)
- [ ] Configure `dagbag_import_timeout` appropriately
- [ ] Set `killed_task_cleanup_time` for orphan task handling

### Performance

- [ ] Tune `parallelism` and `max_active_tasks_per_dag`
- [ ] Set `min_file_process_interval` (30-60s for prod)
- [ ] Configure `parsing_processes` based on CPU cores
- [ ] Use `smart_sensor` for many sensors
- [ ] Enable DAG serialization (default in 3.x)
- [ ] Prune metadata regularly with `airflow db clean`

### Monitoring

- [ ] Export metrics to Prometheus/StatsD
- [ ] Set up alerting for scheduler heartbeat
- [ ] Monitor DAG parsing time
- [ ] Set up SLA miss notifications
- [ ] Configure email alerts for task failures

```ini
[metrics]
statsd_on = True
statsd_host = statsd.monitoring.svc
statsd_port = 8125
statsd_prefix = airflow
```

### Deployment Process

- [ ] DAG files in version control (git)
- [ ] CI pipeline validates DAG parsing
- [ ] CI runs DAG structure tests
- [ ] Staging environment mirrors production
- [ ] Blue-green or rolling deployments for workers
- [ ] Git-sync for DAG distribution (Kubernetes)

## Related Topics

- [Executors](09-executors.md) — Choosing and configuring executors
- [Overview](00-overview.md) — Architecture components
- [Testing](10-testing.md) — CI/CD integration
