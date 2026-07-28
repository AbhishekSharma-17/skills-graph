# Dynamic Task Mapping

> Source: [airflow.apache.org/docs/…/dynamic-task-mapping](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html) · v3.3.0

## Table of Contents

- [Overview](#overview)
- [expand() Basics](#expand-basics)
- [partial() for Fixed Arguments](#partial-for-fixed-arguments)
- [Task-Generated Mapping](#task-generated-mapping)
- [Cross Products](#cross-products)
- [expand_kwargs()](#expand_kwargs)
- [Mapping Task Groups](#mapping-task-groups)
- [Filtering and Transforming](#filtering-and-transforming)
- [Zipping and Concatenating](#zipping-and-concatenating)
- [Classic Operators](#classic-operators)
- [Limitations and Configuration](#limitations-and-configuration)

## Overview

Dynamic Task Mapping creates task instances at runtime based on current data, rather than requiring fixed task counts at parse time. This enables workflows like "process each file in a directory" without knowing how many files exist ahead of time.

```python
@task()
def get_files():
    return ["a.csv", "b.csv", "c.csv"]  # Runtime-determined list

@task()
def process(filename: str):
    print(f"Processing {filename}")

process.expand(filename=get_files())  # Creates 3 task instances
```

## expand() Basics

`expand()` maps a task over a list of values, creating one task instance per element:

```python
from airflow.sdk import dag, task

@dag(...)
def mapping_example():
    @task()
    def add_one(x: int):
        return x + 1

    @task()
    def sum_values(values):
        total = sum(values)
        print(f"Total: {total}")

    results = add_one.expand(x=[1, 2, 3])  # Creates 3 task instances
    sum_values(results)  # Receives [2, 3, 4]
```

Each mapped instance gets a `map_index` (0, 1, 2, ...) shown in the UI.

## partial() for Fixed Arguments

Use `partial()` to set arguments that remain constant across all mapped instances:

```python
@task()
def transform(data: str, format: str, verbose: bool):
    if verbose:
        print(f"Transforming {data} to {format}")
    return f"{data}.{format}"

# format and verbose are fixed; data varies
transform.partial(format="parquet", verbose=True).expand(
    data=["users", "orders", "events"]
)
```

`partial()` returns an intermediate object — call `expand()` on the result.

## Task-Generated Mapping

The list to map over can come from an upstream task:

```python
@task()
def list_files():
    import boto3
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket="data-lake", Prefix="incoming/")
    return [obj["Key"] for obj in response.get("Contents", [])]

@task()
def process_file(s3_key: str):
    print(f"Processing {s3_key}")
    return {"key": s3_key, "status": "done"}

files = list_files()
process_file.expand(s3_key=files)  # Dynamic count based on S3 contents
```

The actual list is resolved at runtime via XCom.

## Cross Products

Mapping over multiple parameters creates a cross product:

```python
@task()
def process(region: str, date: str):
    print(f"Processing {region} for {date}")

# Creates 6 instances: (us, 2024-01-01), (us, 2024-01-02), (us, 2024-01-03),
#                       (eu, 2024-01-01), (eu, 2024-01-02), (eu, 2024-01-03)
process.expand(
    region=["us", "eu"],
    date=["2024-01-01", "2024-01-02", "2024-01-03"],
)
```

## expand_kwargs()

Map multiple arguments simultaneously using dictionaries (no cross product):

```python
from airflow.providers.standard.operators.bash import BashOperator

BashOperator.partial(task_id="run_scripts").expand_kwargs(
    [
        {"bash_command": "python etl.py --region us", "env": {"REGION": "us"}},
        {"bash_command": "python etl.py --region eu", "env": {"REGION": "eu"}},
        {"bash_command": "python etl.py --region apac", "env": {"REGION": "apac"}},
    ]
)
```

Use `expand_kwargs()` when each mapped instance needs a different combination of parameters.

### From Upstream Tasks

```python
@task()
def generate_configs():
    return [
        {"region": "us", "batch_size": 1000},
        {"region": "eu", "batch_size": 500},
    ]

@task()
def run_pipeline(region: str, batch_size: int):
    print(f"Running {region} with batch {batch_size}")

run_pipeline.expand_kwargs(generate_configs())
```

## Mapping Task Groups

Expand an entire group of tasks over a list:

```python
from airflow.sdk import task_group, task

@task_group()
def process_partition(partition: str):
    @task()
    def validate(p: str):
        return f"validated {p}"

    @task()
    def transform(p: str):
        return f"transformed {p}"

    @task()
    def load(p: str):
        return f"loaded {p}"

    v = validate(p=partition)
    t = transform(p=partition)
    l = load(p=partition)
    v >> t >> l

# Each partition gets its own validate → transform → load chain
process_partition.expand(partition=["2024-01", "2024-02", "2024-03"])
```

**Limitation:** Nested mapping inside a mapped task group is not permitted.

## Filtering and Transforming

### Return None to Skip

```python
@task()
def maybe_process(filename: str):
    if not filename.endswith((".csv", ".json")):
        return None  # Skipped in downstream aggregation
    return {"file": filename, "rows": process(filename)}
```

### map() for Pre-Processing

Apply a plain Python function (not a task) to transform values before expansion:

```python
def to_s3_path(filename: str):
    if filename.startswith("_"):
        raise AirflowSkipException(f"Skipping {filename}")
    return f"s3://data-lake/incoming/{filename}"

@task()
def list_files():
    return ["data.csv", "_metadata.json", "events.parquet"]

@task()
def download(path: str):
    print(f"Downloading {path}")

files = list_files()
s3_paths = files.output.map(to_s3_path)
download.expand(path=s3_paths)
```

The `map()` callable must accept exactly one positional argument and must not be a task decorator.

## Zipping and Concatenating

### zip() — Combine Parallel Lists

```python
@task()
def get_sources():
    return ["raw/a.csv", "raw/b.csv"]

@task()
def get_destinations():
    return ["clean/a.parquet", "clean/b.parquet"]

@task()
def copy_file(pair):
    src, dst = pair
    print(f"Copying {src} → {dst}")

sources = get_sources()
destinations = get_destinations()
zipped = sources.output.zip(destinations)
copy_file.expand(pair=zipped)
```

Pass a `default` value to switch to `zip_longest` behavior for unequal-length lists.

### concat() — Merge Multiple Lists

```python
@task()
def us_files():
    return ["us/data1.csv", "us/data2.csv"]

@task()
def eu_files():
    return ["eu/data1.csv"]

@task()
def process(filename: str):
    print(f"Processing {filename}")

all_files = us_files().output.concat(eu_files())
process.expand(filename=all_files)  # 3 instances total
```

## Classic Operators

Non-TaskFlow operators use the same `partial()` and `expand()` pattern:

```python
from airflow.providers.standard.operators.bash import BashOperator

BashOperator.partial(
    task_id="process_region",
    env={"COMMON_VAR": "shared_value"},
).expand(
    bash_command=[
        "python process.py --region us",
        "python process.py --region eu",
        "python process.py --region apac",
    ]
)
```

Reference upstream outputs via `.output`:

```python
from airflow.providers.standard.operators.bash import BashOperator

list_task = BashOperator(task_id="list", bash_command="echo '[1,2,3]'")

@task()
def process(value):
    print(value)

process.expand(value=list_task.output)
```

## Limitations and Configuration

### Max Map Length

Default limit: 1024 task instances per expansion. Exceeding this fails the source task.

```ini
[core]
max_map_length = 2048  # Increase if needed
```

### Concurrency Control

```python
@task(max_active_tis_per_dag=16)  # Max 16 concurrent instances across all runs
def process_file(path: str):
    return transform(path)
```

### Zero-Length Maps

Empty input lists automatically skip the mapped task:

```python
@task()
def get_items():
    return []  # Empty list

@task()
def process(item):
    ...

process.expand(item=get_items())  # Task marked as SKIPPED
```

### Templating Interaction

Mapped arguments bypass Jinja templating. If you need templating in mapped parameters, pre-render them:

```python
# This does NOT template the bash_command
BashOperator.partial(task_id="run").expand(
    bash_command=["echo {{ ds }}"]  # Literal string, not templated
)

# Instead, use expand_kwargs with pre-rendered values
@task()
def make_commands(ds=None):
    return [{"bash_command": f"echo {ds}"}]

BashOperator.partial(task_id="run").expand_kwargs(make_commands())
```

### Named Map Indices

Override integer indices with meaningful names:

```python
SQLExecuteQueryOperator.partial(
    task_id="query",
    sql="SELECT * FROM data WHERE date = %(date)s",
    map_index_template="{{ task.parameters['date'] }}",
).expand(
    parameters=[{"date": "2024-01-01"}, {"date": "2024-01-02"}],
)
```

### Lazy Proxy Objects

Mapped task outputs are lazy — they don't materialize until consumed:

```python
results = add_one.expand(x=[1, 2, 3])
# results is a LazySelectSequence, not a Python list
# Calling list(results) materializes but may degrade performance with large maps
```

## Related Topics

- [TaskFlow API](02-taskflow-api.md) — @task decorator basics
- [Operators & Sensors](03-operators-and-sensors.md) — Classic operator patterns
- [Best Practices](12-best-practices.md) — Performance with dynamic mapping
