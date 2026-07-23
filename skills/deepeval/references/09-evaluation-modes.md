# Evaluation Modes

> Source: https://deepeval.com/docs/evaluation-end-to-end-llm-evals | https://deepeval.com/docs/evaluation-component-level-llm-evals

## Overview

DeepEval supports two evaluation granularities: **end-to-end** (black box, trace level) and **component-level** (individual spans). These can run simultaneously in the same evaluation loop. There are also two execution methods: `evaluate()` for scripts and `assert_test()` for CI/CD.

## End-to-End Evaluation

Treats your LLM system as a black box — evaluates observable inputs and outputs without examining internal processes.

### With evaluate() (Scripts / Notebooks)

```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

test_cases = []
for golden in dataset.goldens:
    answer, chunks = rag_pipeline(golden.input)
    test_cases.append(LLMTestCase(
        input=golden.input,
        actual_output=answer,
        retrieval_context=chunks,
    ))

results = evaluate(
    test_cases=test_cases,
    metrics=[AnswerRelevancyMetric(), FaithfulnessMetric()]
)
```

### With assert_test() (CI/CD)

```python
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

@pytest.mark.parametrize("golden", dataset.goldens)
def test_llm(golden):
    answer = my_app(golden.input)
    test_case = LLMTestCase(input=golden.input, actual_output=answer)
    assert_test(test_case, [AnswerRelevancyMetric()])
```

### With evals_iterator() + Tracing (Recommended)

```python
from deepeval.metrics import AnswerRelevancyMetric

for golden in dataset.evals_iterator(metrics=[AnswerRelevancyMetric()]):
    my_traced_app(golden.input)  # App decorated with @observe
```

**Why `evals_iterator` is preferred:**
- Test cases built automatically from captured traces
- Built-in trace views on Confident AI
- Supports later expansion to component-level evaluation
- Handles async evaluation configuration

## Component-Level Evaluation

Evaluates individual components (retriever, generator, tools) by attaching metrics to traced spans.

### Attaching Metrics to Spans

```python
from deepeval.tracing import observe, update_current_span
from deepeval.metrics import ContextualRelevancyMetric, AnswerRelevancyMetric

@observe(metrics=[ContextualRelevancyMetric()])
async def retrieve(query: str) -> list[str]:
    chunks = await vector_store.search(query)
    update_current_span(
        test_case=LLMTestCase(input=query, retrieval_context=chunks)
    )
    return chunks

@observe(metrics=[AnswerRelevancyMetric()])
async def generate(query: str, chunks: list[str]) -> str:
    response = await llm.generate(query, context=chunks)
    update_current_span(
        test_case=LLMTestCase(input=query, actual_output=response)
    )
    return response
```

### How Component-Level Works

1. Your traced app emits multiple spans during execution
2. Metrics attached to specific spans via `@observe(metrics=[...])`
3. `evals_iterator()` opens a test run and yields goldens
4. Your app runs; each span with attached metrics becomes a scored test case
5. Per-span scores upload alongside traces as one test run

### Sub-Agent Evaluation

```python
from deepeval.metrics import TaskCompletionMetric

@observe(type="agent", metrics=[TaskCompletionMetric()])
def research_agent(query: str) -> str:
    return web_search(query)

@observe(type="agent", metrics=[TaskCompletionMetric()])
def writing_agent(topic: str, research: str) -> str:
    return generate_article(topic, research)
```

## Mixed Evaluation

Combine end-to-end and component-level in one run:

```python
from deepeval.metrics import TaskCompletionMetric, ContextualRelevancyMetric

# Component-level: attached to spans
@observe(metrics=[ContextualRelevancyMetric()])
def retriever(query):
    # ...

# End-to-end: passed to evals_iterator
for golden in dataset.evals_iterator(metrics=[TaskCompletionMetric()]):
    my_agent(golden.input)  # Trace-level gets TaskCompletion,
                            # retriever span gets ContextualRelevancy
```

## evaluate() vs assert_test()

| Feature | `evaluate()` | `assert_test()` |
|---------|-------------|----------------|
| Purpose | Scripts, notebooks | CI/CD pipelines |
| On failure | Collects results, no exception | Raises AssertionError |
| Execution | `python script.py` | `deepeval test run test_file.py` |
| Parallel | Via test_cases list | Via pytest parallelization |
| CI integration | Manual exit code | Automatic pytest integration |

## evaluate() Parameters

```python
from deepeval import evaluate

results = evaluate(
    test_cases=[...],            # List of LLMTestCase or ConversationalTestCase
    metrics=[...],               # Metrics to apply
    official=False,              # Mark as baseline run (needs Confident AI)
    run_async=True,              # Async metric execution
    max_concurrent=10,           # Max concurrent metrics
    throttle_value=0,            # Delay between metrics (seconds)
    skip_on_missing_params=False # Skip instead of error on missing fields
)
```

## assert_test() Parameters

### With Tracing

```python
assert_test(
    golden=golden,           # Active golden from parametrize
    metrics=[...],           # End-to-end metrics (optional if spans have metrics)
)
```

### Without Tracing (Black Box)

```python
assert_test(
    test_case=test_case,     # Constructed LLMTestCase
    metrics=[...],           # Required — no spans to attach to
)
```

## CI/CD with assert_test

### Test File Structure

```python
# test_llm_app.py
import pytest
from deepeval import assert_test
from deepeval.dataset import Golden, EvaluationDataset
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

dataset = EvaluationDataset(goldens=[
    Golden(input="What is your return policy?"),
    Golden(input="How do I contact support?"),
])

@pytest.mark.parametrize("golden", dataset.goldens)
def test_rag_quality(golden: Golden):
    answer, chunks = rag_pipeline(golden.input)
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=answer,
        retrieval_context=chunks,
    )
    assert_test(test_case, [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
    ])
```

### Run Tests

```bash
deepeval test run test_llm_app.py
```

### Key deepeval test run Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--verbose` | `-v` | Detailed output |
| `--exit-on-first-failure` | `-x` | Stop on first failure |
| `--num-processes` | `-n` | Parallel execution |
| `--use-cache` | `-c` | Leverage cached results |
| `--repeat` | `-r` | Rerun tests N times |
| `--identifier` | `-id` | Label the test run |
| `--official` | `-o` | Mark as baseline |
| `--skip-on-missing-params` | `-s` | Skip vs error on missing |

## One-Off Evaluation (Debugging)

For quick iteration on a single metric:

```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

metric = AnswerRelevancyMetric(threshold=0.7, verbose_mode=True)
test_case = LLMTestCase(
    input="What is AI?",
    actual_output="AI is artificial intelligence."
)

metric.measure(test_case)
print(f"Score: {metric.score}")
print(f"Reason: {metric.reason}")
print(f"Passed: {metric.is_successful()}")
```

## Common Pitfalls

1. **Using `evaluate()` in CI/CD** — Use `assert_test()` which properly fails the pipeline
2. **Not using `deepeval test run`** — Plain `pytest` misses DeepEval's added functionality
3. **Forgetting `update_current_span`** — Component-level metrics need test case data on each span
4. **End-to-end only** — Add component-level metrics to pinpoint where failures originate
5. **No baseline runs** — Use `--official` flag to establish regression baselines
