# Dagster — AI/ML Pipelines

> Source: [docs.dagster.io/guides/build/ml-pipelines](https://docs.dagster.io/guides/build/ml-pipelines)

## Table of Contents

- [Overview](#overview)
- [OpenAI Integration](#openai-integration)
- [LLM Fine-Tuning Pipeline](#llm-fine-tuning-pipeline)
- [ML Training Pipeline Pattern](#ml-training-pipeline-pattern)
- [AI/ML Architecture Patterns](#aiml-architecture-patterns)
- [Best Practices](#best-practices)

---

## Overview

Dagster's asset-centric model maps naturally to ML workflows where each artifact (dataset, features, model, predictions) is a software-defined asset with lineage tracking. Key advantages:
- **Asset lineage** — trace from raw data through features to model to predictions
- **Partitioning** — process training data in time-based or categorical partitions
- **Configurable resources** — swap dev/prod model configs without code changes
- **Sensors** — trigger retraining when data arrives or model performance degrades
- **Observability** — automatic usage metadata logging for AI providers

## OpenAI Integration

```bash
pip install dagster-openai
```

### Basic chat completion

```python
from dagster import AssetExecutionContext, asset, Definitions, EnvVar
from dagster_openai import OpenAIResource

@asset(compute_kind="OpenAI")
def openai_completion(context: AssetExecutionContext, openai: OpenAIResource):
    with openai.get_client(context) as client:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Summarize recent trends"}],
        )
    return response.choices[0].message.content

defs = Definitions(
    assets=[openai_completion],
    resources={"openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY"))},
)
```

When used with `get_client(context)`, usage metadata (tokens, cost) is automatically logged as asset metadata and visible in the UI Events tab.

### Batch text processing

```python
@asset(compute_kind="OpenAI")
def classified_tickets(
    context: AssetExecutionContext,
    openai: OpenAIResource,
    raw_tickets: list[dict],
) -> list[dict]:
    with openai.get_client(context) as client:
        results = []
        for ticket in raw_tickets:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Classify: bug, feature, question"},
                    {"role": "user", "content": ticket["text"]},
                ],
            )
            results.append({
                **ticket,
                "category": response.choices[0].message.content,
            })
    return results
```

## LLM Fine-Tuning Pipeline

Full pipeline from data ingestion to fine-tuned model:

### File upload asset

```python
import dagster as dg
from dagster_openai import OpenAIResource

@dg.asset(kinds={"openai"}, group_name="fine_tuning")
def upload_training_file(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    training_file: str,
) -> str:
    with openai.get_client(context) as client:
        with open(training_file, "rb") as f:
            response = client.files.create(file=f, purpose="fine-tune")
    return response.id
```

### Fine-tuning job asset

```python
import time

@dg.asset(kinds={"openai"}, group_name="fine_tuning")
def fine_tuned_model(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    upload_training_file: str,
    upload_validation_file: str,
) -> str:
    with openai.get_client(context) as client:
        job = client.fine_tuning.jobs.create(
            training_file=upload_training_file,
            validation_file=upload_validation_file,
            model="gpt-4o-mini",
            suffix="my-model",
        )
        job_id = job.id

        while True:
            status = client.fine_tuning.jobs.retrieve(job_id)
            if status.status in ["succeeded", "cancelled", "failed"]:
                break
            time.sleep(30)

        model_name = status.fine_tuned_model
        context.add_output_metadata({"model_name": model_name})
        return model_name
```

### Pipeline structure

```
[Raw Data] → [DuckDB Ingestion] → [Feature Engineering]
    → [Training/Validation Split] → [File Upload]
    → [OpenAI Fine-Tuning Job] → [Model Validation]
```

## ML Training Pipeline Pattern

### Configurable training asset

```python
class TrainingConfig(dg.Config):
    learning_rate: float = 0.001
    epochs: int = 10
    batch_size: int = 32

@dg.asset(group_name="ml", kinds={"python", "pytorch"})
def trained_model(
    context: dg.AssetExecutionContext,
    config: TrainingConfig,
    training_data: pd.DataFrame,
) -> dg.MaterializeResult:
    model = build_model()
    history = train(
        model,
        training_data,
        lr=config.learning_rate,
        epochs=config.epochs,
        batch_size=config.batch_size,
    )
    save_model(model, "models/latest.pt")

    return dg.MaterializeResult(
        metadata={
            "loss": history["loss"][-1],
            "accuracy": history["accuracy"][-1],
            "epochs": config.epochs,
        }
    )
```

### Evaluation asset with quality gate

```python
@dg.asset(group_name="ml")
def model_evaluation(
    context: dg.AssetExecutionContext,
    trained_model: dg.MaterializeResult,
    test_data: pd.DataFrame,
) -> dg.MaterializeResult:
    model = load_model("models/latest.pt")
    metrics = evaluate(model, test_data)

    passed = metrics["accuracy"] > 0.95
    context.log.info(f"Accuracy: {metrics['accuracy']:.4f} — {'PASS' if passed else 'FAIL'}")

    return dg.MaterializeResult(
        metadata={
            "accuracy": metrics["accuracy"],
            "f1_score": metrics["f1"],
            "passed_threshold": passed,
        }
    )
```

### Sensor for retraining

```python
@dg.sensor(job=training_job, minimum_interval_seconds=3600)
def drift_sensor(context: dg.SensorEvaluationContext):
    drift_score = check_model_drift()
    if drift_score > 0.1:
        return dg.RunRequest(
            run_key=f"retrain-{drift_score:.3f}",
            tags={"reason": "drift_detected", "drift_score": str(drift_score)},
        )
    return dg.SkipReason(f"No drift detected (score: {drift_score:.3f})")
```

## AI/ML Architecture Patterns

```
[Raw Data Sources]
       ↓
[Data Ingestion Assets]     (Airbyte, Fivetran, S3, APIs)
       ↓
[Feature Engineering]       (Pandas, Polars, DuckDB, dbt)
       ↓
[Training Assets]           (PyTorch, TensorFlow, scikit-learn, OpenAI)
       ↓
[Evaluation Assets]         (metrics, A/B tests, quality gates)
       ↓
[Deployment Assets]         (model registry, serving endpoint)
       ↓
[Inference Assets]          (batch scoring, real-time API)
       ↓
[Monitoring Assets]         (drift detection, performance tracking)
```

### Environment-specific configs

```python
# Development — fast iteration
dev_defs = dg.Definitions(
    assets=[training_data, trained_model, evaluation],
    resources={
        "io_manager": DuckDBPandasIOManager(database="dev.duckdb"),
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
    },
)

# Production — full pipeline with quality gates
prod_defs = dg.Definitions(
    assets=[training_data, trained_model, evaluation, deployment],
    resources={
        "io_manager": SnowflakePandasIOManager(
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            database="ML_PROD",
        ),
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
    },
)
```

## Best Practices

- **Model each ML artifact as an asset** — datasets, features, models, predictions all get lineage tracking.
- **Use partitioned assets** for time-windowed training data — enables incremental retraining.
- **Use sensors** to trigger retraining on data drift, schedule degradation, or new data arrival.
- **Use `code_version`** on model assets to track which code version produced each model.
- **Use config classes** for hyperparameters — enables experiment tracking and comparison in the UI.
- **Use `get_client(context)`** with OpenAI to get automatic token/cost tracking in asset metadata.
- **Separate dev/prod via resources** — same asset code, different I/O managers and model configs.
- **Use asset checks** for data quality gates before training (no nulls, feature distributions).
