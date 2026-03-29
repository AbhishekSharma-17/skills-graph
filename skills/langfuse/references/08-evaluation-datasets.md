# Evaluation & Datasets

> Source: [langfuse.com/docs/evaluation/overview](https://langfuse.com/docs/evaluation/overview)

## Table of Contents

- [Overview](#overview)
- [Datasets](#datasets)
- [Creating Dataset Items](#creating-dataset-items)
- [Running Experiments](#running-experiments)
- [Scoring](#scoring)
- [LLM-as-a-Judge](#llm-as-a-judge)
- [Human Annotations](#human-annotations)
- [Live Evaluators](#live-evaluators)
- [Experiment Workflows](#experiment-workflows)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

---

## Overview

Langfuse evaluation replaces guesswork with data. Measure LLM application quality using:

- **Datasets** — structured collections of inputs and expected outputs
- **Experiments** — run your app against a dataset and compare results
- **Scoring** — attach quality metrics (automated or human)
- **LLM-as-a-judge** — automated evaluation using an LLM evaluator
- **Annotation queues** — human review workflows

## Datasets

A dataset is a collection of items (input + optional expected output) used to benchmark your application.

### Creating Datasets

```python
from langfuse import get_client

langfuse = get_client()

langfuse.create_dataset(
    name="qa-golden-set",
    description="Golden test cases for QA pipeline",
    metadata={"author": "team-ml", "domain": "customer-support"},
)
```

```typescript
await langfuse.api.datasets.create({
  name: "qa-golden-set",
  description: "Golden test cases for QA pipeline",
  metadata: { author: "team-ml" },
});
```

### Dataset Organization

Use slashes for virtual folders:

```python
langfuse.create_dataset(name="evaluation/qa/customer-support")
langfuse.create_dataset(name="evaluation/qa/technical-docs")
```

## Creating Dataset Items

### Via SDK

```python
langfuse.create_dataset_item(
    dataset_name="qa-golden-set",
    input={"question": "What is the refund policy?"},
    expected_output={"answer": "Full refund within 30 days of purchase."},
    metadata={"category": "refunds", "difficulty": "easy"},
)
```

```typescript
await langfuse.api.datasetItems.create({
  datasetName: "qa-golden-set",
  input: { question: "What is the refund policy?" },
  expectedOutput: { answer: "Full refund within 30 days of purchase." },
  metadata: { category: "refunds" },
});
```

### From Production Traces

Link dataset items to their source trace for context:

```python
langfuse.create_dataset_item(
    dataset_name="qa-golden-set",
    input={"question": "How do I reset my password?"},
    expected_output={"answer": "Go to Settings > Security > Reset Password."},
    source_trace_id="trace-abc-123",
    source_observation_id="generation-xyz-789",
)
```

### Via UI

- Upload CSV files with input/expected_output columns
- Create items manually in the dataset view
- Add items from the trace viewer (click "Add to dataset")

### Schema Enforcement

Define JSON schemas to validate items:

```python
langfuse.create_dataset(
    name="typed-dataset",
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "context": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["question"],
    },
    expected_output_schema={
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
        },
        "required": ["answer"],
    },
)
```

## Running Experiments

### Python SDK

```python
dataset = langfuse.get_dataset("qa-golden-set")

for item in dataset.items:
    # Run your app
    result = my_qa_pipeline(item.input["question"])

    # Link the result trace to the dataset item
    item.link(
        trace_id=result.trace_id,
        run_name="experiment-v2-gpt4o",
        run_metadata={"model": "gpt-4o", "temperature": 0.3},
    )

    # Score the result
    item.score(
        name="correctness",
        value=evaluate_correctness(result.answer, item.expected_output["answer"]),
    )

langfuse.flush()
```

### Versioned Experiments

Datasets support versioning for reproducible experiments:

```python
from datetime import datetime, timezone

version_timestamp = datetime(2026, 3, 15, 6, 30, 0, tzinfo=timezone.utc)
dataset = langfuse.get_dataset(
    name="qa-golden-set",
    version=version_timestamp,
)
# Run experiment against this specific snapshot
```

## Scoring

Attach scores to traces, observations, or dataset run items.

### Score Types

| Type | Value | Example |
|------|-------|---------|
| Numeric | `float` | Relevance: 0.85 |
| Boolean | `0` or `1` | Factually correct: 1 |
| Categorical | `str` | Quality: "good" |

### Via SDK

```python
# Score a trace
langfuse.score(
    trace_id="trace-123",
    name="user-satisfaction",
    value=1,
    comment="User rated response as helpful",
)

# Score a specific observation
langfuse.score(
    trace_id="trace-123",
    observation_id="gen-456",
    name="relevance",
    value=0.92,
)
```

### Score Definitions

Define scoring rubrics for consistency:

```python
langfuse.create_score_config(
    name="helpfulness",
    data_type="NUMERIC",
    min_value=0,
    max_value=1,
    description="How helpful was the response?",
)
```

## LLM-as-a-Judge

Automate evaluation using an LLM to score outputs:

### Setting Up Evaluators in UI

1. Go to **Evaluation** > **Evaluators**
2. Click **New Evaluator**
3. Configure:
   - Name and description
   - LLM model to use as judge (e.g., GPT-4o)
   - Evaluation prompt template
   - Scoring rubric (what scores mean)
   - Score name and type

### Evaluation Prompt Template Example

```
You are evaluating the quality of an AI assistant's response.

User Question: {{input}}
Expected Answer: {{expected_output}}
Actual Answer: {{output}}

Rate the response on a scale of 1-5:
1 = Completely wrong or irrelevant
2 = Partially relevant but mostly incorrect
3 = Somewhat helpful but missing key information
4 = Good answer with minor gaps
5 = Excellent, comprehensive answer

Return ONLY the numeric score.
```

### Programmatic Evaluation

```python
from langfuse import get_client

langfuse = get_client()

# Fetch traces and evaluate
traces = langfuse.fetch_traces(name="qa-pipeline", limit=100)

for trace in traces.data:
    # Run your evaluator
    score = evaluate_with_llm(
        input=trace.input,
        output=trace.output,
    )

    langfuse.score(
        trace_id=trace.id,
        name="llm-judge-quality",
        value=score,
    )
```

## Human Annotations

### Annotation Queues

1. Create a queue in **Evaluation** > **Annotation Queues**
2. Define scoring criteria and rubric
3. Add traces to the queue (manually or via filter rules)
4. Annotators review and score traces
5. Scores appear on traces and in analytics

### Via API

```python
# Create annotation queue
langfuse.create_annotation_queue(
    name="quality-review",
    description="Manual review of customer-facing responses",
    score_configs=["helpfulness", "factual-accuracy"],
)
```

## Live Evaluators

Run evaluations automatically on incoming production traces:

1. Go to **Evaluation** > **Live Evaluators**
2. Configure trigger conditions (trace name, tags, etc.)
3. Set the evaluator (LLM-as-a-judge template)
4. Scores are automatically attached to matching traces

Use cases:
- Monitor production quality in real-time
- Detect hallucinations or safety issues
- Track quality trends over time

## Experiment Workflows

### Comparing Prompt Versions

```python
dataset = langfuse.get_dataset("qa-golden-set")

for prompt_label in ["v1-baseline", "v2-improved"]:
    prompt = langfuse.get_prompt("qa-prompt", label=prompt_label)

    for item in dataset.items:
        compiled = prompt.compile(**item.input)
        result = call_llm(compiled)

        item.link(
            trace_id=result.trace_id,
            run_name=f"experiment-{prompt_label}",
        )

langfuse.flush()
# Compare results in Langfuse UI > Datasets > Experiments
```

### Comparing Models

```python
for model in ["gpt-4o", "claude-3.5-sonnet", "gpt-4o-mini"]:
    for item in dataset.items:
        result = call_llm(item.input["question"], model=model)
        item.link(trace_id=result.trace_id, run_name=f"model-{model}")
```

## Common Patterns

### CI/CD Quality Gates

```python
# In CI pipeline
dataset = langfuse.get_dataset("regression-tests")
scores = []

for item in dataset.items:
    result = my_pipeline(item.input)
    score = evaluate(result, item.expected_output)
    scores.append(score)

avg_score = sum(scores) / len(scores)
assert avg_score >= 0.85, f"Quality regression: {avg_score:.2f} < 0.85"
```

### Feedback Collection

```python
# In your API endpoint
@app.post("/feedback")
async def submit_feedback(trace_id: str, rating: int):
    langfuse.score(
        trace_id=trace_id,
        name="user-feedback",
        value=rating,
        comment="User-submitted rating",
    )
    return {"status": "ok"}
```

## Pitfalls

1. **Dataset size** — Very large datasets (>10K items) may slow down experiment runs. Use sampling for faster iteration.

2. **Evaluation prompt quality** — LLM-as-a-judge is only as good as the evaluation prompt. Calibrate with human annotations first.

3. **Score consistency** — Different LLM judges may produce inconsistent scores. Standardize on one judge model for comparable results.

4. **Missing flush** — Don't forget `langfuse.flush()` after batch operations. Scores and links may be lost.
