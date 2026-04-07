# DSPy — Assertions & Suggestions

> Source: https://dspy.ai/learn/programming/assertions — Written for DSPy v2.5.x

## Overview

Assertions and suggestions let a DSPy module declare **runtime constraints** on LM outputs and automatically retry (with self-refinement feedback) when those constraints fail. They turn "hoping the LM obeys a rule" into "the rule is enforced as code".

Two primitives:

- **`dspy.Assert(condition, message)`** — hard constraint. If it fails after backtracking retries, the entire call raises.
- **`dspy.Suggest(condition, message)`** — soft constraint. If it ultimately fails, DSPy logs a warning and returns the best attempt.

Both integrate with the optimizer: during compile, assertion feedback is folded into the bootstrapping loop so the optimizer preferentially keeps demos that *don't* trigger retries.

## Basic usage

Wrap a module in `assert_transform_module` (or use the context manager) and call `dspy.Assert` inside `forward`:

```python
import dspy
from dspy.primitives.assertions import (
    assert_transform_module,
    backtrack_handler,
)

class ConciseAnswer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.ChainOfThought("question -> answer")

    def forward(self, question: str) -> dspy.Prediction:
        pred = self.predict(question=question)
        dspy.Suggest(
            len(pred.answer.split()) <= 20,
            "The answer should be at most 20 words; rewrite it more concisely.",
        )
        return pred

program = assert_transform_module(
    ConciseAnswer(),
    backtrack_handler,
)
result = program(question="Explain relativity in one sentence.")
print(result.answer)
```

When the suggestion fails, DSPy appends the feedback message to the next attempt's prompt and re-runs the module. By default it tries up to 2 additional attempts.

## Assert vs Suggest

| Primitive | Behaviour on failure after retries |
|-----------|-----------------------------------|
| `dspy.Assert` | Raises `AssertionError`; caller must handle |
| `dspy.Suggest` | Logs warning; returns last attempt |

Use `Assert` for correctness-critical constraints (valid JSON shape, references exist) and `Suggest` for style/quality nudges (length, tone).

## Multiple constraints

Stack several checks; they're evaluated sequentially in order.

```python
def forward(self, question: str) -> dspy.Prediction:
    pred = self.predict(question=question)

    dspy.Assert(
        pred.answer.strip() != "",
        "Answer cannot be empty.",
    )
    dspy.Suggest(
        not pred.answer.lower().startswith("i don't know"),
        "Avoid refusing; make your best guess if uncertain.",
    )
    dspy.Suggest(
        len(pred.answer.split(".")) >= 2,
        "Provide at least two sentences of explanation.",
    )
    return pred
```

## Validating structured output

Assertions shine for JSON / Pydantic validation — if parsing fails, feed the error back.

```python
import json
import dspy

class ExtractJSON(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict("text -> json_output")

    def forward(self, text: str) -> dspy.Prediction:
        pred = self.predict(text=text)
        try:
            data = json.loads(pred.json_output)
        except json.JSONDecodeError as e:
            dspy.Assert(False, f"Output must be valid JSON. Error: {e}")
            raise
        dspy.Assert(
            "name" in data and "age" in data,
            "JSON must contain 'name' and 'age' fields.",
        )
        return pred
```

Pydantic version:

```python
from pydantic import BaseModel, ValidationError

class Person(BaseModel):
    name: str
    age: int

def forward(self, text: str) -> dspy.Prediction:
    pred = self.predict(text=text)
    try:
        person = Person.model_validate_json(pred.json_output)
    except ValidationError as e:
        dspy.Assert(
            False,
            f"Output must match Person schema. Errors: {e.errors()}",
        )
        raise
    return dspy.Prediction(person=person)
```

## Backtracking behaviour

The `backtrack_handler` catches failed assertions, appends the message to the next attempt as a correction, and retries the module. Configure:

```python
from dspy.primitives.assertions import assert_transform_module, backtrack_handler

program = assert_transform_module(
    MyProgram(),
    functools.partial(backtrack_handler, max_backtracks=3),
)
```

`max_backtracks` controls how many times a single failed assertion will trigger a retry within one call.

## Using a custom handler

If you want to log, emit telemetry, or route failures elsewhere:

```python
def my_handler(func):
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except dspy.DSPyAssertionError as e:
                print(f"[attempt {attempt}] assertion failed: {e}")
                # optionally mutate kwargs with hints
        raise RuntimeError("Exhausted retries")
    return wrapper

program = assert_transform_module(MyProgram(), my_handler)
```

## Assertions + Optimizers

When you run an optimizer on an assertion-wrapped program, failed traces are excluded from the bootstrapped demos. This biases the compile toward traces that satisfy your constraints on the first try — a form of implicit reward shaping.

```python
compiled = BootstrapFewShot(metric=my_metric).compile(
    assert_transform_module(MyProgram(), backtrack_handler),
    trainset=train,
)
```

You should still write a numeric `metric` — assertions complement it, they don't replace it.

## Assertion-driven self-refinement pattern

A common pattern: generate, critique, refine. DSPy lets you express this declaratively.

```python
class RefineEssay(dspy.Module):
    def __init__(self):
        super().__init__()
        self.write = dspy.ChainOfThought("topic -> essay")
        self.critic = dspy.Predict("essay -> issues: list[str]")

    def forward(self, topic: str) -> dspy.Prediction:
        draft = self.write(topic=topic).essay
        issues = self.critic(essay=draft).issues
        dspy.Suggest(
            len(issues) == 0,
            f"Rewrite the essay to fix these issues: {'; '.join(issues)}",
        )
        return dspy.Prediction(essay=draft)
```

## Logging and debugging assertion failures

Enable DSPy's trace mode to see what each retry sent to the LM:

```python
with dspy.settings.context(trace=[]):
    result = program(question="...")
    for name, inputs, outputs in dspy.settings.trace:
        print(name, inputs, "->", outputs)
```

For production, wire `dspy.Assert` failures into your observability stack (Langfuse, OTEL) so you can spot rules that fail often.

## Common pitfalls

- **Forgetting `assert_transform_module`.** Calling `dspy.Assert` in a raw `dspy.Module` that wasn't wrapped will raise immediately — no retry logic is active.
- **Writing assertion messages that don't explain *how* to fix the violation.** The message is fed back to the LM verbatim; make it actionable ("rewrite more concisely"), not descriptive ("too long").
- **Piling on 10 assertions per call.** Each failure triggers a retry; you can end up with 10× the LM spend. Prefer 1–3 high-value constraints.
- **Using `Assert` for soft style rules.** Your callers get unexpected exceptions. Use `Suggest` unless the rule is truly correctness-critical.
- **Checking conditions outside the module's `forward`.** Assertions must fire during the call so the backtrack handler can retry.
- **Expecting assertions to replace a metric.** They guide retries *during* a call; the optimizer still needs a metric to pick demos across calls.

## Related topics

- **Modules that assertions wrap:** `02-modules.md`
- **Metrics that complement assertions:** `05-metrics-evaluation.md`
- **Production error handling and logging:** `08-deployment.md`
