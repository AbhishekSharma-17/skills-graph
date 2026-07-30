# dlt Deployment

> Source: https://dlthub.com/docs/walkthroughs/deploy-a-pipeline | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [dltHub Deploy Command](#dlthub-deploy-command)
- [GitHub Actions](#github-actions)
- [Airflow Integration](#airflow-integration)
- [Dagster Integration](#dagster-integration)
- [Cloud Functions](#cloud-functions)
- [Docker Deployment](#docker-deployment)
- [Orchestrator Best Practices](#orchestrator-best-practices)
- [Credential Management in Production](#credential-management-in-production)

## Overview

dlt runs wherever Python runs. Deployment options range from simple cron jobs to full orchestration platforms:

| Method | Best For |
|--------|----------|
| GitHub Actions | Simple scheduled pipelines, free tier available |
| Airflow | Complex DAGs, existing Airflow infrastructure |
| Dagster | Modern orchestration with asset-based workflows |
| Cloud Functions | Event-driven, serverless pipelines |
| Docker | Containerized deployment on any platform |
| dltHub Cloud | Managed deployment with built-in scheduling |

## dltHub Deploy Command

Generate deployment scaffolding automatically:

```bash
# Deploy to GitHub Actions
dlt deploy my_pipeline.py github-action --schedule "0 */6 * * *"

# Deploy to Airflow
dlt deploy my_pipeline.py airflow-composer

# Deploy to Cloud Run Functions
dlt deploy my_pipeline.py cloud-run-functions
```

## GitHub Actions

Recommended entry point — GitHub offers a generous free tier:

```yaml
# .github/workflows/dlt_pipeline.yml
name: Run dlt Pipeline
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  run_pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run pipeline
        env:
          DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL: ${{ secrets.GCP_CLIENT_EMAIL }}
          DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY: ${{ secrets.GCP_PRIVATE_KEY }}
          SOURCES__MY_SOURCE__API_KEY: ${{ secrets.SOURCE_API_KEY }}
        run: |
          python my_pipeline.py
```

Store credentials as GitHub repository secrets.

## Airflow Integration

### DAG definition
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def run_dlt_pipeline():
    import dlt
    from my_sources import github_source

    pipeline = dlt.pipeline(
        pipeline_name="github_data",
        destination="bigquery",
        dataset_name="github"
    )
    info = pipeline.run(github_source())
    info.raise_on_failed_jobs()
    print(info)

with DAG(
    "dlt_github_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
) as dag:
    load_task = PythonOperator(
        task_id="run_pipeline",
        python_callable=run_dlt_pipeline,
    )
```

### Airflow interval integration
Use Airflow's execution intervals for incremental loading:

```python
@dlt.resource(primary_key="id")
def tickets(
    updated_at=dlt.sources.incremental[int](
        "updated_at",
        allow_external_schedulers=True  # Uses Airflow intervals
    )
):
    for page in get_tickets(start_time=updated_at.start_value):
        yield page
```

When `allow_external_schedulers=True`, dlt reads `data_interval_start` and `data_interval_end` from Airflow context.

## Dagster Integration

```python
from dagster import asset, Definitions
import dlt

@asset
def github_issues():
    pipeline = dlt.pipeline(
        pipeline_name="github",
        destination="duckdb",
        dataset_name="github_data"
    )
    source = github_source()
    info = pipeline.run(source.with_resources("issues"))
    info.raise_on_failed_jobs()
    return {"rows_loaded": info.metrics}

defs = Definitions(assets=[github_issues])
```

## Cloud Functions

### AWS Lambda
```python
import dlt

def handler(event, context):
    pipeline = dlt.pipeline(
        pipeline_name="lambda_pipeline",
        destination="redshift",
        dataset_name="api_data",
        pipelines_dir="/tmp/dlt_pipelines"  # Lambda writable directory
    )
    source = my_api_source()
    info = pipeline.run(source)
    info.raise_on_failed_jobs()
    return {"statusCode": 200, "body": str(info)}
```

### Google Cloud Functions
```python
import dlt
import functions_framework

@functions_framework.http
def run_pipeline(request):
    pipeline = dlt.pipeline(
        pipeline_name="gcf_pipeline",
        destination="bigquery",
        dataset_name="api_data"
    )
    info = pipeline.run(my_source())
    info.raise_on_failed_jobs()
    return str(info)
```

### Storage for serverless
Serverless functions have ephemeral filesystems. Use a FUSE mount or set the data directory:

```python
import os
os.environ["DLT_DATA_DIR"] = "/tmp/dlt_data"
```

## Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "my_pipeline.py"]
```

```bash
docker build -t my-dlt-pipeline .
docker run \
  -e DESTINATION__POSTGRES__CREDENTIALS="postgresql://user:pass@host/db" \
  -e SOURCES__MY_SOURCE__API_KEY="key" \
  my-dlt-pipeline
```

## Orchestrator Best Practices

1. **Use environment variables for credentials** — never store secrets in code or config files in production

2. **Set `pipelines_dir` explicitly** — especially in serverless or containerized environments where the default `~/.dlt/pipelines/` may not persist

3. **Call `info.raise_on_failed_jobs()`** — always check for load failures to fail the task/step rather than silently losing data

4. **Use `refresh="drop_data"` sparingly** — only for full reloads; prefer incremental loading for efficiency

5. **Monitor with `progress="log"`** — in production, use log-based progress monitoring:
   ```python
   pipeline = dlt.pipeline(progress="log")
   ```

6. **Handle state persistence** — pipeline state (incremental cursors) is stored on disk; ensure the `pipelines_dir` persists between runs or use destination state storage

## Credential Management in Production

### Environment variables (recommended)
```bash
export DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID="my-project"
export DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL="loader@..."
export DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY="-----BEGIN..."
```

### Vault integration
dlt supports Google Secrets Manager, Azure Key Vault, and AWS Secrets Manager as configuration providers. Configure via environment variables:

```bash
# Google Secrets Manager
export SECRETS_TOML_PROVIDER="google_secrets"
export GOOGLE_CLOUD_PROJECT="my-project"

# AWS Secrets Manager
export SECRETS_TOML_PROVIDER="aws_secrets"
export AWS_REGION="us-east-1"
```

### Kubernetes secrets
Mount secrets as environment variables or files that dlt reads via its standard lookup chain.
