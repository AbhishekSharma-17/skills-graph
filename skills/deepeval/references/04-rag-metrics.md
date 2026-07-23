# RAG Metrics

> Source: https://deepeval.com/docs/getting-started-rag

## Overview

DeepEval provides five dedicated metrics for evaluating retrieval-augmented generation pipelines. These split into two groups: **generator metrics** (evaluate the LLM's output quality) and **retriever metrics** (evaluate the quality of retrieved context). The principle: the final output is only as good as the context fed into your LLM.

## Generator Metrics

### AnswerRelevancyMetric

Measures whether the generated answer addresses the user's input query. Referenceless — no ground truth needed.

```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

metric = AnswerRelevancyMetric(threshold=0.7)

test_case = LLMTestCase(
    input="How do I reset my password?",
    actual_output="To reset your password, go to Settings > Security > Reset Password."
)

metric.measure(test_case)
print(f"Score: {metric.score}, Reason: {metric.reason}")
```

**Required fields:** `input`, `actual_output`

**How it works:** Breaks the actual_output into statements, then checks how many are relevant to the input. Score = relevant statements / total statements.

### FaithfulnessMetric

Ensures the generated response stays grounded in the retrieved context. Detects hallucinations and unsupported claims.

```python
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

metric = FaithfulnessMetric(threshold=0.7)

test_case = LLMTestCase(
    input="What is the refund policy?",
    actual_output="We offer a 30-day money-back guarantee with free return shipping.",
    retrieval_context=[
        "Our refund policy allows returns within 30 days for a full refund.",
        "Return shipping costs are covered by the customer."
    ]
)

metric.measure(test_case)
```

**Required fields:** `input`, `actual_output`, `retrieval_context`

**How it works:** Extracts claims from actual_output, then verifies each claim against retrieval_context. Score = supported claims / total claims. The example above would score low because "free return shipping" contradicts the context.

## Retriever Metrics

### ContextualRelevancyMetric

Evaluates whether the retrieved chunks are relevant to the user's query. Referenceless.

```python
from deepeval.metrics import ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase

metric = ContextualRelevancyMetric(threshold=0.7)

test_case = LLMTestCase(
    input="How do I reset my password?",
    actual_output="Go to Settings > Security.",
    retrieval_context=[
        "To reset your password, navigate to Settings > Security > Reset Password.",
        "Our company was founded in 2015 and has grown significantly.",
        "Password requirements include at least 8 characters."
    ]
)

metric.measure(test_case)
```

**Required fields:** `input`, `retrieval_context`

**How it works:** Evaluates each chunk's relevance to the input query. Irrelevant chunks dilute the context and can confuse the LLM.

### ContextualPrecisionMetric

Assesses the quality ranking of retrieved chunks — are the most relevant chunks ranked highest? Reference-based.

```python
from deepeval.metrics import ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase

metric = ContextualPrecisionMetric(threshold=0.7)

test_case = LLMTestCase(
    input="What is the refund policy?",
    actual_output="30-day refund policy.",
    expected_output="We offer a 30-day full refund at no extra cost.",
    retrieval_context=[
        "Company history and mission statement.",
        "All customers are eligible for a 30 day full refund at no extra cost.",
        "Contact us at support@example.com."
    ]
)

metric.measure(test_case)
```

**Required fields:** `input`, `retrieval_context`, `expected_output`

**How it works:** Checks if chunks that contain information matching the expected_output are ranked higher than irrelevant chunks.

### ContextualRecallMetric

Measures completeness — did the retriever find all the information needed? Reference-based.

```python
from deepeval.metrics import ContextualRecallMetric
from deepeval.test_case import LLMTestCase

metric = ContextualRecallMetric(threshold=0.7)

test_case = LLMTestCase(
    input="What are the system requirements?",
    actual_output="You need Python 3.8+ and 4GB RAM.",
    expected_output="System requirements: Python 3.8+, 4GB RAM, 2GB disk space, Linux/macOS/Windows.",
    retrieval_context=[
        "Python 3.8 or higher is required.",
        "Minimum 4GB of RAM is recommended.",
    ]
)

metric.measure(test_case)
```

**Required fields:** `input`, `retrieval_context`, `expected_output`

**How it works:** Compares expected_output against retrieval_context to determine what fraction of required information was retrieved. Missing "2GB disk space" and "Linux/macOS/Windows" would lower the score.

## Complete RAG Evaluation Example

### Without Tracing (Black Box)

```python
import pytest
from deepeval import assert_test
from deepeval.dataset import Golden, EvaluationDataset
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

goldens = [
    Golden(input="How do I reset my password?"),
    Golden(input="What's your refund policy?"),
]
dataset = EvaluationDataset(goldens=goldens)

@pytest.mark.parametrize("golden", dataset.goldens)
def test_rag(golden: Golden):
    answer, retrieved_chunks = rag_pipeline(golden.input)
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=answer,
        retrieval_context=retrieved_chunks,
    )
    assert_test(test_case, [AnswerRelevancyMetric(), FaithfulnessMetric()])
```

### With Tracing (Instrumented)

```python
from deepeval.tracing import observe, update_current_trace
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

@observe()
def rag_pipeline(query: str) -> str:
    chunks = retrieve(query)
    answer = generate(query, chunks)
    update_current_trace(input=query, output=answer, retrieval_context=chunks)
    return answer

@pytest.mark.parametrize("golden", dataset.goldens)
def test_rag(golden: Golden):
    rag_pipeline(golden.input)
    assert_test(golden=golden, metrics=[AnswerRelevancyMetric(), FaithfulnessMetric()])
```

### Component-Level RAG Evaluation

Attach metrics directly to retriever and generator spans:

```python
from deepeval.tracing import observe, update_current_span
from deepeval.metrics import ContextualRelevancyMetric, AnswerRelevancyMetric

@observe(metrics=[ContextualRelevancyMetric()])
def retriever(query: str) -> list[str]:
    chunks = vector_store.search(query, top_k=5)
    update_current_span(
        test_case=LLMTestCase(input=query, retrieval_context=chunks)
    )
    return chunks

@observe(metrics=[AnswerRelevancyMetric()])
def generator(query: str, chunks: list[str]) -> str:
    answer = llm.generate(query, context=chunks)
    update_current_span(
        test_case=LLMTestCase(input=query, actual_output=answer)
    )
    return answer

@observe()
def rag_pipeline(query: str) -> str:
    chunks = retriever(query)
    return generator(query, chunks)
```

## Multi-Turn RAG Metrics

For conversational RAG (e.g., customer support chatbot):

```python
from deepeval.metrics import TurnFaithfulnessMetric, TurnContextualRelevancyMetric

evaluate(
    test_cases=conversational_test_cases,
    metrics=[TurnFaithfulnessMetric(), TurnContextualRelevancyMetric()]
)
```

These check grounding turn-by-turn against each assistant response's retrieved chunks.

## RAG Metric Selection Guide

| Goal | Primary Metric | Secondary Metric |
|------|---------------|-----------------|
| Reduce hallucinations | Faithfulness | ContextualRelevancy |
| Improve answer quality | AnswerRelevancy | Faithfulness |
| Improve retrieval | ContextualRelevancy | ContextualPrecision |
| Ensure coverage | ContextualRecall | ContextualPrecision |
| Production monitoring | AnswerRelevancy + Faithfulness | (referenceless only) |

## Common Pitfalls

1. **Empty `retrieval_context`** — Faithfulness and ContextualRelevancy require non-empty lists
2. **Using ContextualRecall in production** — It's reference-based and needs expected_output
3. **Not distinguishing retriever vs generator failures** — Low Faithfulness may be a retriever problem if irrelevant chunks are retrieved
4. **Ignoring chunk ranking** — ContextualPrecision reveals ranking issues even when recall is high
