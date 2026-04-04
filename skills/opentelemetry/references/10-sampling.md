# OpenTelemetry — Sampling

> Source: [opentelemetry.io/docs/concepts/sampling](https://opentelemetry.io/docs/concepts/sampling/)

## Table of Contents

- [Why Sampling](#why-sampling)
- [Head Sampling vs Tail Sampling](#head-sampling-vs-tail-sampling)
- [SDK Samplers](#sdk-samplers)
- [Configuring Samplers in Python](#configuring-samplers-in-python)
- [Configuring Samplers in Node.js](#configuring-samplers-in-nodejs)
- [Collector-Based Sampling](#collector-based-sampling)
- [Tail Sampling in the Collector](#tail-sampling-in-the-collector)
- [Sampling Strategies](#sampling-strategies)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## Why Sampling

At scale, exporting every trace is expensive and often unnecessary. A service handling 10,000 requests/second generates millions of spans per minute. Sampling reduces this volume while preserving observability.

**Trade-offs:**

| Full Export | Sampled |
|------------|---------|
| 100% visibility | Statistical visibility |
| High storage cost | Reduced cost |
| High network overhead | Lower overhead |
| Complete debugging data | May miss rare events |

**When to sample:**

- Production services with >100 requests/second
- When storage costs are a concern
- When network bandwidth to the collector is limited

**When NOT to sample:**

- Development and staging environments
- Low-traffic services (<100 req/s)
- When you need 100% error visibility (use tail sampling instead)

## Head Sampling vs Tail Sampling

### Head Sampling

Decision made at the **start** of the trace, before any spans are processed:

```
Request arrives → Sample? (coin flip) → Yes: trace all spans
                                      → No: drop all spans
```

**Pros:** Simple, low overhead, works in the SDK
**Cons:** Cannot make decisions based on trace outcome (errors, latency)

### Tail Sampling

Decision made at the **end** of the trace, after all spans are collected:

```
Request arrives → Collect all spans → Analyze trace → Keep or drop
```

**Pros:** Can sample based on errors, latency, attributes
**Cons:** Requires collector, uses more memory, adds complexity

## SDK Samplers

Built-in samplers available in all OTel SDKs:

| Sampler | Behavior |
|---------|----------|
| `AlwaysOn` | Sample 100% of traces |
| `AlwaysOff` | Sample 0% of traces |
| `TraceIdRatioBased(ratio)` | Sample N% based on trace ID |
| `ParentBased(root)` | Respect parent's sampling decision |

### ParentBased Sampler (default)

The default sampler. It delegates to different samplers based on whether the span has a parent:

```
ParentBased(root=TraceIdRatioBased(0.1))
│
├── Has remote parent + sampled=true  → AlwaysOn
├── Has remote parent + sampled=false → AlwaysOff
├── Has local parent + sampled=true   → AlwaysOn
├── Has local parent + sampled=false  → AlwaysOff
└── No parent (root span)            → TraceIdRatioBased(0.1)
```

This means: if a parent service decided to sample, we continue sampling. If not, we don't. Root spans are sampled at 10%.

## Configuring Samplers in Python

### Environment Variables

```bash
# Always sample (development)
OTEL_TRACES_SAMPLER=always_on

# Never sample
OTEL_TRACES_SAMPLER=always_off

# Sample 25% of root traces
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.25

# Default behavior
OTEL_TRACES_SAMPLER=parentbased_always_on
```

### Programmatic Configuration

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_ON,
    ALWAYS_OFF,
    TraceIdRatioBased,
    ParentBased,
    ParentBasedTraceIdRatio,
)

# Sample 10% of root traces, respect parent decisions
provider = TracerProvider(
    sampler=ParentBased(root=TraceIdRatioBased(0.1))
)

# Or use the convenience sampler
provider = TracerProvider(
    sampler=ParentBasedTraceIdRatio(0.1)
)
```

### Custom Sampler

```python
from opentelemetry.sdk.trace.sampling import Sampler, Decision, SamplingResult
from opentelemetry.trace import SpanKind
from opentelemetry.util.types import Attributes

class PrioritySampler(Sampler):
    """Always sample errors and high-priority requests; sample 10% of the rest."""

    def should_sample(
        self,
        parent_context,
        trace_id,
        name,
        kind,
        attributes: Attributes = None,
        links=None,
    ) -> SamplingResult:
        # Always sample if priority header is set
        if attributes and attributes.get("http.request.header.x-priority") == "high":
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        # 10% sampling for everything else
        if trace_id % 10 == 0:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        return SamplingResult(Decision.DROP)

    def get_description(self):
        return "PrioritySampler"

provider = TracerProvider(sampler=PrioritySampler())
```

## Configuring Samplers in Node.js

```typescript
import { TraceIdRatioBasedSampler, ParentBasedSampler, AlwaysOnSampler } from "@opentelemetry/sdk-trace-base";

const sdk = new NodeSDK({
  sampler: new ParentBasedSampler({
    root: new TraceIdRatioBasedSampler(0.1),  // 10% of root traces
  }),
});

// Or environment variables:
// OTEL_TRACES_SAMPLER=parentbased_traceidratio
// OTEL_TRACES_SAMPLER_ARG=0.1
```

## Collector-Based Sampling

### Probabilistic Sampler Processor (head sampling)

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 25  # Keep 25% of traces
```

### Tail Sampling in the Collector

```yaml
processors:
  tail_sampling:
    decision_wait: 10s          # Wait for trace to complete
    num_traces: 100000          # Max traces to hold in memory
    expected_new_traces_per_sec: 1000
    policies:
      # Policy 1: Always keep errors
      - name: keep-errors
        type: status_code
        status_code:
          status_codes: [ERROR]

      # Policy 2: Always keep slow traces (>2s)
      - name: keep-slow
        type: latency
        latency:
          threshold_ms: 2000

      # Policy 3: Always keep specific routes
      - name: keep-important
        type: string_attribute
        string_attribute:
          key: http.route
          values: ["/api/checkout", "/api/payments"]

      # Policy 4: Sample 5% of remaining
      - name: sample-rest
        type: probabilistic
        probabilistic:
          sampling_percentage: 5

      # Policy 5: Composite — combine multiple criteria
      - name: composite-policy
        type: composite
        composite:
          max_total_spans_per_second: 1000
          policy_order: [keep-errors, keep-slow, sample-rest]
          rate_allocation:
            - policy: keep-errors
              percent: 50
            - policy: keep-slow
              percent: 30
```

## Sampling Strategies

### Strategy 1: Simple Ratio (Low Traffic)

```bash
OTEL_TRACES_SAMPLER=parentbased_always_on  # Sample everything
```

Best for: <100 req/s, development, staging.

### Strategy 2: Head Sampling (Medium Traffic)

```bash
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling
```

Best for: 100-10K req/s, when you don't need error guarantee.

### Strategy 3: Tail Sampling (High Traffic, Need Errors)

Deploy head sampling at SDK + tail sampling at Collector:

```
SDK: ParentBased(TraceIdRatioBased(0.5))  # Pre-filter 50%
      │
      ▼
Collector: tail_sampling                    # Keep errors + 10% of rest
      │
      ▼
Backend: Receives only important traces
```

Best for: >10K req/s, when you need 100% error visibility.

### Strategy 4: Priority Sampling

Sample based on request attributes:

```yaml
# Collector config
processors:
  tail_sampling:
    policies:
      - name: vip-customers
        type: string_attribute
        string_attribute:
          key: customer.tier
          values: ["enterprise", "premium"]
      - name: sample-rest
        type: probabilistic
        probabilistic:
          sampling_percentage: 1
```

## Best Practices

1. **Start with `parentbased_always_on`** — Don't optimize prematurely. Sample only when you need to.
2. **Use ParentBased** — Always respect parent sampling decisions to avoid broken traces.
3. **Tail sample at the gateway collector** — Agent collectors should forward everything; the gateway decides.
4. **Always keep errors** — A 1% sample rate means you miss 99% of errors without tail sampling.
5. **Monitor your sampling rate** — Track `otelcol_processor_dropped_spans` to understand data loss.

## Common Pitfalls

1. **Inconsistent sampling across services** — If Service A samples at 10% and Service B at 50%, traces are fragmented. Use ParentBased to propagate decisions.
2. **Tail sampling memory** — The tail sampling processor holds traces in memory while waiting. Size `num_traces` appropriately and monitor memory.
3. **Head sampling losing errors** — A 1% head sampler drops 99% of traces, including errors. Use tail sampling if you need error guarantee.
4. **Sampling after export** — Sampling should happen before export. If you sample in the collector but the SDK already exported to a second backend, that backend gets unsampled data.
5. **TraceIdRatio not being exactly N%** — It's probabilistic based on trace ID hash. With low traffic, actual rate may deviate from target.
