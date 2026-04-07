# DSPy — Metrics & Evaluation

> Source: https://dspy.ai/learn/evaluation/metrics — Written for DSPy v2.5.x

## Overview

A DSPy pipeline is only as good as the metric you compile it against. Metrics serve two purposes:

1. **Evaluation** — measure how well a program performs on a held-out devset (via `dspy.Evaluate`).
2. **Optimization** — guide an optimizer to pick better prompts and demos (passed as `metric=` to `BootstrapFewShot`, `MIPROv2`, etc.).

A metric is any Python callable with the signature:

```python
def metric(example, prediction, trace=None) -> bool | float:
    ...
```

- `example` — a `dspy.Example` row from your dataset (contains both inputs and gold labels).
- `prediction` — the `dspy.Prediction` the program returned for those inputs.
- `trace` — optional full call trace for inspection.
- Return `True`/`False` (treated as 1/0) or a float in `[0, 1]` for graded metrics.

## dspy.Example

Your training and eval data live in `dspy.Example` objects:

```python
import dspy

ex = dspy.Example(
    question="What is 2 + 2?",
    answer="4",
    reasoning="Basic addition.",
).with_inputs("question")

print(ex.question)        # field access
print(ex.inputs())        # just the input fields
print(ex.labels())        # the complement (answer, reasoning)
```

`with_inputs(...)` is mandatory — it tells DSPy which fields are inputs and which are labels.

## Simple string metrics

```python
def exact_match(example, pred, trace=None) -> bool:
    return example.answer.strip().lower() == pred.answer.strip().lower()

def answer_contains(example, pred, trace=None) -> bool:
    return example.answer.strip().lower() in pred.answer.strip().lower()
```

DSPy ships a few helpers in `dspy.evaluate`:

```python
from dspy.evaluate import answer_exact_match, answer_passage_match

# answer_exact_match(example, pred): normalised exact match
# answer_passage_match(example, pred): LM's answer appears verbatim in a retrieved passage
```

## Graded metrics (float)

Return any value in `[0, 1]` (or larger) — optimizers will try to maximise the average.

```python
def rouge_l(example, pred, trace=None) -> float:
    from rouge_score import rouge_scorer
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(example.answer, pred.answer)
    return scores["rougeL"].fmeasure
```

Graded metrics are more informative for `MIPROv2` than binary ones.

## Composite metrics

Combine multiple criteria with weights:

```python
def composite(example, pred, trace=None) -> float:
    correct = float(exact_match(example, pred))
    short = float(len(pred.answer) <= 80)
    return 0.8 * correct + 0.2 * short
```

You can also encode hard constraints by returning `0.0` whenever a disqualifier fires.

## LLM-as-judge metrics

For subjective criteria (tone, factuality, helpfulness) use an LM as the grader. Write a small DSPy module for the judge itself — then you can optimise the judge too.

```python
import dspy

class JudgeAnswer(dspy.Signature):
    """Judge whether a predicted answer correctly answers the question."""
    question: str = dspy.InputField()
    gold_answer: str = dspy.InputField()
    predicted_answer: str = dspy.InputField()
    is_correct: bool = dspy.OutputField(desc="True iff the prediction is semantically equivalent to the gold answer")

judge = dspy.Predict(JudgeAnswer)

def llm_judge(example, pred, trace=None) -> bool:
    result = judge(
        question=example.question,
        gold_answer=example.answer,
        predicted_answer=pred.answer,
    )
    return bool(result.is_correct)
```

Tips:
- Use a cheaper fast model for the judge to keep compile time reasonable.
- Cache judge calls (`dspy.LM(..., cache=True)`) — same pair will be re-evaluated across optimizer trials.
- Calibrate the judge against a small hand-labeled set before trusting it.

## dspy.Evaluate

`dspy.Evaluate` runs a metric across a devset in parallel and returns the mean score.

```python
from dspy.evaluate import Evaluate

evaluator = Evaluate(
    devset=devset,
    metric=exact_match,
    num_threads=8,
    display_progress=True,
    display_table=5,        # show top 5 rows in output
)

score = evaluator(program)     # -> float in [0,1]
print(f"accuracy: {score:.3f}")
```

`Evaluate` returns just the mean by default. Pass `return_outputs=True` to also get the list of `(example, prediction, score)` tuples for error analysis.

```python
score, outputs = evaluator(program, return_outputs=True)
wrong = [o for o in outputs if not o[2]]
```

## Before/after comparisons

The standard DSPy workflow:

```python
# 1. Baseline
baseline_score = evaluator(program)

# 2. Compile
compiler = BootstrapFewShot(metric=exact_match, max_bootstrapped_demos=4)
compiled = compiler.compile(program, trainset=train)

# 3. Evaluate compiled
compiled_score = evaluator(compiled)

print(f"baseline: {baseline_score:.3f}")
print(f"compiled: {compiled_score:.3f}  (delta: {compiled_score - baseline_score:+.3f})")
```

Always report the delta, not just the absolute number. A 2-point bump on an already-strong baseline is more meaningful than a 10-point bump on a bad one.

## Using traces during metric evaluation

The third `trace` argument lets a metric inspect intermediate module calls — useful during compile but not at inference.

```python
def metric_with_hops(example, pred, trace=None) -> bool:
    if not exact_match(example, pred):
        return False
    if trace is None:
        return True
    # During compile: penalise pipelines that use too many retrieval hops
    hops = sum(1 for name, _, _ in trace if "Retrieve" in name)
    return hops <= 3
```

Optimizers pass `trace` during bootstrap rounds; evaluators normally don't.

## Data splits — train / dev / test

A sensible default:
- **trainset** — used by the optimizer to generate/select demos (150–500 rows).
- **valset** — held out from the optimizer for candidate selection (50–100 rows).
- **devset** — used by `dspy.Evaluate` for iteration (50–200 rows).
- **testset** — evaluated exactly once at the end, never seen by the optimizer.

Never compile on your testset.

## Error analysis pattern

After each compile, look at the losses:

```python
_, outputs = evaluator(compiled, return_outputs=True)
for example, pred, score in outputs:
    if not score:
        print(f"Q: {example.question}")
        print(f"Gold: {example.answer}")
        print(f"Pred: {pred.answer}")
        if hasattr(pred, "rationale"):
            print(f"Rationale: {pred.rationale}")
        print("---")
```

Categorise failures into buckets (hallucination, parsing, misunderstanding) and address the biggest bucket first — by improving the signature, the metric, or the retrieval.

## Common pitfalls

- **Metric that silently mutates `example` or `pred`.** Keep them pure — optimizers may call the metric on the same pair multiple times.
- **Metric with exceptions.** An exception inside a metric halts the whole eval run. Wrap risky logic in try/except and return `0.0` on error.
- **Using accuracy on a heavily imbalanced dataset.** Switch to F1 or per-class metrics or compile will happily memorise the majority class.
- **Evaluating on the trainset.** Looks great, means nothing. Always use a held-out devset.
- **Measuring latency with `cache=True`.** The cached calls are instant; disable the cache when benchmarking end-to-end time.
- **LLM-judge drift.** If you change the judge prompt or model between compile and eval, scores become incomparable. Version the judge.

## Related topics

- **Optimizers that consume metrics:** `04-optimizers.md`
- **Adding runtime constraints with Assertions:** `07-assertions.md`
- **Writing signatures the judge can use:** `01-signatures.md`
