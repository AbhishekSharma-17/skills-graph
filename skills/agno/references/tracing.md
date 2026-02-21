# Tracing

OpenTelemetry-based observability for Agno agents, teams, and workflows.

## Docs Hierarchy

```
Tracing
├── Overview                        ← this router
├── Basic Setup                     → setup.md
├── DB Functions (Accessing Traces) → querying.md
├── Usage
│   ├── Basic Agent Tracing         → setup.md
│   ├── Basic Team Tracing          → setup.md
│   └── Basic Workflow Tracing      → setup.md
└── AgentOS Tracing                 → setup.md (AgentOS section)
```

## Why Tracing?

- **Debugging** — see exactly what went wrong when an agent fails
- **Performance** — identify bottlenecks in agent execution
- **Cost tracking** — monitor token usage and API calls
- **Behavior analysis** — understand decision-making patterns
- **Audit trail** — track what agents did and why

All tracing data is stored in **your own database**. No data leaves your system.

## Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | One complete agent execution (start to finish). Has unique `trace_id`. |
| **Span** | Single operation within a trace (parent-child hierarchy). |

### What Gets Traced Automatically

| Operation | What Gets Traced |
|-----------|-----------------|
| Agent Runs | Every `agent.run()` / `agent.arun()` with full context |
| Model Calls | LLM interactions — prompts, responses, token usage |
| Tool Executions | Tool invocations with arguments and results |
| Team Operations | Team coordination and member agent runs |
| Workflow Operations | Workflow coordination and step runs |

## Sub-References

| File | Read When |
|------|-----------|
| `tracing/setup.md` | Installing, enabling tracing (SDK + AgentOS), processing modes, agent/team/workflow examples |
| `tracing/querying.md` | DB functions — get_trace, get_traces, get_span, get_spans, filtering, pagination, analyzing runs |

## setup_tracing() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `BaseDb` | Required | Database for storing traces |
| `batch_processing` | `bool` | `False` | Enable batch processing mode (recommended for production) |
| `max_queue_size` | `int` | `2048` | Max traces in memory before dropping (batch mode only) |
| `max_export_batch_size` | `int` | `512` | Traces per batch write (batch mode only) |
| `schedule_delay_millis` | `int` | `5000` | Export interval in milliseconds (batch mode only) |

## Quick Start

```python
from agno.tracing import setup_tracing
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/traces.db")
setup_tracing(db=db)  # Call once at startup

# Agents are automatically traced after this!
```

## Install

```bash
uv pip install -U opentelemetry-api opentelemetry-sdk openinference-instrumentation-agno
```

## Key Features

- **Zero-code instrumentation** — no need to modify agent code
- **Database storage** — traces stored in your Agno database (SQLite, PostgreSQL, etc.)
- **OpenTelemetry standard** — export to Arize Phoenix, Langfuse, etc.
- **Non-blocking** — tracing never slows down your agents
- **Configurable** — adjust batch sizes and processing

## Key Imports

```python
from agno.tracing import setup_tracing
from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb
```
