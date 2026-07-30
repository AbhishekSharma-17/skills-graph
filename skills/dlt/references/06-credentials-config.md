# dlt Credentials & Configuration

> Source: https://dlthub.com/docs/general-usage/credentials | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Credential Injection](#credential-injection)
- [Lookup Order](#lookup-order)
- [Native Credential Types](#native-credential-types)
- [Multiple Pipeline Instances](#multiple-pipeline-instances)
- [Code-Based Configuration](#code-based-configuration)
- [Custom Providers](#custom-providers)
- [Error Diagnostics](#error-diagnostics)

## Overview

dlt separates sensitive credentials from code using a layered configuration system:
- **secrets.toml** — passwords, API keys, private keys (never commit)
- **config.toml** — non-sensitive settings (safe to commit)
- **Environment variables** — production deployments, CI/CD
- **Vault providers** — Google Secrets Manager, Azure Key Vault, AWS Secrets Manager

## Configuration Files

Both files live in `.dlt/` relative to the working directory.

### secrets.toml
```toml
# Source credentials
[sources.notion]
api_key = "secret-notion-api-key"

[sources.google_sheets.credentials]
client_email = "service-account@project.iam.gserviceaccount.com"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
project_id = "my-project"

# Destination credentials
[destination.postgres.credentials]
user = "dlthub"
password = "secure-password"

[destination.filesystem]
bucket_url = "s3://my-bucket"

[destination.filesystem.credentials]
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

### config.toml
```toml
[runtime]
log_level = "WARNING"

[extract]
workers = 4

[normalize]
workers = 3

[load]
workers = 20
```

## Environment Variables

Use UPPERCASE with double-underscore (`__`) separators:

```bash
# Source credentials
export SOURCES__NOTION__API_KEY="key_value"
export SOURCES__SQL_DATABASE__CREDENTIALS="postgresql://user:pass@host/db"

# Destination credentials
export DESTINATION__POSTGRES__CREDENTIALS__USER="dlthub"
export DESTINATION__POSTGRES__CREDENTIALS__PASSWORD="pass"
export DESTINATION__FILESYSTEM__BUCKET_URL="s3://bucket"
export DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID="AKIA..."
export DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY="secret"

# Pipeline settings
export EXTRACT__WORKERS=4
export NORMALIZE__WORKERS=3
export LOAD__WORKERS=20
```

For Kubernetes/Docker secrets (alternative separator):
```bash
sources--notion--api-key
```

## Credential Injection

Functions decorated with `@dlt.source`, `@dlt.resource`, or `@dlt.destination` get automatic credential injection:

```python
@dlt.source
def notion_databases(
    database_ids=None,
    api_key: str = dlt.secrets.value  # Marks parameter for injection
):
    # api_key is injected automatically from config
    return [get_database(db_id, api_key) for db_id in database_ids]

# Call without api_key — dlt injects it
pipeline.run(notion_databases(database_ids=["db1", "db2"]))
```

### Injection markers

| Marker | Use for |
|--------|---------|
| `dlt.secrets.value` | Sensitive values (passwords, keys) — searches secrets.toml |
| `dlt.config.value` | Non-sensitive config — searches config.toml |

## Lookup Order

dlt searches for configuration in this priority:

1. **Environment variables**
2. **secrets.toml** and **config.toml**
3. **Vault providers** (Google Secrets Manager, Azure Key Vault, AWS Secrets Manager)
4. **Custom providers**
5. **Default argument values** in function signature

For a parameter `api_key` in source `notion` (file `notion.py`):
1. `sources.notion.notion_databases.api_key`
2. `sources.notion.api_key`
3. `sources.api_key`
4. `api_key`

## Native Credential Types

### ConnectionStringCredentials (SQL databases)
```toml
# As connection string
[sources.sql_database]
credentials = "snowflake://user:password@host/database?warehouse=wh&role=role"

# As structured fields
[sources.sql_database.credentials]
drivername = "snowflake"
username = "user"
password = "password"
database = "database"
host = "account.snowflakecomputing.com"
warehouse = "warehouse_name"
role = "role"
```

### GcpServiceAccountCredentials
```toml
[destination.bigquery.credentials]
client_email = "loader@project.iam.gserviceaccount.com"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
project_id = "my-project"
```

### AwsCredentials
```toml
[destination.filesystem.credentials]
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
region_name = "us-east-1"
```

## Multiple Pipeline Instances

Configure the same source with different credentials using pipeline names:

```toml
[pipeline_prod.sources.sql_database]
credentials = "snowflake://prod_user:pass@host/prod_db"

[pipeline_staging.sources.sql_database]
credentials = "snowflake://staging_user:pass@host/staging_db"
```

```python
prod_pipeline = dlt.pipeline(pipeline_name="pipeline_prod", destination="duckdb")
staging_pipeline = dlt.pipeline(pipeline_name="pipeline_staging", destination="duckdb")
```

## Code-Based Configuration

Set configuration programmatically:

```python
import os
import dlt
from dlt.common.credentials import AwsCredentials

# Via environment variables
os.environ["SOURCES__NOTION__API_KEY"] = os.environ.get("NOTION_KEY")

# Via dlt.config dictionary
dlt.config["destination.filesystem.bucket_url"] = "s3://my-bucket"

# Via dlt.secrets dictionary
dlt.secrets["sources.notion.api_key"] = "key_value"

# Via native credential objects
credentials = AwsCredentials()
dlt.secrets["destination.filesystem.credentials"] = credentials
```

## Custom Providers

Register custom configuration sources:

```python
import json
import dlt
from dlt.common.configuration.providers import CustomLoaderDocProvider

def load_config():
    with open("config.json", "rb") as f:
        return json.load(f)

provider = CustomLoaderDocProvider(
    "my_json_provider",
    load_config,
    supports_secrets=False
)
dlt.config.register_provider(provider)
```

## Error Diagnostics

Missing configuration raises `ConfigFieldMissingException` with details:

```
ConfigFieldMissingException: Following fields are missing:
  api_key in sources.notion.api_key
  
Checked in:
  Environment Variables:
    SOURCES__NOTION__API_KEY
  In secrets.toml:
    sources.notion.api_key
  In config.toml:
    sources.notion.api_key
```

The error lists all attempted lookups with pipeline-prefixed and non-prefixed key paths, environment variable names, and file paths checked.
