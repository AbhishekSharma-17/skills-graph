# Dagster — Dagster Pipes

> Source: [docs.dagster.io/concepts/dagster-pipes](https://docs.dagster.io/concepts/dagster-pipes)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Subprocess Pipes](#subprocess-pipes)
- [Kubernetes Pipes](#kubernetes-pipes)
- [Databricks Pipes](#databricks-pipes)
- [Docker Pipes](#docker-pipes)
- [External Script API](#external-script-api)
- [Supported Environments](#supported-environments)

---

## Overview

Dagster Pipes lets you invoke code running in external processes while retaining Dagster's scheduling, metadata reporting, and observability. The external process uses the lightweight `dagster-pipes` package (no Dagster dependency required) to communicate back.

Use Pipes when:
- External code runs in a different environment (Databricks, Kubernetes, Lambda)
- You can't or don't want to install full Dagster in the execution environment
- You need to orchestrate existing scripts without rewriting them

## Architecture

```
[Dagster Orchestration]              [External Process]
+----------------------------+       +---------------------------+
| @asset using PipesClient   | ----> | Script imports            |
|   - PipesSubprocessClient  | ctx   | dagster_pipes             |
|   - PipesK8sClient         | ----> |   - open_dagster_pipes()  |
|   - PipesDatabricksClient  |       |   - pipes.log.info()      |
|   - PipesDockerClient      | <---- |   - pipes.report_asset_   |
|                            | events|     materialization()      |
+----------------------------+       +---------------------------+
```

Context is injected into the external process (via env vars, files, or cloud storage). Events and metadata flow back via stdout, files, or cloud storage.

## Subprocess Pipes

Built-in — no extra package required.

### Dagster asset

```python
import shutil
import dagster as dg

@dg.asset
def subprocess_asset(
    context: dg.AssetExecutionContext,
    pipes_subprocess_client: dg.PipesSubprocessClient,
) -> dg.MaterializeResult:
    cmd = [shutil.which("python"), "scripts/external_code.py"]
    return pipes_subprocess_client.run(
        command=cmd,
        context=context,
    ).get_materialize_result()

defs = dg.Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)
```

### External script (scripts/external_code.py)

```python
from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    pipes.log.info("Running external computation")
    result = do_computation()
    pipes.report_asset_materialization(
        metadata={
            "row_count": {"raw_value": result["rows"], "type": "int"},
            "status": {"raw_value": "success", "type": "text"},
        },
        data_version="v1",
    )
```

## Kubernetes Pipes

```bash
pip install dagster-k8s
```

### Dagster asset

```python
from dagster_k8s import PipesK8sClient

@dg.asset
def k8s_asset(
    context: dg.AssetExecutionContext,
    k8s_pipes_client: PipesK8sClient,
) -> dg.MaterializeResult:
    return k8s_pipes_client.run(
        context=context,
        image="my-registry/my-script:v1",
        extras={"batch_size": 1000},
    ).get_materialize_result()

defs = dg.Definitions(
    assets=[k8s_asset],
    resources={"k8s_pipes_client": PipesK8sClient()},
)
```

### External script in container

```python
from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    batch_size = pipes.get_extra("batch_size")
    pipes.log.info(f"Processing batch of {batch_size}")
    pipes.report_asset_materialization(
        metadata={"processed": {"raw_value": batch_size, "type": "int"}},
    )
```

### Dockerfile

```dockerfile
FROM python:3.12-slim
RUN pip install dagster-pipes
COPY my_script.py .
ENTRYPOINT ["python", "my_script.py"]
```

## Databricks Pipes

```bash
pip install dagster-databricks
```

### Dagster asset

```python
import os
from dagster_databricks import PipesDatabricksClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

@dg.asset
def databricks_asset(
    context: dg.AssetExecutionContext,
    pipes_databricks: PipesDatabricksClient,
) -> dg.MaterializeResult:
    task = jobs.SubmitTask.from_dict({
        "new_cluster": {
            "spark_version": "12.2.x-scala2.12",
            "node_type_id": "i3.xlarge",
            "num_workers": 0,
        },
        "libraries": [{"pypi": {"package": "dagster-pipes"}}],
        "task_key": "etl-task",
        "spark_python_task": {
            "python_file": "dbfs:/scripts/my_etl.py",
            "source": jobs.Source.WORKSPACE,
        },
    })
    return pipes_databricks.run(
        task=task,
        context=context,
        extras={"date": "2024-01-15"},
    ).get_materialize_result()

defs = dg.Definitions(
    assets=[databricks_asset],
    resources={
        "pipes_databricks": PipesDatabricksClient(
            client=WorkspaceClient(
                host=os.environ["DATABRICKS_HOST"],
                token=os.environ["DATABRICKS_TOKEN"],
            )
        )
    },
)
```

### Databricks script

```python
from dagster_pipes import (
    PipesDbfsContextLoader,
    PipesDbfsMessageWriter,
    open_dagster_pipes,
)

with open_dagster_pipes(
    context_loader=PipesDbfsContextLoader(),
    message_writer=PipesDbfsMessageWriter(),
) as pipes:
    date = pipes.get_extra("date")
    pipes.log.info(f"Processing {date}")
    pipes.report_asset_materialization(
        metadata={"rows": {"raw_value": 50000, "type": "int"}},
    )
```

For serverless Databricks, use `PipesDatabricksServerlessClient` with Unity Catalog Volumes loaders/writers.

## Docker Pipes

```bash
pip install dagster-docker
```

```python
from dagster_docker import PipesDockerClient

@dg.asset
def docker_asset(
    context: dg.AssetExecutionContext,
    docker_pipes_client: PipesDockerClient,
) -> dg.MaterializeResult:
    return docker_pipes_client.run(
        image="python:3.12-slim",
        command=["python", "-m", "my_module"],
        context=context,
    ).get_materialize_result()

defs = dg.Definitions(
    assets=[docker_asset],
    resources={"docker_pipes_client": PipesDockerClient()},
)
```

## External Script API

The `dagster-pipes` package (installed in the external environment) provides:

```python
from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    # Logging
    pipes.log.info("message")
    pipes.log.warning("message")
    pipes.log.error("message")

    # Get extras passed from the Dagster asset
    value = pipes.get_extra("key")

    # Report asset materialization
    pipes.report_asset_materialization(
        metadata={"key": {"raw_value": 42, "type": "int"}},
        data_version="v1",
        asset_key="optional_asset_key",
    )

    # Report asset check result
    pipes.report_asset_check(
        check_name="row_count_check",
        passed=True,
        asset_key="my_asset",
        metadata={"row_count": {"raw_value": 100, "type": "int"}},
    )
```

Metadata types: `int`, `float`, `text`, `md` (markdown), `json`, `url`, `path`, `bool`, `timestamp`, `notebook`.

## Supported Environments

| Environment | Client | Package |
|------------|--------|---------|
| Subprocess | `PipesSubprocessClient` | `dagster` (built-in) |
| Kubernetes | `PipesK8sClient` | `dagster-k8s` |
| Docker | `PipesDockerClient` | `dagster-docker` |
| Databricks | `PipesDatabricksClient` | `dagster-databricks` |
| AWS Lambda | `PipesLambdaClient` | `dagster-aws` |
| Azure ML | `PipesAzureMLClient` | `dagster-azure` |
| GCP Dataproc | `PipesDataprocClient` | `dagster-gcp` |
| PySpark | Subprocess with Spark | `dagster-pipes` |
