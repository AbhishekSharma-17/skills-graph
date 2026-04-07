# DSPy — Modules (Predict, ChainOfThought, ReAct, ProgramOfThought)

> Source: https://dspy.ai/learn/programming/modules — Written for DSPy v2.5.x

## Overview

A DSPy **module** turns a `Signature` into something callable. Modules are the analogue of `nn.Module` in PyTorch: they have learnable state (prompts, demos), they can be nested, and they can be compiled. DSPy ships five built-in modules plus a base class `dspy.Module` for composing your own.

| Module | Adds | Use for |
|--------|------|---------|
| `dspy.Predict` | Nothing; one LM call matching the signature | Simple single-step tasks |
| `dspy.ChainOfThought` | A `rationale` output field (reasoning trace) | Anything requiring multi-step reasoning |
| `dspy.ProgramOfThought` | Generates + executes Python to derive the answer | Math, symbolic problems, data transforms |
| `dspy.ReAct` | Tool-using reason/act/observe loop | Agents calling tools, web search, APIs |
| `dspy.MultiChainComparison` | Samples N CoTs, picks the best | High-stakes single-shot answers |
| `dspy.Module` | Base class for compositions | Multi-step pipelines (RAG, multi-hop) |

## dspy.Predict

The simplest module — a direct LM call that conforms to a signature.

```python
import dspy
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))

classify = dspy.Predict("text -> label")
print(classify(text="I love this phone!").label)
```

Result: a `dspy.Prediction` object. Access fields by name (`.label`, `.answer`, etc.) or use `prediction.toDict()`.

Arguments to every module include:
- `lm=` — override the default LM for this call.
- `temperature=`, `max_tokens=`, `n=` — passed through to the LM.
- `demos=` — a list of `dspy.Example`s used as few-shot (normally set by the optimizer).

## dspy.ChainOfThought

Adds a hidden `rationale` output field before the declared outputs. The LM is forced to emit its reasoning first, which empirically improves accuracy on reasoning-heavy tasks.

```python
cot = dspy.ChainOfThought("question -> answer")
pred = cot(question="If a train travels 60 km in 1.5 hours, what is its average speed?")
print(pred.rationale)  # step-by-step working
print(pred.answer)     # "40 km/h"
```

You can customise the rationale prompt:

```python
cot = dspy.ChainOfThought(
    "question -> answer",
    rationale_type=dspy.OutputField(
        desc="let's think step by step to identify the correct answer",
    ),
)
```

## dspy.ProgramOfThought

Generates Python code, executes it in a sandbox, and uses the result as the answer. Excellent for arithmetic and deterministic transforms where the LM alone is unreliable.

```python
pot = dspy.ProgramOfThought("question -> answer")
pred = pot(question="How many prime numbers are there between 1 and 100?")
print(pred.answer)  # 25
```

Under the hood it iterates: generate code, run it, if it errors, regenerate. Good companion to `dspy.Assert` for hard constraints.

## dspy.ReAct — tool-using agent

`ReAct` implements a reason–act–observe loop over a set of tools. You pass a signature and a list of Python callables; each tool's docstring becomes its description in the prompt.

```python
import dspy

def web_search(query: str) -> list[str]:
    """Search the web and return the top 3 snippets."""
    ...

def calculator(expression: str) -> float:
    """Evaluate a mathematical expression. Only basic operators."""
    return eval(expression, {"__builtins__": {}})

agent = dspy.ReAct(
    "question -> answer",
    tools=[web_search, calculator],
    max_iters=5,
)
print(agent(question="What is the square root of the population of Tokyo (millions)?"))
```

Tool signatures must have typed parameters and a docstring. `ReAct` will:
1. Ask the LM to choose a tool + arguments or emit the final answer.
2. Call the tool.
3. Feed the observation back and repeat until either the LM emits `answer` or `max_iters` is hit.

## Composing with dspy.Module

The real power of DSPy is composition. Subclass `dspy.Module`, declare sub-modules in `__init__`, implement `forward`. Compiled optimizers will tune the *whole* graph.

```python
import dspy

class MultiHopQA(dspy.Module):
    def __init__(self, passages_per_hop: int = 3, max_hops: int = 2):
        super().__init__()
        self.max_hops = max_hops
        self.generate_query = dspy.ChainOfThought(
            "context, question -> search_query"
        )
        self.retrieve = dspy.Retrieve(k=passages_per_hop)
        self.generate_answer = dspy.ChainOfThought(
            "context, question -> answer"
        )

    def forward(self, question: str) -> dspy.Prediction:
        context: list[str] = []
        for _ in range(self.max_hops):
            query = self.generate_query(context=context, question=question).search_query
            passages = self.retrieve(query).passages
            context.extend(passages)
        return self.generate_answer(context=context, question=question)
```

Idioms:
- Always call `super().__init__()`.
- Submodules assigned on `self.*` are auto-registered — the optimizer walks them via `named_predictors()`.
- `forward` takes the same kwargs as the outer signature and returns a `dspy.Prediction`.
- Do *not* perform LM calls outside a declared module — the optimizer can't tune them.

## Inspecting and debugging a call

```python
with dspy.settings.context(trace=[]):
    pred = program(question="Who wrote Hamlet?")
    for name, inputs, outputs in dspy.settings.trace:
        print(name, "->", outputs)
```

Or enable verbose logging:

```python
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini", cache=False), trace=True)
```

Every module call also stores `_trace` on the prediction object so you can inspect sub-call arguments after the fact.

## Copy and deep-copy

Modules are stateful. If you want a second independent copy (e.g. one optimized, one baseline), use `.deepcopy()`:

```python
baseline = program
compiled = compiler.compile(program.deepcopy(), trainset=trainset)
```

## Saving and loading

```python
program.save("rag.json")          # saves instructions, demos, LM config keys
program.load("rag.json")          # restores onto an existing instance
```

For full serialization (including class code), use `dspy.load` / `dspy.save`. See `08-deployment.md`.

## Common pitfalls

- **Creating modules inside `forward`.** They won't be registered with the parent, so optimizers can't tune them. Always put submodules in `__init__`.
- **Forgetting `super().__init__()`.** Your `dspy.Module` will fail to track submodules and `deepcopy` will silently lose state.
- **Calling a module with a single positional string argument.** DSPy expects keyword args matching the signature fields.
- **Using `ReAct` without docstrings on tools.** Tools without docstrings produce nonsense tool-selection prompts.
- **Nesting `ChainOfThought` inside another `ChainOfThought` unnecessarily** — one is usually enough, and the extra rationale field can confuse downstream consumers.
- **Sharing a single module instance across concurrent threads before compiling.** Modules have mutable demo state; use `.deepcopy()` or compile once and treat compiled modules as immutable thereafter.

## Related topics

- **Signatures (the inputs to modules):** `01-signatures.md`
- **Compiling / optimising a module:** `04-optimizers.md`
- **Using modules in RAG:** `06-rag-retrieval.md`
- **Constraints via Assert/Suggest:** `07-assertions.md`
