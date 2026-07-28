# Connections & Hooks

> Source: [airflow.apache.org/docs/…/connections](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/connections.html) · v3.3.0

## Table of Contents

- [Connections Overview](#connections-overview)
- [Creating Connections](#creating-connections)
- [Connection URI Format](#connection-uri-format)
- [Using Connections](#using-connections)
- [Hooks](#hooks)
- [Common Hook Types](#common-hook-types)
- [Secrets Backends](#secrets-backends)
- [Custom Connection Types](#custom-connection-types)

## Connections Overview

A Connection stores credentials and parameters needed to communicate with an external system — database host, API key, S3 bucket, etc. Each Connection has:

- **conn_id** — unique identifier used in operators and hooks
- **conn_type** — the system type (postgres, aws, http, etc.)
- **host** — hostname or endpoint
- **port** — port number
- **login** — username
- **password** — password or token
- **schema** — database name or namespace
- **extra** — JSON blob for additional parameters

## Creating Connections

### Via the UI

Navigate to **Admin > Connections > Add Connection** and fill in the fields. This is the simplest approach for interactive setup.

### Via CLI

```bash
airflow connections add 'my_postgres' \
    --conn-type 'postgres' \
    --conn-host 'db.example.com' \
    --conn-port 5432 \
    --conn-login 'airflow' \
    --conn-password 'secret123' \
    --conn-schema 'analytics'

airflow connections add 'my_aws' \
    --conn-type 'aws' \
    --conn-extra '{"region_name": "us-east-1", "role_arn": "arn:aws:iam::role/airflow"}'

# List connections
airflow connections list

# Delete a connection
airflow connections delete 'old_connection'

# Export connections
airflow connections export connections.json
```

### Via Environment Variables

Set `AIRFLOW_CONN_{CONN_ID}` with a URI or JSON value:

```bash
# URI format
export AIRFLOW_CONN_MY_POSTGRES='postgresql://airflow:secret@db.example.com:5432/analytics'

# JSON format (Airflow 2.3+)
export AIRFLOW_CONN_MY_AWS='{
    "conn_type": "aws",
    "extra": {
        "region_name": "us-east-1",
        "role_arn": "arn:aws:iam::123456:role/airflow"
    }
}'
```

Environment variable connections take precedence over database-stored connections.

### Via Python (in DAG or plugin)

```python
from airflow.sdk import Connection

conn = Connection(
    conn_id="my_api",
    conn_type="http",
    host="https://api.example.com",
    extra={"headers": {"Authorization": "Bearer {{ var.value.api_token }}"}},
)
```

## Connection URI Format

```
<conn_type>://<login>:<password>@<host>:<port>/<schema>?param1=value1&param2=value2
```

Examples:

```
# PostgreSQL
postgresql://user:pass@db.example.com:5432/mydb

# MySQL
mysql://user:pass@mysql.example.com:3306/mydb

# HTTP
http://https%3A%2F%2Fapi.example.com

# AWS (login=access_key, password=secret_key)
aws://AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI%2FK7MDENG%2FbPxRfiCYEXAMPLEKEY@

# Google Cloud
google-cloud-platform://?extra__google_cloud_platform__project=my-project
```

Special characters in passwords must be URL-encoded (`%` → `%25`, `@` → `%40`, `/` → `%2F`).

## Using Connections

### In Operators

Most operators accept a `conn_id` parameter:

```python
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.http.operators.http import HttpOperator

query = SQLExecuteQueryOperator(
    task_id="run_query",
    conn_id="warehouse_postgres",
    sql="SELECT COUNT(*) FROM events WHERE dt = '{{ ds }}'",
)

api_call = HttpOperator(
    task_id="call_api",
    http_conn_id="my_api",
    endpoint="/v1/process",
    method="POST",
    data='{"date": "{{ ds }}"}',
)
```

### In Templates

```python
BashOperator(
    task_id="connect",
    bash_command="psql -h {{ conn.warehouse_postgres.host }} -U {{ conn.warehouse_postgres.login }} -d {{ conn.warehouse_postgres.schema }}",
)
```

### Directly via Hooks

```python
@task()
def custom_query():
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    hook = PostgresHook(postgres_conn_id="warehouse_postgres")
    records = hook.get_records("SELECT * FROM summary LIMIT 10")
    return records
```

## Hooks

Hooks are high-level interfaces to external systems. They manage connection lifecycle, handle authentication, and provide convenience methods. Operators use hooks internally.

```python
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.http.hooks.http import HttpHook

@task()
def etl_with_hooks():
    # Read from PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id="source_db")
    df = pg_hook.get_pandas_df("SELECT * FROM users WHERE created_at >= '{{ ds }}'")

    # Write to S3
    s3_hook = S3Hook(aws_conn_id="my_aws")
    s3_hook.load_string(
        string_data=df.to_csv(index=False),
        key=f"data/users/{{ ds }}/users.csv",
        bucket_name="data-lake",
        replace=True,
    )

    return f"Uploaded {len(df)} rows"
```

## Common Hook Types

### Database Hooks

```python
# PostgreSQL
from airflow.providers.postgres.hooks.postgres import PostgresHook
hook = PostgresHook("my_postgres")
hook.get_records("SELECT 1")
hook.get_pandas_df("SELECT * FROM table")
hook.run("INSERT INTO table VALUES (%s)", parameters=["value"])
hook.bulk_load("table", "/tmp/data.csv")

# MySQL
from airflow.providers.mysql.hooks.mysql import MySqlHook
hook = MySqlHook("my_mysql")

# Generic SQL
from airflow.providers.common.sql.hooks.sql import DbApiHook
hook = DbApiHook.get_hook("any_db_conn")
```

### Cloud Hooks

```python
# AWS S3
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
s3 = S3Hook("my_aws")
s3.check_for_key("key", "bucket")
s3.read_key("key", "bucket")
s3.load_file("/local/path", "s3_key", "bucket")

# Google Cloud Storage
from airflow.providers.google.cloud.hooks.gcs import GCSHook
gcs = GCSHook("my_gcp")
gcs.download("bucket", "object", "/local/path")
gcs.upload("bucket", "object", "/local/path")

# Google BigQuery
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
bq = BigQueryHook("my_gcp")
bq.get_pandas_df("SELECT * FROM dataset.table")
```

### HTTP Hook

```python
from airflow.providers.http.hooks.http import HttpHook

http = HttpHook(method="GET", http_conn_id="my_api")
response = http.run(endpoint="/v1/data", headers={"Accept": "application/json"})
data = response.json()
```

## Secrets Backends

Store connections and variables in external secret managers instead of the Airflow database:

### HashiCorp Vault

```ini
[secrets]
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {
    "connections_path": "airflow/connections",
    "variables_path": "airflow/variables",
    "url": "https://vault.example.com:8200",
    "auth_type": "token",
    "token": "s.xxxxxxxxx"
}
```

### AWS Secrets Manager

```ini
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {
    "connections_prefix": "airflow/connections",
    "variables_prefix": "airflow/variables",
    "region_name": "us-east-1"
}
```

### GCP Secret Manager

```ini
[secrets]
backend = airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
backend_kwargs = {
    "connections_prefix": "airflow-connections",
    "variables_prefix": "airflow-variables",
    "project_id": "my-project"
}
```

### Resolution Order

Airflow checks secrets backends in this order:
1. Environment variables (`AIRFLOW_CONN_*`, `AIRFLOW_VAR_*`)
2. Custom secrets backend (Vault, AWS SM, GCP SM)
3. Airflow metadata database

## Custom Connection Types

Provider packages can define custom connection types with specialized UI forms:

```python
from airflow.hooks.base import BaseHook

class MyServiceHook(BaseHook):
    conn_name_attr = "my_service_conn_id"
    default_conn_name = "my_service_default"
    conn_type = "my_service"
    hook_name = "My Service"

    def __init__(self, my_service_conn_id: str = default_conn_name):
        super().__init__()
        self.conn_id = my_service_conn_id
        self.connection = self.get_connection(self.conn_id)

    def get_conn(self):
        import my_service_sdk
        return my_service_sdk.Client(
            api_key=self.connection.password,
            endpoint=self.connection.host,
        )

    def test_connection(self):
        try:
            self.get_conn().ping()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
```

## Testing Connections

```bash
# CLI
airflow connections test my_postgres

# In Python
from airflow.providers.postgres.hooks.postgres import PostgresHook
hook = PostgresHook("my_postgres")
status, message = hook.test_connection()
print(f"{status}: {message}")
```

### Mocking Connections in Tests

```python
from unittest import mock
from airflow.sdk import Connection

conn = Connection(
    conn_type="postgres",
    host="localhost",
    login="test_user",
    password="test_pass",
    schema="test_db",
)
conn_uri = conn.get_uri()

with mock.patch.dict("os.environ", AIRFLOW_CONN_TEST_DB=conn_uri):
    hook = PostgresHook("test_db")
    assert hook.get_connection("test_db").login == "test_user"
```

## Related Topics

- [XComs & Variables](04-xcoms-and-variables.md) — Variable storage and access
- [Operators & Sensors](03-operators-and-sensors.md) — Using conn_id in operators
- [Deployment](11-deployment.md) — Production secrets configuration
