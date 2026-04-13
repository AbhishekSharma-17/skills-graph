# Dagger Services

> Source: https://docs.dagger.io/features/services | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Creating Services](#creating-services)
- [Service Binding](#service-binding)
- [Networking Contexts](#networking-contexts)
- [Health Checks](#health-checks)
- [Database Services for Testing](#database-services-for-testing)
- [Multi-Service Pipelines](#multi-service-pipelines)
- [Service Lifecycle](#service-lifecycle)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger supports ephemeral service containers that can be spun up dynamically during pipeline execution. Services enable container-to-container networking, allowing you to run databases, caches, APIs, and other dependencies alongside your pipeline functions.

Key characteristics:
- **Content-addressed hostnames**: Each service gets a canonical hostname
- **Just-in-time**: Services start on demand and stop when no longer needed
- **Health checked**: Services are verified healthy before clients connect
- **Deduplicated**: Identical service definitions share a single instance

## Creating Services

### From a Container

```python
@function
async def start_db(self) -> dagger.Service:
    """Create a PostgreSQL service."""
    return (
        dag.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "testpass")
        .with_env_variable("POSTGRES_DB", "testdb")
        .with_exposed_port(5432)
        .as_service()
    )
```

### With Persistent Storage

```python
@function
async def start_db_cached(self) -> dagger.Service:
    """PostgreSQL with cached data directory."""
    return (
        dag.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "testpass")
        .with_mounted_cache("/var/lib/postgresql/data", dag.cache_volume("pg-data"))
        .with_exposed_port(5432)
        .as_service()
    )
```

## Service Binding

Bind a service to a container to make it accessible by hostname:

```python
@function
async def test_with_db(self, source: dagger.Directory) -> str:
    """Run tests against a real database."""
    db = (
        dag.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "testpass")
        .with_env_variable("POSTGRES_DB", "testdb")
        .with_exposed_port(5432)
        .as_service()
    )

    return await (
        dag.container()
        .from_("python:3.12")
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_service_binding("db", db)  # Accessible as hostname "db"
        .with_env_variable("DATABASE_URL", "postgresql://postgres:testpass@db:5432/testdb")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
        .with_exec(["pytest", "-v"])
        .stdout()
    )
```

The `with_service_binding("alias", service)` method:
- Starts the service container
- Waits for health check to pass
- Makes it accessible at the given alias hostname
- Automatically stops the service when the parent container finishes

## Networking Contexts

### Container-to-Container

The most common pattern — one container accesses another as a service:

```python
redis = (
    dag.container()
    .from_("redis:7")
    .with_exposed_port(6379)
    .as_service()
)

app = (
    dag.container()
    .from_("python:3.12")
    .with_service_binding("cache", redis)
    .with_exec(["python", "-c", "import redis; r = redis.Redis(host='cache'); r.ping()"])
)
```

### Container-to-Host

Access services running on the host machine:

```python
@function
async def test_against_host_db(self, source: dagger.Directory) -> str:
    """Test against a database running on the host."""
    host_db = dag.host().service(
        ports=[dagger.PortForward(backend=5432, frontend=5432)]
    )

    return await (
        dag.container()
        .from_("python:3.12")
        .with_service_binding("db", host_db)
        .with_exec(["python", "-c", "import psycopg2; psycopg2.connect(host='db')"])
        .stdout()
    )
```

### Host-to-Container

Expose a Dagger service to the host:

```python
@function
def dev_server(self, source: dagger.Directory) -> dagger.Service:
    """Start a dev server accessible from the host."""
    return (
        dag.container()
        .from_("node:20")
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["npm", "install"])
        .with_exec(["npm", "run", "dev"])
        .with_exposed_port(3000)
        .as_service()
    )
```

Run from CLI:
```bash
dagger call dev-server --source=. up --ports=3000:3000
```

## Health Checks

Services are health-checked before clients connect. Dagger checks that exposed ports are accepting connections.

### Custom Health Check Timing

```python
service = (
    dag.container()
    .from_("postgres:16")
    .with_env_variable("POSTGRES_PASSWORD", "test")
    .with_exposed_port(5432)
    .as_service(
        args=dagger.ServiceArgs(
            use_entrypoint=True,
        )
    )
)
```

For services with slow startup, the health check retries until the port accepts connections.

## Database Services for Testing

### PostgreSQL

```python
def postgres_service(self) -> dagger.Service:
    return (
        dag.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "test")
        .with_env_variable("POSTGRES_DB", "testdb")
        .with_exposed_port(5432)
        .as_service()
    )
```

### MySQL

```python
def mysql_service(self) -> dagger.Service:
    return (
        dag.container()
        .from_("mysql:8")
        .with_env_variable("MYSQL_ROOT_PASSWORD", "test")
        .with_env_variable("MYSQL_DATABASE", "testdb")
        .with_exposed_port(3306)
        .as_service()
    )
```

### Redis

```python
def redis_service(self) -> dagger.Service:
    return (
        dag.container()
        .from_("redis:7-alpine")
        .with_exposed_port(6379)
        .as_service()
    )
```

### MongoDB

```python
def mongo_service(self) -> dagger.Service:
    return (
        dag.container()
        .from_("mongo:7")
        .with_exposed_port(27017)
        .as_service()
    )
```

## Multi-Service Pipelines

Bind multiple services to a single container:

```python
@function
async def integration_test(self, source: dagger.Directory) -> str:
    """Run integration tests with DB and cache."""
    db = self.postgres_service()
    cache = self.redis_service()

    return await (
        dag.container()
        .from_("python:3.12")
        .with_service_binding("db", db)
        .with_service_binding("cache", cache)
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_env_variable("DATABASE_URL", "postgresql://postgres:test@db:5432/testdb")
        .with_env_variable("REDIS_URL", "redis://cache:6379")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
        .with_exec(["pytest", "tests/integration/", "-v"])
        .stdout()
    )
```

## Service Lifecycle

1. **Creation**: `as_service()` converts a container into a service definition
2. **Start**: Service starts when first referenced by a running container
3. **Health check**: Dagger verifies the service is accepting connections
4. **Active**: Service serves requests from bound containers
5. **Stop**: Service stops when no more containers reference it

Services are **not** started eagerly — they only start when a bound container begins execution.

## Common Pitfalls

1. **Missing `with_exposed_port`**: Services without exposed ports can't be health-checked
2. **Wrong hostname**: Use the alias from `with_service_binding`, not `localhost`
3. **Race conditions**: Dagger handles startup ordering, but slow services may need wait logic
4. **Port conflicts**: Each service binding uses its own hostname, so port numbers can overlap
5. **Not using environment variables**: Hardcoding connection strings reduces portability
