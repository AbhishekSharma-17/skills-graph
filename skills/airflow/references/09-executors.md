# Executors

> Source: [airflow.apache.org/docs/…/executor](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html) · v3.3.0

## Overview

Executors determine how task instances are run. They are the bridge between the scheduler (which decides *when* tasks run) and the actual execution environment (which runs the task code).

## Executor Types

### Local Executors

Tasks execute within the scheduler process or as local subprocesses.

```ini
[core]
executor = LocalExecutor
```

| Executor | Parallelism | Use When |
|----------|-------------|----------|
| `SequentialExecutor` | 1 task at a time | Development/testing only |
| `LocalExecutor` | Multiple tasks via subprocesses | Small deployments, single machine |

**LocalExecutor** spawns a new process for each task. It works well for small to medium workloads on a single machine with no need for distributed execution.

### CeleryExecutor

Distributes tasks across multiple worker machines via a message broker (Redis or RabbitMQ):

```ini
[core]
executor = CeleryExecutor

[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:airflow@postgres/airflow
worker_concurrency = 16
```

```bash
# Start workers
airflow celery worker --queues default,heavy_tasks
airflow celery flower  # Monitoring dashboard on port 5555
```

**Pros:** Horizontal scaling, queue-based routing, mature ecosystem
**Cons:** Requires broker infrastructure, noisy neighbor problem (resource contention)

### KubernetesExecutor

Each task runs in its own Kubernetes pod:

```ini
[core]
executor = KubernetesExecutor

[kubernetes_executor]
namespace = airflow
worker_container_repository = apache/airflow
worker_container_tag = 3.3.0
delete_worker_pods = True
delete_worker_pods_on_failure = False
```

**Pros:** Complete task isolation, per-task resource requests, auto-scaling, custom images per task
**Cons:** Pod startup latency (5-30s), overhead for short tasks, requires Kubernetes cluster

#### Per-Task Pod Configuration

```python
from kubernetes.client import models as k8s

@task(
    executor_config={
        "pod_override": k8s.V1Pod(
            spec=k8s.V1PodSpec(
                containers=[
                    k8s.V1Container(
                        name="base",
                        resources=k8s.V1ResourceRequirements(
                            requests={"cpu": "2", "memory": "4Gi"},
                            limits={"cpu": "4", "memory": "8Gi", "nvidia.com/gpu": "1"},
                        ),
                        image="my-ml-image:latest",
                    )
                ],
                node_selector={"gpu": "true"},
                tolerations=[
                    k8s.V1Toleration(key="gpu", operator="Equal", value="true", effect="NoSchedule")
                ],
            )
        )
    }
)
def gpu_training():
    import torch
    return train_model()
```

### Cloud-Managed Executors

| Executor | Platform | Task Runs In |
|----------|----------|-------------|
| `EcsExecutor` | AWS | ECS Fargate/EC2 tasks |
| `BatchExecutor` | AWS | AWS Batch jobs |
| `EdgeExecutor` | Any | Edge nodes near data sources |

```ini
[core]
executor = airflow.providers.amazon.aws.executors.ecs.ecs_executor.AwsEcsExecutor

[aws_ecs_executor]
cluster = airflow-cluster
region = us-east-1
container_name = airflow-worker
launch_type = FARGATE
```

## Choosing an Executor

| Scenario | Recommended Executor |
|----------|---------------------|
| Local development / testing | `LocalExecutor` |
| Small team, single server (<50 DAGs) | `LocalExecutor` |
| Medium team, multiple workers | `CeleryExecutor` |
| Heavy isolation needs, varied dependencies | `KubernetesExecutor` |
| GPU/ML workloads | `KubernetesExecutor` |
| AWS-native, serverless | `EcsExecutor` |
| Edge computing, IoT data | `EdgeExecutor` |
| Mixed workloads | Multi-executor |

## Multiple Executors

Run different executors concurrently (Airflow 2.10+):

```ini
[core]
executor = local:LocalExecutor,celery:CeleryExecutor,k8s:KubernetesExecutor
```

### Assigning Tasks to Executors

```python
# Task-level
@task(executor="k8s")
def heavy_processing():
    return process_large_dataset()

@task(executor="local")
def quick_check():
    return "ok"

# DAG-level default
@dag(default_args={"executor": "celery"}, ...)
def distributed_pipeline():
    @task(executor="k8s")  # Override for this task
    def gpu_task():
        return train()

    @task()  # Inherits celery from default_args
    def regular_task():
        return process()
```

### With Aliases

```ini
[core]
executor = fast:LocalExecutor,distributed:CeleryExecutor,isolated:KubernetesExecutor
```

```python
@task(executor="fast")        # Quick, low-latency tasks
def validate(): ...

@task(executor="distributed") # Standard parallel tasks
def process(): ...

@task(executor="isolated")    # Custom dependencies, GPU
def ml_train(): ...
```

The first executor in the list is the default when no executor is specified on a task.

## Executor Configuration

### Parallelism

```ini
[core]
# Maximum task instances running across all DAGs
parallelism = 32

# Max active task instances per DAG
max_active_tasks_per_dag = 16

# Max active DAG runs per DAG
max_active_runs_per_dag = 16
```

### Celery-Specific

```ini
[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:airflow@postgres/airflow
worker_concurrency = 16
worker_prefetch_multiplier = 1
worker_autoscale = 16,4  # max,min workers

# Task routing
task_default_queue = default
task_routes = {
    "my_dag.heavy_task": {"queue": "heavy"},
    "my_dag.gpu_task": {"queue": "gpu"},
}
```

### Kubernetes-Specific

```ini
[kubernetes_executor]
namespace = airflow
worker_container_repository = apache/airflow
worker_container_tag = 3.3.0
delete_worker_pods = True
delete_worker_pods_on_failure = False
in_cluster = True
kube_client_request_args = {"_request_timeout": [60, 60]}

# Pod template file for advanced configuration
pod_template_file = /opt/airflow/pod_template.yaml
```

### Queue Routing with Celery

```python
@task(queue="heavy_compute")
def resource_intensive():
    return process()

@task(queue="default")
def lightweight():
    return check()
```

Start workers listening to specific queues:

```bash
airflow celery worker --queues default
airflow celery worker --queues heavy_compute --concurrency 4
airflow celery worker --queues gpu --concurrency 1
```

## Monitoring Executors

```bash
# Check current executor
airflow config get-value core executor

# Celery monitoring
airflow celery flower  # Web UI on port 5555

# Kubernetes monitoring
kubectl get pods -n airflow -l component=worker
kubectl logs -n airflow <pod-name>
```

## Related Topics

- [Deployment](11-deployment.md) — Production setup with Docker and Kubernetes
- [Overview](00-overview.md) — Architecture components
- [Best Practices](12-best-practices.md) — Performance tuning
