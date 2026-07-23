# Metrics Overview

> Source: https://deepeval.com/docs/metrics-introduction

## Overview

DeepEval provides 50+ state-of-the-art metrics organized into seven categories. All metrics output a score between 0 and 1, with an optional reasoning string. A metric succeeds when its score meets or exceeds the configured threshold (default: 0.5).

## Metric Properties

Every metric shares these core properties:

```python
metric.score           # Float 0-1
metric.reason          # Explanation string
metric.is_successful() # Boolean based on threshold
```

## Common Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | `float` | `0.5` | Pass/fail cutoff score |
| `strict_mode` | `bool` | `False` | Binary scoring (0 or 1 only) |
| `verbose_mode` | `bool` | `False` | Print execution logs |
| `async_mode` | `bool` | `True` | Concurrent internal operations |
| `model` | `str \| DeepEvalBaseLLM` | OpenAI default | LLM judge model |
| `evaluation_template` | class | None | Custom prompt template |

## Metric Categories

### 1. Custom Metrics (Architecture-Agnostic)

Build metrics for any evaluation criteria:

| Metric | Description | Use Case |
|--------|-------------|----------|
| **GEval** | LLM-as-judge with custom criteria | Subjective eval (correctness, tone, coherence) |
| **DAG** | Decision-tree metric | Objective/mixed criteria with deterministic scores |
| **ConversationalGEval** | Multi-turn variant of GEval | Conversation-level custom criteria |
| **ArenaGEval** | Comparative evaluation | A/B testing between outputs |

### 2. RAG Metrics

Evaluate retrieval-augmented generation pipelines:

| Metric | Component | Required Fields |
|--------|-----------|----------------|
| **AnswerRelevancy** | Generator | `input`, `actual_output` |
| **Faithfulness** | Generator | `input`, `actual_output`, `retrieval_context` |
| **ContextualRelevancy** | Retriever | `input`, `retrieval_context` |
| **ContextualPrecision** | Retriever | `input`, `retrieval_context`, `expected_output` |
| **ContextualRecall** | Retriever | `input`, `retrieval_context`, `expected_output` |

### 3. Agent Metrics

Evaluate agentic systems:

| Metric | Description |
|--------|-------------|
| **TaskCompletion** | Did the agent achieve the goal? |
| **ToolCorrectness** | Were the right tools called? |
| **ArgumentCorrectness** | Were correct arguments passed to tools? |
| **StepEfficiency** | Was the execution path optimal? |
| **PlanAdherence** | Did the agent follow its plan? |
| **PlanQuality** | Is the agent's plan well-structured? |

### 4. Chatbot Metrics (Multi-Turn)

| Metric | Description |
|--------|-------------|
| **KnowledgeRetention** | Does the bot remember prior context? |
| **RoleAdherence** | Does the bot stay in character? |
| **ConversationCompleteness** | Did the conversation resolve the user's need? |
| **ConversationRelevancy** | Are responses relevant to the dialogue? |

### 5. Safety Metrics

| Metric | Description |
|--------|-------------|
| **Bias** | Detects demographic or ideological bias |
| **Toxicity** | Identifies harmful or offensive content |
| **NonAdvice** | Ensures no unauthorized professional advice |
| **Misuse** | Detects potential system prompt exploitation |
| **PIILeakage** | Checks for personally identifiable information |
| **RoleViolation** | Detects role/persona breaks |

### 6. Image Metrics (Multimodal)

| Metric | Description |
|--------|-------------|
| **ImageCoherence** | Visual consistency of generated images |
| **ImageHelpfulness** | Relevance of image to query |
| **ImageReference** | Fidelity to reference image |
| **TextToImage** | Prompt adherence for generation |
| **ImageEditing** | Quality of image modifications |

### 7. Other Metrics

| Metric | Description |
|--------|-------------|
| **Hallucination** | Detects unsupported claims |
| **JsonCorrectness** | Validates JSON output structure |
| **Summarization** | Evaluates summary quality |
| **Ragas** | Ragas framework compatibility |

## Metric Execution

### Synchronous

```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

metric = AnswerRelevancyMetric(threshold=0.7)
test_case = LLMTestCase(input="What is AI?", actual_output="AI is artificial intelligence.")

metric.measure(test_case)
print(f"Score: {metric.score}")
print(f"Reason: {metric.reason}")
print(f"Passed: {metric.is_successful()}")
```

### Asynchronous

```python
import asyncio
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

async def evaluate_metrics():
    metric1 = AnswerRelevancyMetric()
    metric2 = FaithfulnessMetric()
    await asyncio.gather(
        metric1.a_measure(test_case),
        metric2.a_measure(test_case)
    )

asyncio.run(evaluate_metrics())
```

## Reference vs Referenceless Metrics

**Reference-based** (require ground truth labels):
- ContextualRecall, ContextualPrecision, ToolCorrectness
- Use in development/testing only (need labeled data)

**Referenceless** (no labels needed):
- AnswerRelevancy, Faithfulness, Bias, Toxicity
- Safe for production monitoring

## Metric Selection Strategy

Limit to maximum 5 metrics total per evaluation:

- **2-3 generic, system-specific metrics** — AnswerRelevancy for RAG, ToolCorrectness for agents
- **1-2 custom, use-case-specific metrics** — Domain-specific GEval (medical helpfulness, legal accuracy)

### Recommended Starting Points

| Application Type | Start With |
|-------------------|-----------|
| RAG pipeline | AnswerRelevancy + Faithfulness |
| AI agent | ToolCorrectness + TaskCompletion |
| Chatbot | ConversationCompleteness + RoleAdherence |
| Any LLM app | GEval (custom criteria) + Bias |

## Common Pitfalls

1. **Too many metrics** — Start with 2-3 and add only when needed
2. **Wrong threshold** — Default 0.5 is lenient; production systems often need 0.7+
3. **Missing required fields** — Each metric needs specific test case parameters
4. **Ignoring `reason`** — The explanation string is critical for debugging failures
5. **Using reference metrics in production** — Only referenceless metrics work without ground truth
