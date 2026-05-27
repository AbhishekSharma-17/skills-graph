# Mastra — Evals & Observability

> Source: [mastra.ai/docs/evals](https://mastra.ai/docs/evals/overview) · [mastra.ai/docs/observability](https://mastra.ai/docs/observability/overview) · `@mastra/core` v1.37.x

## Table of Contents

- [Evals Overview](#evals-overview)
- [Scorer Types](#scorer-types)
- [Live Evaluations](#live-evaluations)
- [Workflow Step Evals](#workflow-step-evals)
- [Trace Evaluations](#trace-evaluations)
- [Custom Scorers](#custom-scorers)
- [Observability Overview](#observability-overview)
- [Three Signals](#three-signals)
- [Observability Setup](#observability-setup)
- [External Integrations](#external-integrations)
- [Studio](#studio)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Evals Overview

Mastra's evaluation system uses **scorers** to measure AI quality through quantifiable metrics. Scorers return numerical values (typically 0-1) that assess output performance across dimensions like relevance, faithfulness, and safety.

```bash
npm install @mastra/evals@latest
```

## Scorer Types

### Textual Scorers

Assess accuracy, reliability, and contextual understanding:

| Scorer | Measures |
|--------|----------|
| `createAnswerRelevancyScorer` | How relevant the answer is to the question |
| `createFaithfulnessScorer` | Whether the answer is grounded in provided context |
| `createHallucinationScorer` | Detects fabricated information |
| `createCompletenessScorer` | Whether all aspects of the query are addressed |
| `createToxicityScorer` | Presence of toxic or harmful content |

### Classification Scorers

Measure categorization accuracy for structured outputs.

### Prompt Engineering Scorers

Test instruction and format variations to optimize prompts.

## Live Evaluations

Scorers run asynchronously in production, scoring agent responses without blocking:

```typescript
import { Agent } from '@mastra/core/agent'
import { createAnswerRelevancyScorer, createFaithfulnessScorer } from '@mastra/evals'

const agent = new Agent({
  id: 'evaluated-agent',
  name: 'Evaluated Agent',
  instructions: 'Answer questions accurately using provided context.',
  model: 'openai/gpt-5.4',
  scorers: {
    relevancy: {
      scorer: createAnswerRelevancyScorer({ model: 'openai/gpt-5-mini' }),
      sampling: { type: 'ratio', rate: 0.5 },  // Score 50% of responses
    },
    faithfulness: {
      scorer: createFaithfulnessScorer({ model: 'openai/gpt-5-mini' }),
      sampling: { type: 'ratio', rate: 0.3 },
    },
  },
})
```

### Sampling Rates

Control how often scoring runs:
- `1.0` — every response (expensive, good for development)
- `0.5` — 50% of responses
- `0.1` — 10% of responses (good for production)

Results automatically store in the `mastra_scorers` database table.

## Workflow Step Evals

Attach scorers to individual workflow steps:

```typescript
const analyzeStep = createStep({
  id: 'analyze',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ summary: z.string() }),
  scorers: {
    completeness: {
      scorer: createCompletenessScorer({ model: 'openai/gpt-5-mini' }),
      sampling: { type: 'ratio', rate: 1.0 },
    },
  },
  execute: async ({ inputData }) => {
    // Step logic
    return { summary: '...' }
  },
})
```

## Trace Evaluations

Analyze historical agent interactions after enabling observability:

1. Enable observability on the Mastra instance
2. Register scorers
3. Use Studio to browse and score historical traces

```typescript
export const mastra = new Mastra({
  agents: { myAgent },
  scorers: {
    relevancy: createAnswerRelevancyScorer({ model: 'openai/gpt-5-mini' }),
    toxicity: createToxicityScorer({ model: 'openai/gpt-5-mini' }),
  },
})
```

## Custom Scorers

Create domain-specific evaluation metrics:

```typescript
import { createScorer } from '@mastra/evals'

const brandVoiceScorer = createScorer({
  id: 'brand-voice',
  description: 'Evaluates adherence to brand voice guidelines',
  model: 'openai/gpt-5-mini',
  prompt: ({ output, context }) => `
Rate the following response on brand voice adherence (0-1):
Brand guidelines: Professional, concise, no jargon.
Response: ${output}
Score (0-1):`,
  parse: (response) => {
    const score = parseFloat(response.text)
    return { score: isNaN(score) ? 0 : Math.min(1, Math.max(0, score)) }
  },
})
```

## Observability Overview

Mastra's observability captures every agent run, workflow step, tool call, and model interaction for debugging, monitoring, and optimization.

```bash
npm install @mastra/observability @mastra/duckdb
```

## Three Signals

### Tracing

Hierarchical timelines documenting all operations:

```
Agent Run (trace)
├── LLM Generation (span)
│   ├── Input tokens: 1,234
│   ├── Output tokens: 567
│   └── Duration: 2.3s
├── Tool Call: weatherTool (span)
│   ├── Input: { city: "Paris" }
│   ├── Output: { temp: 22 }
│   └── Duration: 0.8s
└── LLM Generation (span)
    ├── Input tokens: 1,890
    ├── Output tokens: 234
    └── Duration: 1.1s
```

### Logging

Structured log entries correlated with traces:

```typescript
// Logs are automatically correlated with spans
// Use span_id and trace_id for cross-referencing
```

### Metrics

Automatically extracted from traces:
- Duration per span
- Token counts (input/output)
- Estimated cost
- Error rates

## Observability Setup

```typescript
import { Mastra } from '@mastra/core/mastra'
import { MastraCompositeStore } from '@mastra/core/storage'
import { LibSQLStore } from '@mastra/libsql'
import { DuckDBStore } from '@mastra/duckdb'
import { Observability, MastraStorageExporter } from '@mastra/observability'

export const mastra = new Mastra({
  storage: new MastraCompositeStore({
    default: new LibSQLStore({ url: 'file:./mastra.db' }),
    domains: {
      observability: await new DuckDBStore().getStore('observability'),
    },
  }),
  observability: new Observability({
    configs: {
      default: {
        serviceName: 'my-app',
        exporters: [new MastraStorageExporter()],
      },
    },
  }),
})
```

### Sensitive Data Filtering

Automatically redact passwords, tokens, and API keys:

```typescript
import { SensitiveDataFilter } from '@mastra/observability'

observability: new Observability({
  configs: {
    default: {
      serviceName: 'my-app',
      processors: [new SensitiveDataFilter()],
      exporters: [new MastraStorageExporter()],
    },
  },
})
```

## External Integrations

Export traces to external platforms:

- **Langfuse** — AI-specific observability
- **Datadog** — Infrastructure monitoring
- **OpenTelemetry** — any OTLP-compatible backend

## Studio

Mastra Studio provides a visual interface for:

- **Trace viewer** — hierarchical span visualization with timing
- **Log browser** — filtered, correlated log entries
- **Metric dashboards** — cost, latency, token usage trends
- **Eval experiments** — run scorers against historical traces
- **Agent tester** — interactive conversation UI with real-time traces

Access Studio via `npx mastra dev` at `http://localhost:4111`.

## Common Patterns

### Production Monitoring Setup

```typescript
const mastra = new Mastra({
  agents: { myAgent },
  observability: new Observability({
    configs: {
      default: {
        serviceName: 'production-app',
        exporters: [
          new MastraStorageExporter(),  // Studio
          new OTLPExporter({ url: 'https://otel.example.com' }),  // External
        ],
      },
    },
  }),
  scorers: {
    relevancy: createAnswerRelevancyScorer({ model: 'openai/gpt-5-mini' }),
  },
})
```

### Cost Monitoring Agent

```typescript
const agent = new Agent({
  id: 'cost-monitored',
  model: 'openai/gpt-5.4',
  processors: [
    new CostGuardProcessor({ maxCost: 2.00, strategy: 'block' }),
  ],
  scorers: {
    relevancy: {
      scorer: createAnswerRelevancyScorer({ model: 'openai/gpt-5-mini' }),
      sampling: { type: 'ratio', rate: 0.1 },
    },
  },
})
```

## Pitfalls

1. **Metrics need OLAP storage** — DuckDB for dev, ClickHouse for production. LibSQL alone won't work for metrics aggregation
2. **Scorer sampling in production** — use low rates (0.1-0.3) to control cost; 1.0 is expensive at scale
3. **Correlation IDs** — all signals share trace/span IDs for cross-referencing. Don't create separate logging systems
4. **Storage separation** — use `MastraCompositeStore` to route observability data to a dedicated backend
5. **Custom scorers need parsing** — the `parse` function must return `{ score: number }` in the 0-1 range
