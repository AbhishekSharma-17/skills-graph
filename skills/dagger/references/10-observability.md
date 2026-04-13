# Dagger Observability

> Source: https://docs.dagger.io/features/observability | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Terminal UI (TUI)](#terminal-ui-tui)
- [Dagger Cloud Traces](#dagger-cloud-traces)
- [OpenTelemetry Integration](#opentelemetry-integration)
- [Progress Frontend](#progress-frontend)
- [Debugging Techniques](#debugging-techniques)
- [Performance Analysis](#performance-analysis)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger provides built-in observability for all pipeline executions through:

1. **Terminal UI (TUI)**: Real-time visualization in the terminal
2. **Dagger Cloud**: Browser-based trace visualization and analytics
3. **OpenTelemetry**: Standard telemetry export for custom backends
4. **Log streaming**: Structured output from pipeline steps

Every `dagger call` execution automatically collects telemetry data.

## Terminal UI (TUI)

The default output mode shows a real-time tree of operations:

```bash
$ dagger call build --source=.
┃ build
┃ ┣ container.from python:3.12
┃ ┣ container.withDirectory /app
┃ ┣ container.withExec pip install -r requirements.txt
┃ ┗ container.withExec python -m build
```

### TUI Features
- Real-time progress for each operation
- Expandable tree view showing nested operations
- Duration and status for each step
- Automatic error highlighting

### Verbose Mode

```bash
# Show all operations including cached ones
dagger call --debug build --source=.

# Focus output (logs-only, no TUI)
dagger call --progress=plain build --source=.
```

### Progress Modes

```bash
# Interactive TUI (default in TTY)
dagger call --progress=auto build --source=.

# Plain text logs (default in CI)
dagger call --progress=plain build --source=.

# Logs-focused (v0.20+): streams output directly
dagger call --progress=plain build --source=.
```

## Dagger Cloud Traces

### Setup

```bash
# Set your Dagger Cloud token
export DAGGER_CLOUD_TOKEN=your-token

# Every execution now generates a trace URL
dagger call build --source=.
# Output includes: https://dagger.cloud/trace/abc123
```

### Trace Features
- **Waterfall view**: Visualize operation timing and parallelism
- **Step details**: Inspect inputs, outputs, and duration for each operation
- **Log streaming**: View stdout/stderr from any container execution
- **Cache hits**: See which operations were cached vs executed
- **Error drilldown**: Click into failed steps for full error context

### Organization-Wide Analytics
- Pipeline success/failure rates
- Average execution times
- Cache hit ratios
- Module usage across projects
- Team performance dashboards

## OpenTelemetry Integration

Dagger natively exports telemetry in OpenTelemetry format, allowing integration with any OTLP-compatible backend.

### Exporting to Custom Backends

```bash
# Export to Jaeger
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Export to Grafana Tempo
export OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317

# Export to Honeycomb
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=your-api-key"
```

### Trace Structure

Dagger creates spans for:
- Module function calls
- Container operations (from, withExec, etc.)
- File and directory operations
- Service lifecycle events
- Cache hit/miss decisions

### Custom Span Attributes

Traces include:
- `dagger.function`: Function name being executed
- `dagger.module`: Module containing the function
- `dagger.operation`: API operation type
- `dagger.cached`: Whether the result was cached

## Progress Frontend

### v0.20+ Logs-Focused Mode

The v0.20 release introduced a logs-focused progress frontend that streams output directly with no dot noise:

```bash
# Automatically used in CI environments
$ dagger call test --source=.
[test] Running pytest -v...
[test] tests/test_api.py::test_health_check PASSED
[test] tests/test_api.py::test_create_user PASSED
[test] 2 passed in 1.23s
```

This is designed for terminal-first workflows and CI logs where the interactive TUI isn't appropriate.

## Debugging Techniques

### Interactive Terminal

```bash
# Drop into a container at any pipeline stage
dagger shell
> container | from python:3.12 | with-directory /app . | terminal
```

### Inspecting Intermediate State

```bash
# Check container filesystem at a specific step
dagger call build --source=. directory /app entries
```

### Debug Flag

```bash
# Enable verbose logging
dagger call --debug build --source=.
```

### Trace Analysis

When a pipeline fails:
1. Check the trace URL in the output
2. Open in Dagger Cloud or view locally
3. Find the failed step in the waterfall
4. Inspect the step's logs and inputs
5. Use `terminal` to drop into the failed container state

### Common Debug Workflow

```python
@dagger.function
async def debug_build(self, source: dagger.Directory) -> str:
    """Build with debug output."""
    ctr = (
        dag.container()
        .from_("python:3.12")
        .with_directory("/app", source)
        .with_workdir("/app")
    )

    # Check what files are present
    files = await ctr.with_exec(["ls", "-la"]).stdout()
    print(f"Files: {files}")

    # Check Python version
    version = await ctr.with_exec(["python", "--version"]).stdout()
    print(f"Python: {version}")

    # Run the actual build
    return await ctr.with_exec(["pip", "install", "."]).stdout()
```

## Performance Analysis

### Identifying Bottlenecks

Use Dagger Cloud trace waterfall to:
1. Find the longest-running operations
2. Check cache hit ratios
3. Identify sequential operations that could be parallelized
4. Spot unnecessary operations

### Cache Analysis

```bash
# Check what's being cached vs re-executed
dagger call --debug build --source=. 2>&1 | grep -i cache
```

### Timing Functions

```python
import time

@dagger.function
async def build(self, source: dagger.Directory) -> str:
    start = time.time()
    result = await self._build_impl(source)
    duration = time.time() - start
    return f"Build completed in {duration:.1f}s: {result}"
```

## Common Pitfalls

1. **Missing DAGGER_CLOUD_TOKEN**: Traces won't be uploaded without the token
2. **TUI in CI**: The interactive TUI doesn't work in non-TTY environments — use `--progress=plain`
3. **OTLP endpoint format**: Use the gRPC endpoint (port 4317), not HTTP (port 4318)
4. **Trace volume**: High-frequency pipelines can generate large volumes of trace data
5. **Local debugging**: Use `dagger shell` with `terminal` for interactive debugging, not print statements
