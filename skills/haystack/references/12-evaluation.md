# Haystack Evaluation

> Source: [docs.haystack.deepset.ai/docs/evaluation](https://docs.haystack.deepset.ai/docs/evaluation) | haystack-ai 2.30.0

## Table of Contents

- [Overview](#overview)
- [Evaluation Approaches](#evaluation-approaches)
- [Model-Based Evaluators](#model-based-evaluators)
- [Statistical Evaluators](#statistical-evaluators)
- [Building an Evaluation Pipeline](#building-an-evaluation-pipeline)
- [Integration Evaluators](#integration-evaluators)
- [Evaluation Best Practices](#evaluation-best-practices)
- [Common Pitfalls](#common-pitfalls)

## Overview

Evaluation measures the quality of your Haystack pipeline outputs. Two levels:

- **Component-level**: Evaluate individual components (e.g., how good is the retriever?) to find bottlenecks
- **End-to-end**: Evaluate the full pipeline as a black box (does it answer correctly?)

Haystack provides built-in evaluators and integrations with external evaluation frameworks (Ragas, DeepEval).

## Evaluation Approaches

### Model-Based Evaluation

Uses an LLM to judge quality. No ground-truth labels needed for some metrics:

- Judges answer faithfulness, relevance, and correctness
- Flexible and can evaluate nuanced quality
- Requires LLM API calls (cost and latency)

### Statistical Evaluation

Lightweight, label-based metrics:

- Exact match, MRR, MAP, recall
- Fast and deterministic
- Requires ground-truth labels

## Model-Based Evaluators

### FaithfulnessEvaluator

Checks if the generated answer is supported by the retrieved context (detects hallucination):

```python
from haystack.components.evaluators import FaithfulnessEvaluator

evaluator = FaithfulnessEvaluator()

result = evaluator.run(
    questions=["What is Haystack?"],
    contexts=[["Haystack is an AI framework by deepset."]],
    predicted_answers=["Haystack is an AI framework by deepset for building RAG apps."],
)
print(result["individual_scores"])  # [1.0] — fully faithful
print(result["score"])              # 1.0 — average score
```

**Scores**: 0.0 (hallucinated) to 1.0 (fully faithful)

### ContextRelevanceEvaluator

Checks if retrieved documents are relevant to the question:

```python
from haystack.components.evaluators import ContextRelevanceEvaluator

evaluator = ContextRelevanceEvaluator()

result = evaluator.run(
    questions=["What is Haystack?"],
    contexts=[["Haystack is an AI framework.", "Python was created in 1991."]],
)
# Scores each context document for relevance
```

### LLMEvaluator

Custom evaluation with user-defined criteria:

```python
from haystack.components.evaluators import LLMEvaluator

evaluator = LLMEvaluator(
    instructions=(
        "Evaluate the answer quality on a scale of 1-5. "
        "Consider accuracy, completeness, and clarity."
    ),
    inputs=[
        ("questions", list[str]),
        ("predicted_answers", list[str]),
    ],
    outputs=["score"],
    examples=[
        {
            "inputs": {
                "questions": "What is Python?",
                "predicted_answers": "Python is a programming language.",
            },
            "outputs": {"score": 4},
        }
    ],
)

result = evaluator.run(
    questions=["What is Haystack?"],
    predicted_answers=["Haystack is a tool."],
)
```

## Statistical Evaluators

### AnswerExactMatchEvaluator

Binary check — does the prediction exactly match ground truth?

```python
from haystack.components.evaluators import AnswerExactMatchEvaluator

evaluator = AnswerExactMatchEvaluator()
result = evaluator.run(
    predicted_answers=["Haystack"],
    ground_truth_answers=["Haystack"],
)
print(result["individual_scores"])  # [1]
```

### SASEvaluator (Semantic Answer Similarity)

Uses an embedding model to compute semantic similarity:

```python
from haystack.components.evaluators import SASEvaluator

evaluator = SASEvaluator(model="sentence-transformers/all-MiniLM-L6-v2")
evaluator.warm_up()

result = evaluator.run(
    predicted_answers=["Haystack is an AI framework"],
    ground_truth_answers=["Haystack is an AI orchestration framework by deepset"],
)
print(result["score"])  # ~0.85 (high semantic similarity)
```

### DocumentMRREvaluator

Mean Reciprocal Rank — how high is the first relevant document ranked?

```python
from haystack.components.evaluators import DocumentMRREvaluator

evaluator = DocumentMRREvaluator()
result = evaluator.run(
    ground_truth_documents=[
        [Document(content="relevant doc")]
    ],
    retrieved_documents=[
        [
            Document(content="irrelevant"),
            Document(content="relevant doc"),  # Rank 2
            Document(content="another"),
        ]
    ],
)
print(result["score"])  # 0.5 (1/rank = 1/2)
```

### DocumentMAPEvaluator

Mean Average Precision — overall ranking quality:

```python
from haystack.components.evaluators import DocumentMAPEvaluator

evaluator = DocumentMAPEvaluator()
result = evaluator.run(
    ground_truth_documents=[ground_truth],
    retrieved_documents=[retrieved],
)
```

### DocumentRecallEvaluator

What fraction of relevant documents were retrieved?

```python
from haystack.components.evaluators import DocumentRecallEvaluator

evaluator = DocumentRecallEvaluator(mode="single_hit")  # or "multi_hit"
result = evaluator.run(
    ground_truth_documents=[ground_truth],
    retrieved_documents=[retrieved],
)
```

## All Built-in Evaluators

| Evaluator | Evaluates | Type | Labels Required |
|-----------|-----------|------|-----------------|
| `FaithfulnessEvaluator` | Answers | Model-based | No |
| `ContextRelevanceEvaluator` | Documents | Model-based | No |
| `LLMEvaluator` | Custom | Model-based | No |
| `AnswerExactMatchEvaluator` | Answers | Statistical | Yes |
| `SASEvaluator` | Answers | Model-based | Yes |
| `DocumentMRREvaluator` | Documents | Statistical | Yes |
| `DocumentMAPEvaluator` | Documents | Statistical | Yes |
| `DocumentRecallEvaluator` | Documents | Statistical | Yes |

## Building an Evaluation Pipeline

Evaluate a RAG pipeline end-to-end:

```python
from haystack import Pipeline
from haystack.components.evaluators import (
    FaithfulnessEvaluator,
    ContextRelevanceEvaluator,
    AnswerExactMatchEvaluator,
)

# Prepare evaluation data
questions = [
    "What is Haystack?",
    "Who created Python?",
]
ground_truths = [
    "Haystack is an AI framework by deepset.",
    "Guido van Rossum.",
]

# Run RAG pipeline to get predictions
predictions = []
contexts = []
for q in questions:
    result = rag_pipeline.run({
        "retriever": {"query": q},
        "prompt": {"query": q},
    })
    predictions.append(result["llm"]["replies"][0].text)
    contexts.append([doc.content for doc in result["retriever"]["documents"]])

# Evaluate
faithfulness = FaithfulnessEvaluator()
faith_result = faithfulness.run(
    questions=questions,
    contexts=contexts,
    predicted_answers=predictions,
)

context_rel = ContextRelevanceEvaluator()
ctx_result = context_rel.run(
    questions=questions,
    contexts=contexts,
)

exact_match = AnswerExactMatchEvaluator()
em_result = exact_match.run(
    predicted_answers=predictions,
    ground_truth_answers=ground_truths,
)

print(f"Faithfulness: {faith_result['score']:.2f}")
print(f"Context Relevance: {ctx_result['score']:.2f}")
print(f"Exact Match: {em_result['score']:.2f}")
```

## Integration Evaluators

### Ragas

```bash
pip install ragas-haystack
```

```python
from haystack_integrations.components.evaluators.ragas import RagasEvaluator

evaluator = RagasEvaluator(metric="answer_relevancy")
result = evaluator.run(
    questions=questions,
    contexts=contexts,
    predicted_answers=predictions,
)
```

### DeepEval

```bash
pip install deepeval-haystack
```

```python
from haystack_integrations.components.evaluators.deepeval import DeepEvalEvaluator

evaluator = DeepEvalEvaluator(metric="faithfulness")
```

## Evaluation Best Practices

1. **Start with label-free metrics**: `FaithfulnessEvaluator` and `ContextRelevanceEvaluator` don't need ground-truth labels — use them first.

2. **Create evaluation datasets**: Build a curated set of questions with expected answers for systematic testing.

3. **Evaluate components individually**: If end-to-end scores are low, evaluate the retriever (MRR, Recall) and generator (Faithfulness) separately to find the bottleneck.

4. **Compare configurations**: Use evaluation to compare different retrievers, embedders, chunk sizes, or prompt templates.

5. **Monitor over time**: Re-evaluate when you change models, update documents, or modify the pipeline.

## Common Pitfalls

**Only evaluating end-to-end**: Low scores could be from bad retrieval OR bad generation. Evaluate components separately.

**Too few evaluation examples**: 5-10 examples aren't enough. Aim for 50-100+ diverse questions covering different topics and difficulty levels.

**Ignoring faithfulness**: High relevance doesn't mean the answer is faithful to the context. Always check faithfulness to catch hallucination.

**Using exact match for open-ended questions**: Exact match is too strict for free-form answers. Use `SASEvaluator` or `LLMEvaluator` for semantic comparison.

**Skipping context relevance**: Poor retrieval is the most common RAG failure. Always evaluate whether the right documents are being retrieved.

## Related Topics

- RAG patterns → `11-rag-patterns.md`
- Retrievers → `06-retrievers.md`
- Generators → `05-generators.md`
