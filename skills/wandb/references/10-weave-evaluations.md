# Weave Evaluations

> Source: [docs.wandb.ai/weave/guides/core-types/evaluations](https://docs.wandb.ai/weave/guides/core-types/evaluations/) | weave (latest)

## Table of Contents

- [Overview](#overview)
- [Evaluation Workflow](#evaluation-workflow)
- [Defining Datasets](#defining-datasets)
- [Defining Scorers](#defining-scorers)
- [Defining Models](#defining-models)
- [Running Evaluations](#running-evaluations)
- [Multiple Trials](#multiple-trials)
- [Input Preprocessing](#input-preprocessing)
- [Custom Scorer Classes](#custom-scorer-classes)
- [EvaluationLogger](#evaluationlogger)
- [Leaderboards](#leaderboards)
- [Guardrails](#guardrails)
- [Common Patterns](#common-patterns)

## Overview

Weave Evaluations enable systematic testing of LLM applications by running models against curated datasets and scoring the outputs. The framework supports evaluation-driven development — measure first, iterate, and track improvements over time.

```
Dataset (test examples) + Scorers (evaluation functions) + Model (your app)
                              ↓
                     Evaluation Results
                              ↓
                 Comparison & Leaderboard
```

## Evaluation Workflow

```python
import asyncio
import weave
from weave import Evaluation

weave.init("my-project")

# 1. Dataset
examples = [
    {"question": "What is the capital of France?", "expected": "Paris"},
    {"question": "Who wrote Hamlet?", "expected": "William Shakespeare"},
]

# 2. Scorer
@weave.op()
def exact_match(expected: str, output: dict) -> dict:
    return {"match": expected.lower() == output["answer"].lower()}

# 3. Model
@weave.op()
def my_model(question: str) -> dict:
    # Your LLM call here
    return {"answer": call_llm(question)}

# 4. Create and run evaluation
evaluation = Evaluation(dataset=examples, scorers=[exact_match])
results = asyncio.run(evaluation.evaluate(my_model))
```

## Defining Datasets

### From Python Lists

```python
examples = [
    {"question": "What is 2+2?", "expected": "4"},
    {"question": "Capital of Japan?", "expected": "Tokyo"},
    {"question": "Who painted the Mona Lisa?", "expected": "Leonardo da Vinci"},
]

evaluation = Evaluation(dataset=examples, scorers=[scorer])
```

### From Weave Dataset Object

```python
dataset = weave.Dataset(
    name="qa-test-set",
    rows=[
        {"question": "What is ML?", "expected": "Machine Learning"},
        {"question": "What is NLP?", "expected": "Natural Language Processing"},
    ],
)

evaluation = Evaluation(dataset=dataset, scorers=[scorer])
```

Weave datasets are versioned — changing rows creates a new version.

## Defining Scorers

Scorers are functions decorated with `@weave.op()` that receive the model output and dataset row fields, returning a dict of scores.

### Simple Exact Match

```python
@weave.op()
def exact_match(expected: str, output: dict) -> dict:
    return {"match": expected == output["answer"]}
```

### Fuzzy Match

```python
@weave.op()
def fuzzy_match(expected: str, output: dict) -> dict:
    answer = output["answer"].lower().strip()
    expected_lower = expected.lower().strip()
    return {
        "exact": answer == expected_lower,
        "contains": expected_lower in answer,
    }
```

### LLM-as-Judge

```python
@weave.op()
def llm_judge(question: str, expected: str, output: dict) -> dict:
    prompt = f"""Rate the answer quality (1-5):
Question: {question}
Expected: {expected}
Actual: {output['answer']}
Return only a number 1-5."""
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    score = int(response.choices[0].message.content.strip())
    return {"quality": score, "acceptable": score >= 3}
```

### Parameter Matching

Scorer function parameters are matched by name to dataset row keys and the special `output` parameter:
- `output` — always receives the model's return value
- Other parameter names must match dataset row keys (e.g., `expected`, `question`)

## Defining Models

### Function-Based

```python
@weave.op()
def my_model(question: str) -> dict:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
    )
    return {"answer": response.choices[0].message.content}
```

### Class-Based (weave.Model)

```python
class QAModel(weave.Model):
    model_name: str
    temperature: float
    system_prompt: str

    @weave.op()
    def predict(self, question: str) -> dict:
        response = openai_client.chat.completions.create(
            model=self.model_name,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question},
            ],
        )
        return {"answer": response.choices[0].message.content}

model = QAModel(
    model_name="gpt-4o",
    temperature=0.0,
    system_prompt="Answer concisely.",
)
```

Class-based models are versioned — changing any field creates a new version.

## Running Evaluations

```python
evaluation = Evaluation(
    dataset=examples,
    scorers=[exact_match, fuzzy_match, llm_judge],
    evaluation_name="QA Benchmark v1",
)

# Async execution
results = asyncio.run(evaluation.evaluate(model))

# Results include per-example scores and aggregates
print(results)
```

## Multiple Trials

Run each example multiple times to measure consistency:

```python
# Python
results = asyncio.run(evaluation.evaluate(model, trials=3))

# Each example is run 3 times, scores are aggregated
```

## Input Preprocessing

Transform dataset rows before passing to the model:

```python
def preprocess(example: dict) -> dict:
    return {"question": example["question"].strip().lower()}

evaluation = Evaluation(
    dataset=examples,
    scorers=[exact_match],
    preprocess_model_input=preprocess,
)
```

Scorers always receive the **original** dataset row, not the preprocessed version.

## Custom Scorer Classes

For complex scoring logic with aggregation:

```python
class AccuracyScorer(weave.Scorer):
    threshold: float = 0.5

    @weave.op()
    def score(self, output: dict, expected: str) -> dict:
        return {"correct": output["answer"].lower() == expected.lower()}

    @weave.op()
    def summarize(self, score_rows: list) -> dict:
        correct = sum(1 for r in score_rows if r["correct"])
        total = len(score_rows)
        return {
            "accuracy": correct / total if total > 0 else 0,
            "correct": correct,
            "total": total,
        }
```

## EvaluationLogger

For complex workflows that don't fit the structured Evaluation framework:

```python
logger = weave.EvaluationLogger(
    dataset=examples,
    scorers=[exact_match],
)

for example in examples:
    output = custom_pipeline(example)
    logger.log(example=example, output=output)

results = logger.finish()
```

## Leaderboards

Compare models side-by-side in the Weave UI:

1. Run the same evaluation with different models
2. Navigate to the Evaluations tab in Weave
3. Select evaluations to compare
4. View per-scorer breakdowns and per-example diffs

```python
# Run same eval with different models
results_gpt4 = asyncio.run(evaluation.evaluate(gpt4_model))
results_claude = asyncio.run(evaluation.evaluate(claude_model))
results_local = asyncio.run(evaluation.evaluate(local_model))

# All three appear in the Weave leaderboard for comparison
```

## Guardrails

Define safety checks that run on every LLM call:

```python
@weave.op()
def toxicity_guard(output: dict) -> dict:
    is_toxic = check_toxicity(output["answer"])
    return {"safe": not is_toxic, "toxicity_score": is_toxic}

@weave.op()
def pii_guard(output: dict) -> dict:
    has_pii = detect_pii(output["answer"])
    return {"no_pii": not has_pii}

evaluation = Evaluation(
    dataset=examples,
    scorers=[exact_match, toxicity_guard, pii_guard],
)
```

## Common Patterns

### RAG Evaluation

```python
@weave.op()
def relevance_scorer(question: str, output: dict) -> dict:
    return {
        "has_answer": output["answer"] != "I don't know",
        "num_sources": len(output.get("sources", [])),
    }

@weave.op()
def faithfulness_scorer(output: dict) -> dict:
    answer = output["answer"]
    context = output.get("context", "")
    is_faithful = check_grounding(answer, context)
    return {"faithful": is_faithful}

evaluation = Evaluation(
    dataset=rag_test_set,
    scorers=[relevance_scorer, faithfulness_scorer, llm_judge],
)
```

### A/B Model Comparison

```python
models = {
    "gpt-4o": GPT4Model(),
    "claude-sonnet": ClaudeModel(),
    "local-llama": LocalModel(),
}

for name, model in models.items():
    results = asyncio.run(evaluation.evaluate(model))
    print(f"{name}: {results}")
```

### Regression Testing

```python
baseline_results = asyncio.run(evaluation.evaluate(baseline_model))
new_results = asyncio.run(evaluation.evaluate(new_model))

baseline_acc = baseline_results["AccuracyScorer"]["accuracy"]
new_acc = new_results["AccuracyScorer"]["accuracy"]

assert new_acc >= baseline_acc, f"Regression: {new_acc} < {baseline_acc}"
```

## Related

- Weave Tracing → `references/09-weave-tracing.md`
- Tables → `references/07-tables.md`
- Integrations → `references/11-integrations.md`
