# Mastra — Guardrails & Safety

> Source: [mastra.ai/docs/agents/guardrails](https://mastra.ai/docs/agents/guardrails) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Processor Types](#processor-types)
- [Input Processors](#input-processors)
- [Output Processors](#output-processors)
- [Hybrid Processors](#hybrid-processors)
- [Strategies](#strategies)
- [Violation Handling](#violation-handling)
- [Performance Optimization](#performance-optimization)
- [Configuring Processors](#configuring-processors)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Mastra provides built-in processors that implement security controls to detect, transform, or block harmful content before it reaches the LLM or users. Processors run as guardrails — input processors run before generation, output processors run after.

## Processor Types

| Type | Runs When | Purpose |
|------|-----------|---------|
| Input | Before LLM generation | Protect the model from harmful input |
| Output | After LLM generation, before delivery | Protect users from harmful output |
| Hybrid | Both directions | Content policy enforcement |

## Input Processors

### UnicodeNormalizer

Cleans and normalizes user input:

```typescript
import { UnicodeNormalizer } from '@mastra/core/agent/processors'

new UnicodeNormalizer()
```

Standardizes whitespace, unifies Unicode characters, and removes problematic symbols that could be used for prompt injection via homoglyph attacks.

### PromptInjectionDetector

Uses an LLM to identify risky patterns:

```typescript
import { PromptInjectionDetector } from '@mastra/core/agent/processors'

new PromptInjectionDetector({
  model: 'openai/gpt-5-mini',
  strategy: 'block',  // or 'rewrite'
  types: ['injection', 'jailbreak', 'system_override'],
  threshold: 0.8,
})
```

**Strategies:**
- `block` — stops request processing immediately
- `rewrite` — rewrites the message to remove dangerous patterns

**Detection types:**
- `injection` — prompt injection attempts
- `jailbreak` — jailbreak exploits
- `system_override` — attempts to override system prompts

### LanguageDetector

Detects incoming language and translates to target:

```typescript
import { LanguageDetector } from '@mastra/core/agent/processors'

new LanguageDetector({
  model: 'openai/gpt-5-mini',
  targetLanguage: 'en',
  strategy: 'translate',
})
```

Enables multilingual support without changing the agent's instructions.

## Output Processors

### SystemPromptScrubber

Detects and redacts system prompts from model responses:

```typescript
import { SystemPromptScrubber } from '@mastra/core/agent/processors'

new SystemPromptScrubber({
  model: 'openai/gpt-5-mini',
  strategy: 'redact',
})
```

Prevents unintended disclosure of system prompt content, internal instructions, or configuration details.

### BatchPartsProcessor

Combines multiple stream parts before emitting to reduce network overhead:

```typescript
import { BatchPartsProcessor } from '@mastra/core/agent/processors'

new BatchPartsProcessor({
  batchSize: 10,      // Combine 10 stream events into one
  flushInterval: 100, // Or flush every 100ms
})
```

## Hybrid Processors

Run on both input and output:

### ModerationProcessor

Flags inappropriate content across categories:

```typescript
import { ModerationProcessor } from '@mastra/core/agent/processors'

new ModerationProcessor({
  model: 'openai/gpt-5-mini',
  strategy: 'block',
  categories: ['hate', 'harassment', 'violence', 'self-harm', 'sexual'],
  threshold: 0.7,
})
```

### PIIDetector

Detects and removes personally identifiable information:

```typescript
import { PIIDetector } from '@mastra/core/agent/processors'

new PIIDetector({
  strategy: 'redact',
  types: ['email', 'phone', 'credit_card', 'ssn', 'address'],
  replacement: '[REDACTED]',
})
```

### CostGuardProcessor

Monitors cumulative estimated costs:

```typescript
import { CostGuardProcessor } from '@mastra/core/agent/processors'

new CostGuardProcessor({
  strategy: 'block',
  maxCost: 1.00,        // $1.00 limit per conversation
  warningThreshold: 0.8, // Warn at 80%
})
```

## Strategies

| Strategy | Behavior |
|----------|----------|
| `block` | Stops processing immediately |
| `warn` | Logs warning, continues processing |
| `detect` | Detects and reports, no action |
| `redact` | Removes or masks sensitive content |
| `rewrite` | Transforms content to be safe |
| `translate` | Converts to target language |

## Violation Handling

All processors support `onViolation` callbacks:

```typescript
new PromptInjectionDetector({
  model: 'openai/gpt-5-mini',
  strategy: 'block',
  onViolation: async (violation) => {
    console.error('Injection detected:', violation.type)
    await alertSystem.notify({
      type: 'security',
      message: `Prompt injection attempt: ${violation.details}`,
      userId: violation.context?.userId,
    })
  },
})
```

Side effects (logging, alerting) execute regardless of the applied strategy.

## Performance Optimization

### Parallel Execution

Independent block-only processors can run in parallel:

```typescript
const agent = new Agent({
  id: 'safe-agent',
  processors: [
    // These run in parallel (both block-only, independent)
    [
      new PromptInjectionDetector({ strategy: 'block' }),
      new ModerationProcessor({ strategy: 'block' }),
    ],
    // This runs sequentially after the parallel group
    new PIIDetector({ strategy: 'redact' }),
  ],
})
```

### Smaller Models for Classification

Use fast, cheap models for guardrail classification:

```typescript
new PromptInjectionDetector({
  model: 'openai/gpt-5-mini',  // Fast & cheap for classification
  strategy: 'block',
})
```

### Batch Stream Chunks

Process stream chunks in batches before heavier processors:

```typescript
processors: [
  new BatchPartsProcessor({ batchSize: 10 }),
  new PIIDetector({ strategy: 'redact' }),
]
```

## Configuring Processors

```typescript
import { Agent } from '@mastra/core/agent'
import {
  UnicodeNormalizer,
  PromptInjectionDetector,
  PIIDetector,
  SystemPromptScrubber,
  ModerationProcessor,
  CostGuardProcessor,
} from '@mastra/core/agent/processors'

const safeAgent = new Agent({
  id: 'safe-agent',
  name: 'Safe Agent',
  instructions: 'You are a helpful assistant.',
  model: 'openai/gpt-5.4',
  processors: [
    // Input: normalize first
    new UnicodeNormalizer(),
    // Input: parallel safety checks
    [
      new PromptInjectionDetector({ model: 'openai/gpt-5-mini', strategy: 'block' }),
      new ModerationProcessor({ model: 'openai/gpt-5-mini', strategy: 'block' }),
    ],
    // Both: PII protection
    new PIIDetector({ strategy: 'redact' }),
    // Output: prevent prompt leakage
    new SystemPromptScrubber({ model: 'openai/gpt-5-mini', strategy: 'redact' }),
    // Both: cost monitoring
    new CostGuardProcessor({ maxCost: 5.00, strategy: 'block' }),
  ],
})
```

## Common Patterns

### Customer-Facing Agent Safety Stack

```typescript
processors: [
  new UnicodeNormalizer(),
  [
    new PromptInjectionDetector({ model: 'openai/gpt-5-mini', strategy: 'block' }),
    new ModerationProcessor({ model: 'openai/gpt-5-mini', strategy: 'block' }),
  ],
  new PIIDetector({ strategy: 'redact', types: ['credit_card', 'ssn'] }),
  new SystemPromptScrubber({ model: 'openai/gpt-5-mini', strategy: 'redact' }),
]
```

### Internal Copilot (Lighter Guardrails)

```typescript
processors: [
  new CostGuardProcessor({ maxCost: 10.00, strategy: 'warn' }),
  new PIIDetector({ strategy: 'warn', types: ['ssn', 'credit_card'] }),
]
```

## Pitfalls

1. **Order matters** — processors run sequentially. Put blocking checks before transformation
2. **Parallel arrays only for independent block processors** — don't parallelize processors that mutate content
3. **LLM-based processors add latency** — use smaller models and parallel execution to minimize impact
4. **CostGuardProcessor needs conversation scope** — configure per conversation, not per message
5. **PIIDetector is pattern-based** — it may miss unusual PII formats; combine with LLM-based detection for critical use cases
