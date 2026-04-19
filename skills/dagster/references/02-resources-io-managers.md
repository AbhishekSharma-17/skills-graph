# Dagster — Resources & I/O Managers

> Source: [docs.dagster.io/concepts/resources](https://docs.dagster.io/concepts/resources)

## Table of Contents

- [ConfigurableResource](#configurableresource)
- [Using Resources in Assets](#using-resources-in-assets)
- [EnvVar](#envvar)
- [Nested Resources](#nested-resources)
- [Resource Lifecycle](#resource-lifecycle)
- [Launch-Time Configuration](#launch-time-configuration)
- [I/O Managers](#io-managers)
- [Custom I/O Manager](#custom-io-manager)
- [Built-in I/O Managers](#built-in-io-managers)
- [Environment Swapping](#environment-swapping)

---

## ConfigurableResource

Resources are external system connections injected into assets via type annotations. Define them by subclassing `ConfigurableResource`:

```python
import dagster as dg
import requests

class GitHubResource(dg.ConfigurableResource):
    api_token: str
    org_name: str

    def get_repos(self) -> list[dict]:
        response = requests.get(
            f"https://api.github.com/orgs/{self.org_name}/repos",
            headers={"Authorization": f"token {self.api_token}"},
        )
        return response.json()
```

## Using Resources in Assets

Resources are injected via type annotation on asset function parameters:

```python
@dg.asset
def repo_list(github: GitHubResource) -> list[dict]:
    return github.get_repos()

@dg.definitions
def defs():
    return dg.Definitions(
        assets=[repo_list],
        resources={
            "github": GitHubResource(
                api_token=dg.EnvVar("GITHUB_TOKEN"),
                org_name="dagster-io",
            )
        },
    )
```

The resource key in `resources=` must match the parameter name in the asset function.

## EnvVar

`EnvVar` resolves environment variables at runtime (not import time), hides values in the UI, and works with Dagster Cloud secrets:

```python
class DatabaseResource(dg.ConfigurableResource):
    host: str
    port: int
    username: str
    password: str

defs = dg.Definitions(
    resources={
        "db": DatabaseResource(
            host=dg.EnvVar("DB_HOST"),
            port=5432,
            username=dg.EnvVar("DB_USER"),
            password=dg.EnvVar("DB_PASSWORD"),
        )
    },
)
```

**Key difference from `os.getenv()`:** `EnvVar` defers resolution to runtime and marks values as secret in the UI. Always prefer `EnvVar` for credentials.

## Nested Resources

Use `ResourceDependency[T]` for resources that depend on other resources:

```python
class CredentialsResource(dg.ConfigurableResource):
    username: str
    password: str

class FileStoreBucket(dg.ConfigurableResource):
    credentials: dg.ResourceDependency[CredentialsResource]
    region: str

    def write(self, data: str):
        client = get_client(
            username=self.credentials.username,
            password=self.credentials.password,
            region=self.region,
        )
        client.write(data)

defs = dg.Definitions(
    resources={
        "bucket": FileStoreBucket(
            credentials=CredentialsResource(
                username="admin",
                password=dg.EnvVar("STORE_PASSWORD"),
            ),
            region="us-east-1",
        ),
    },
)
```

## Resource Lifecycle

### Setup and teardown

```python
from pydantic import PrivateAttr

class APIClientResource(dg.ConfigurableResource):
    api_url: str
    api_key: str
    _session: requests.Session = PrivateAttr()

    def setup_for_execution(self, context: dg.InitResourceContext) -> None:
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def teardown_after_execution(self, context: dg.InitResourceContext) -> None:
        self._session.close()

    def get(self, endpoint: str) -> dict:
        return self._session.get(f"{self.api_url}/{endpoint}").json()
```

### Context manager pattern

```python
from contextlib import contextmanager

class DBConnectionResource(dg.ConfigurableResource):
    connection_string: str

    @contextmanager
    def yield_for_execution(self, context: dg.InitResourceContext):
        conn = create_connection(self.connection_string)
        try:
            self._conn = conn
            yield self
        finally:
            conn.close()

    def query(self, sql: str):
        return self._conn.execute(sql)
```

## Launch-Time Configuration

Defer resource construction until run launch:

```python
class DatabaseResource(dg.ConfigurableResource):
    table: str
    def read(self): ...

defs = dg.Definitions(
    resources={"db_conn": DatabaseResource.configure_at_launch()},
)

@dg.sensor(job=my_job)
def table_sensor():
    for table_name in get_tables():
        yield dg.RunRequest(
            run_config=dg.RunConfig(
                resources={"db_conn": DatabaseResource(table=table_name)},
            ),
        )
```

## I/O Managers

I/O managers handle storage and retrieval of asset values. They separate *what* to compute from *where* to store it.

### ConfigurableIOManager

```python
import json
import os

class JsonIOManager(dg.ConfigurableIOManager):
    base_dir: str

    def _get_path(self, context) -> str:
        parts = list(context.asset_key.path)
        if context.has_partition_key:
            parts.append(context.asset_partition_key)
        return os.path.join(self.base_dir, *parts) + ".json"

    def handle_output(self, context: dg.OutputContext, obj):
        path = self._get_path(context)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj, f)

    def load_input(self, context: dg.InputContext):
        path = self._get_path(context)
        with open(path) as f:
            return json.load(f)
```

### ConfigurableIOManagerFactory (for stateful I/O)

```python
class DBIOManager(dg.IOManager):
    def __init__(self, connection):
        self._conn = connection

    def handle_output(self, context: dg.OutputContext, obj):
        table = "_".join(context.asset_key.path)
        self._conn.write_table(table, obj)

    def load_input(self, context: dg.InputContext):
        table = "_".join(context.asset_key.path)
        return self._conn.read_table(table)

class DBIOManagerFactory(dg.ConfigurableIOManagerFactory):
    connection_string: str

    def create_io_manager(self, context) -> DBIOManager:
        return DBIOManager(create_connection(self.connection_string))
```

### Key context properties

**OutputContext:** `asset_key`, `asset_partition_key`, `has_partition_key`, `step_key`, `name`

**InputContext:** `asset_key`, `asset_partition_key`, `asset_partition_keys`, `asset_partition_key_range`, `asset_partitions_time_window`, `upstream_output`

## Built-in I/O Managers

| Manager | Package | Storage |
|---------|---------|---------|
| `FilesystemIOManager` | `dagster` | Local pickle files |
| `InMemoryIOManager` | `dagster` | In-memory (testing) |
| `S3PickleIOManager` | `dagster-aws` | AWS S3 |
| `GCSPickleIOManager` | `dagster-gcp` | Google Cloud Storage |
| `BigQueryPandasIOManager` | `dagster-gcp-pandas` | BigQuery tables |
| `SnowflakePandasIOManager` | `dagster-snowflake-pandas` | Snowflake tables |
| `DuckDBPandasIOManager` | `dagster-duckdb-pandas` | DuckDB tables |
| `DuckDBPolarsIOManager` | `dagster-duckdb-polars` | DuckDB (Polars) |

## Environment Swapping

Same asset code, different storage backends:

```python
# Development
dev_defs = dg.Definitions(
    assets=[my_assets],
    resources={"io_manager": DuckDBPandasIOManager(database="dev.duckdb")},
)

# Production
prod_defs = dg.Definitions(
    assets=[my_assets],
    resources={
        "io_manager": SnowflakePandasIOManager(
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
        )
    },
)
```
