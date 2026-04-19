# Dagster — Ops, Jobs & Graphs

> Source: [docs.dagster.io/concepts/ops-jobs-graphs](https://docs.dagster.io/concepts/ops-jobs-graphs/ops)

## Table of Contents

- [The @op Decorator](#the-op-decorator)
- [Op Inputs and Outputs](#op-inputs-and-outputs)
- [RetryPolicy](#retrypolicy)
- [The @graph Decorator](#the-graph-decorator)
- [The @job Decorator](#the-job-decorator)
- [Graph-Backed Assets](#graph-backed-assets)
- [Config for Ops](#config-for-ops)
- [Nothing Type](#nothing-type)
- [Patterns and Best Practices](#patterns-and-best-practices)

---

## The @op Decorator

Ops are the core unit of computation. Assets use ops internally, but ops can also be composed directly for task-centric workflows.

```python
import dagster as dg

@dg.op
def return_five() -> int:
    return 5

@dg.op
def add_one(number: int) -> int:
    return number + 1

@dg.op
def context_op(context: dg.OpExecutionContext):
    context.log.info(f"Run ID: {context.run_id}")
```

Key parameters: `name`, `description`, `ins` (dict of `In`), `out` (dict of `Out`), `config_schema`, `retry_policy`, `tags`, `code_version`, `required_resource_keys`.

## Op Inputs and Outputs

### Typed inputs

```python
@dg.op(ins={"num": dg.In(dagster_type=int)})
def process_number(num: int) -> int:
    return num * 2
```

### Multiple outputs

```python
@dg.op(out={"first": dg.Out(), "second": dg.Out()})
def split_data():
    return 5, 6
```

### Conditional/branching outputs

```python
@dg.op(
    out={
        "branch_a": dg.Out(is_required=False),
        "branch_b": dg.Out(is_required=False),
    }
)
def branching_op():
    import random
    if random.randint(0, 1) == 0:
        yield dg.Output(1, "branch_a")
    else:
        yield dg.Output(2, "branch_b")
```

## RetryPolicy

```python
@dg.op(
    retry_policy=dg.RetryPolicy(
        max_retries=5,
        delay=0.2,                      # seconds between retries
        backoff=dg.Backoff.EXPONENTIAL,  # LINEAR or EXPONENTIAL
        jitter=dg.Jitter.PLUS_MINUS,    # FULL or PLUS_MINUS
    )
)
def flaky_api_call() -> dict:
    return requests.get("https://api.example.com/data").json()
```

Backoff formulas:
- `LINEAR`: `attempt_num * delay`
- `EXPONENTIAL`: `((2 ^ attempt_num) - 1) * delay`

Jitter:
- `FULL`: random in `[0, calculated_delay]`
- `PLUS_MINUS`: `calculated_delay ± delay`

## The @graph Decorator

Graphs compose ops into a DAG without execution semantics:

```python
@dg.graph
def my_pipeline():
    add_one(add_one(return_five()))
```

### Aliased ops (reusing the same op)

```python
@dg.graph
def chained():
    add_one.alias("second_add")(add_one(return_five()))
```

### Fan-out / fan-in

```python
@dg.op
def sum_values(values: list[int]) -> int:
    return sum(values)

@dg.graph
def fan_in_graph():
    results = []
    for i in range(10):
        results.append(return_five.alias(f"source_{i}")())
    sum_values(results)
```

### Convert graph to job

```python
prod_job = my_pipeline.to_job(
    name="prod_pipeline",
    resource_defs={"db": prod_database},
)

test_job = my_pipeline.to_job(
    name="test_pipeline",
    resource_defs={"db": test_database},
)
```

## The @job Decorator

Jobs are the main unit of execution and monitoring:

```python
@dg.job
def my_job():
    add_one(return_five())

# With default config
class DoSomethingConfig(dg.Config):
    param: str

@dg.op
def do_something(config: DoSomethingConfig):
    pass

@dg.job(config=dg.RunConfig(ops={"do_something": DoSomethingConfig(param="value")}))
def configured_job():
    do_something()
```

Key parameters: `name`, `resource_defs`, `config`, `tags`, `executor_def`, `op_retry_policy`, `partitions_def`.

### Execute in process (testing)

```python
result = my_job.execute_in_process()
assert result.success

result = my_job.execute_in_process(
    run_config={"ops": {"do_something": {"config": {"param": "test"}}}},
)
```

## Graph-Backed Assets

Bridge ops/graphs with the asset system:

```python
@dg.op(retry_policy=dg.RetryPolicy(max_retries=3))
def step_one() -> int:
    return fetch_from_api()

@dg.op
def step_two(num: int) -> int:
    return num ** 2

@dg.graph_asset
def processed_data():
    return step_two(step_one())
```

### @graph_multi_asset

```python
@dg.op(out={"raw": dg.Out(), "metadata": dg.Out()})
def extract():
    return [1, 2, 3], {"count": 3}

@dg.op
def transform(raw: list) -> list:
    return [x * 2 for x in raw]

@dg.graph_multi_asset(
    outs={"transformed": dg.AssetOut(), "metadata": dg.AssetOut()},
)
def etl_graph():
    raw, meta = extract()
    return {"transformed": transform(raw), "metadata": meta}
```

## Config for Ops

```python
class MyOpConfig(dg.Config):
    api_endpoint: str
    max_retries: int = 3

@dg.op
def configurable_op(config: MyOpConfig) -> dict:
    return requests.get(config.api_endpoint).json()
```

### ConfigMapping (simplified outer config)

```python
class EnvConfig(dg.Config):
    env: str

@dg.config_mapping
def env_config(val: EnvConfig) -> dg.RunConfig:
    if val.env == "prod":
        return dg.RunConfig(ops={"my_op": MyOpConfig(api_endpoint="https://prod.api.com")})
    return dg.RunConfig(ops={"my_op": MyOpConfig(api_endpoint="https://staging.api.com")})

@dg.job(config=env_config)
def mapped_job():
    configurable_op()
```

## Nothing Type

For ordering-only dependencies (no data communicated):

```python
@dg.op
def create_table_1():
    pass

@dg.op(ins={"start": dg.In(dg.Nothing)})
def create_table_2():
    pass

@dg.graph
def ordered_tables():
    create_table_2(start=create_table_1())
```

## Patterns and Best Practices

**Prefer assets over ops** for new pipelines — assets provide lineage, metadata, and automation out of the box.

**Use `@graph_asset`** when you need per-step retry policies or multi-step computation for a single asset.

**Graph composition functions are a DSL** — function calls define dependencies, they don't execute ops immediately.

**Aliasing is required** when reusing the same op multiple times in a graph.

**Set `is_required=False`** on `Out` for conditional/branching outputs — forgetting this causes runtime errors.

**Use `Nothing` type** for ordering-only dependencies instead of passing dummy values.
