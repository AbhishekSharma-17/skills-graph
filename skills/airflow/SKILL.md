---
name: airflow
description: "Apache Airflow — programmatic workflow orchestration platform for batch-oriented data pipelines. MANDATORY TRIGGERS: airflow, apache airflow, DAG, directed acyclic graph, airflow DAG, airflow operator, airflow sensor, TaskFlow API, airflow scheduler, airflow executor, data pipeline orchestration. Also trigger when the user wants to build ETL/ELT pipelines, schedule batch workflows, orchestrate data engineering tasks, or manage workflow dependencies. When in doubt about whether to use this skill for data pipeline orchestration tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["airflow", "data-engineering", "workflow-orchestration", "etl", "python", "scheduling", "pipelines"]
---

# Apache Airflow

> Source: [airflow.apache.org/docs](https://airflow.apache.org/docs/apache-airflow/stable/) · Tracks **v3.3.0** (July 2026)

## Reference Files

| # | File | Read When |
|---|------|-----------|
| 00 | [Overview](references/00-overview.md) | Starting with Airflow, understanding architecture, installation |
| 01 | [DAGs](references/01-dags.md) | Writing DAGs, dependencies, control flow, branching, trigger rules |
| 02 | [TaskFlow API](references/02-taskflow-api.md) | Using @task/@dag decorators, passing data, context access |
| 03 | [Operators & Sensors](references/03-operators-and-sensors.md) | BashOperator, PythonOperator, sensors, custom operators |
| 04 | [XComs & Variables](references/04-xcoms-and-variables.md) | Task communication, XCom backends, Variables, Params |
| 05 | [Connections & Hooks](references/05-connections-and-hooks.md) | External system credentials, hooks, secrets backends |
| 06 | [Scheduling](references/06-scheduling.md) | Cron, timetables, asset-aware scheduling, event-driven |
| 07 | [Dynamic Task Mapping](references/07-dynamic-task-mapping.md) | expand(), partial(), mapping task groups, zip, filtering |
| 08 | [Assets](references/08-assets.md) | Data-aware scheduling, @asset decorator, partitions, aliases |
| 09 | [Executors](references/09-executors.md) | Local, Celery, Kubernetes, multi-executor configuration |
| 10 | [Testing](references/10-testing.md) | DAG validation, unit tests, mocking, staging environments |
| 11 | [Deployment](references/11-deployment.md) | Docker Compose, Kubernetes Helm, CLI, production setup |
| 12 | [Best Practices](references/12-best-practices.md) | Idempotency, performance, anti-patterns, security |

## Installation

```bash
pip install apache-airflow==3.3.0
```

Docker quick-start:
```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.3.0/docker-compose.yaml'
docker compose up airflow-init && docker compose up
```

## Quick Reference

- [Official Docs](https://airflow.apache.org/docs/apache-airflow/stable/)
- [GitHub](https://github.com/apache/airflow)
- [PyPI](https://pypi.org/project/apache-airflow/)
- [Provider Packages](https://airflow.apache.org/docs/apache-airflow-providers/)
- [Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/index.html)
