# Evaluation

> Source: [developers.llamaindex.ai — Evaluating](https://developers.llamaindex.ai/python/framework/module_guides/evaluating/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Response Evaluation](#response-evaluation)
- [Retrieval Evaluation](#retrieval-evaluation)
- [Question Generation](#question-generation)
- [Batch Evaluation](#batch-evaluation)
- [Cost Analysis](#cost-analysis)
- [Community Integrations](#community-integrations)
- [Common Patterns](#common-patterns)

## Overview

LlamaIndex provides evaluation tools to measure the quality of RAG pipelines across two dimensions:

1. **Response evaluation** — Is the generated answer faithful, relevant, and correct?
2. **Retrieval evaluation** — Are the right documents being retrieved?

Most evaluators use an LLM (like GPT-4) as a judge, enabling automated evaluation without human labeling.

## Response Evaluation

### Faithfulness Evaluator

Checks if the answer is grounded in the retrieved context (detects hallucination):

```python
from llama_index.core.evaluation import FaithfulnessEvaluator
from llama_index.llms.openai import OpenAI

evaluator = FaithfulnessEvaluator(llm=OpenAI(model="gpt-4o"))

query_engine = index.as_query_engine()
response = query_engine.query("What is the revenue?")

eval_result = evaluator.evaluate_response(
    query="What is the revenue?",
    response=response,
)

print(f"Faithful: {eval_result.passing}")   # True/False
print(f"Score: {eval_result.score}")         # 0.0-1.0
print(f"Feedback: {eval_result.feedback}")   # Explanation
```

### Relevancy Evaluator

Checks if the response actually answers the question:

```python
from llama_index.core.evaluation import RelevancyEvaluator

evaluator = RelevancyEvaluator(llm=OpenAI(model="gpt-4o"))

eval_result = evaluator.evaluate_response(
    query="What is the company strategy?",
    response=response,
)
```

### Correctness Evaluator

Compares against a reference answer (requires ground truth):

```python
from llama_index.core.evaluation import CorrectnessEvaluator

evaluator = CorrectnessEvaluator(llm=OpenAI(model="gpt-4o"))

eval_result = evaluator.evaluate(
    query="What year was the company founded?",
    response="The company was founded in 2015.",
    reference="The company was founded in 2015.",
)

print(f"Score: {eval_result.score}")  # 1.0 - 5.0
```

### Semantic Similarity Evaluator

Measures semantic similarity between generated and reference answers:

```python
from llama_index.core.evaluation import SemanticSimilarityEvaluator

evaluator = SemanticSimilarityEvaluator()

eval_result = evaluator.evaluate(
    response="The revenue was $10M in Q3.",
    reference="Q3 revenue reached $10 million.",
)

print(f"Score: {eval_result.score}")  # 0.0 - 1.0
```

### Guideline Evaluator

Check if responses follow specific guidelines:

```python
from llama_index.core.evaluation import GuidelineEvaluator

evaluator = GuidelineEvaluator(
    llm=OpenAI(model="gpt-4o"),
    guidelines=(
        "The response should be professional and formal. "
        "It should not contain slang or casual language. "
        "It should cite sources when making factual claims."
    ),
)

eval_result = evaluator.evaluate_response(
    query="What is the outlook?",
    response=response,
)
```

## Retrieval Evaluation

Evaluate whether the retriever is finding the right documents.

### Dataset Generation

Automatically generate question-context pairs for evaluation:

```python
from llama_index.core.evaluation import generate_question_context_pairs

qa_dataset = generate_question_context_pairs(
    nodes=nodes,
    llm=OpenAI(model="gpt-4o"),
    num_questions_per_chunk=2,
)

# Save for reuse
qa_dataset.save_json("qa_dataset.json")
```

### Retriever Evaluation

```python
from llama_index.core.evaluation import RetrieverEvaluator

retriever = index.as_retriever(similarity_top_k=5)

evaluator = RetrieverEvaluator.from_metric_names(
    ["mrr", "hit_rate"],
    retriever=retriever,
)

eval_results = await evaluator.aevaluate_dataset(qa_dataset)

for result in eval_results:
    print(f"Query: {result.query}")
    print(f"MRR: {result.metric_vals['mrr']:.4f}")
    print(f"Hit Rate: {result.metric_vals['hit_rate']:.4f}")
```

### Retrieval Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `hit_rate` | Fraction of queries where relevant doc appears in top-k | 0.0–1.0 |
| `mrr` | Mean Reciprocal Rank — rank position of first relevant doc | 0.0–1.0 |
| `precision` | Fraction of retrieved docs that are relevant | 0.0–1.0 |
| `recall` | Fraction of relevant docs that are retrieved | 0.0–1.0 |
| `ndcg` | Normalized Discounted Cumulative Gain | 0.0–1.0 |

## Question Generation

Generate evaluation questions from your data:

```python
from llama_index.core.evaluation import DatasetGenerator

generator = DatasetGenerator.from_documents(
    documents,
    llm=OpenAI(model="gpt-4o"),
    num_questions_per_chunk=3,
)

eval_questions = generator.generate_questions_from_nodes()
```

### With Reference Answers

```python
qa_pairs = generator.generate_questions_from_nodes(
    with_reference_answers=True
)

for pair in qa_pairs:
    print(f"Q: {pair.query}")
    print(f"A: {pair.reference_answer}")
```

## Batch Evaluation

Evaluate multiple queries at once:

```python
from llama_index.core.evaluation import BatchEvalRunner

runner = BatchEvalRunner(
    evaluators={
        "faithfulness": FaithfulnessEvaluator(llm=eval_llm),
        "relevancy": RelevancyEvaluator(llm=eval_llm),
    },
    workers=4,
)

eval_results = await runner.aevaluate_queries(
    query_engine=query_engine,
    queries=eval_questions,
)

for key, results in eval_results.items():
    scores = [r.score for r in results if r.score is not None]
    avg = sum(scores) / len(scores) if scores else 0
    print(f"{key}: {avg:.2f}")
```

### With Reference Answers

```python
eval_results = await runner.aevaluate_queries(
    query_engine=query_engine,
    queries=queries,
    reference_answers=references,
)
```

## Cost Analysis

Track token usage and API costs:

```python
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
import tiktoken

token_counter = TokenCountingHandler(
    tokenizer=tiktoken.encoding_for_model("gpt-4o").encode,
)

callback_manager = CallbackManager([token_counter])

from llama_index.core import Settings
Settings.callback_manager = callback_manager

# Run queries
response = query_engine.query("What is the revenue?")

# Check usage
print(f"Embedding tokens: {token_counter.total_embedding_token_count}")
print(f"LLM prompt tokens: {token_counter.prompt_llm_token_count}")
print(f"LLM completion tokens: {token_counter.completion_llm_token_count}")
print(f"Total LLM tokens: {token_counter.total_llm_token_count}")
```

## Community Integrations

| Tool | Purpose | Package |
|------|---------|---------|
| DeepEval | Unit testing for LLMs | `deepeval` |
| Ragas | RAG evaluation framework | `ragas` |
| TruLens | Evaluation and tracking | `trulens-eval` |
| UpTrain | Evaluation and monitoring | `uptrain` |
| RAGChecker | Fine-grained RAG diagnostics | `ragchecker` |
| Cleanlab | Data quality and reliability | `cleanlab` |
| Tonic Validate | RAG quality metrics | `tonic_validate` |

### DeepEval Integration

```python
from deepeval.integrations.llama_index import DeepEvalFaithfulnessEvaluator

evaluator = DeepEvalFaithfulnessEvaluator()
eval_result = evaluator.evaluate_response(
    query="...", response=response
)
```

### Ragas Integration

```python
from ragas.integrations.llama_index import evaluate

result = evaluate(
    query_engine=query_engine,
    dataset=qa_dataset,
    metrics=["answer_relevancy", "faithfulness"],
)
```

## Common Patterns

### A/B Testing Retrieval Strategies

```python
strategies = {
    "vector_top5": index.as_retriever(similarity_top_k=5),
    "vector_top10": index.as_retriever(similarity_top_k=10),
    "hybrid": hybrid_retriever,
}

for name, retriever in strategies.items():
    evaluator = RetrieverEvaluator.from_metric_names(
        ["mrr", "hit_rate"], retriever=retriever
    )
    results = await evaluator.aevaluate_dataset(qa_dataset)
    avg_mrr = sum(r.metric_vals["mrr"] for r in results) / len(results)
    print(f"{name}: MRR={avg_mrr:.4f}")
```

### Continuous Evaluation Pipeline

```python
async def evaluate_pipeline(query_engine, test_queries, references):
    runner = BatchEvalRunner(
        evaluators={
            "faithfulness": FaithfulnessEvaluator(llm=eval_llm),
            "relevancy": RelevancyEvaluator(llm=eval_llm),
            "correctness": CorrectnessEvaluator(llm=eval_llm),
        },
    )
    results = await runner.aevaluate_queries(
        query_engine=query_engine,
        queries=test_queries,
        reference_answers=references,
    )
    
    metrics = {}
    for metric_name, evals in results.items():
        scores = [e.score for e in evals if e.score is not None]
        metrics[metric_name] = sum(scores) / len(scores) if scores else 0
    
    return metrics
```
