# DSPy — Overview & Quickstart

> Source: https://dspy.ai — Written for DSPy v2.5.x

## What is DSPy?

DSPy ("Declarative Self-improving Python") is a framework from Stanford NLP for **programming**, not prompting, language models. Instead of hand-crafting brittle prompt strings, you declare the *inputs*, *outputs*, and *control flow* of your LLM pipeline in typed Python, then let a DSPy **optimizer** (a compiler) search for the best prompts, few-shot examples, or even fine-tuned weights automatically against a metric you define.

Three core ideas:

1. **Signatures** — declarative I/O specs (`"question -> answer"`, or a class with typed fields). They describe *what* the LM should do, not *how*.
2. **Modules** — composable blocks (`Predict`, `ChainOfThought`, `ReAct`, custom `dspy.Module` subclasses) that turn signatures into callable LM programs.
3. **Optimizers** — algorithms (`BootstrapFewShot`, `MIPROv2`, `COPRO`) that compile a module + a training set + a metric into an optimized version with better prompts/demos.

## When to use DSPy

Use DSPy when:
- You find yourself hand-tuning prompt strings and few-shot examples by trial and error.
- You have an eval set (even tiny — 20–200 examples) and a metric function.
- You want portability across LLM providers without rewriting prompts.
- You're building multi-step pipelines (RAG, ReAct agents, multi-hop retrieval) where each step has its own sub-prompt.
- You want to systematically improve a pipeline by compiling rather than manual iteration.

Don't use DSPy when:
- You need pixel-perfect control over a single specific prompt (DSPy rewrites prompts during compile).
- You have no way to define a metric and no examples at all.
- You're making single one-shot calls where the prompt is already trivial.

## Install

```bash
pip install dspy
# optional extras
pip install 'dspy[anthropic,qdrant,chromadb]'
```

DSPy requires Python 3.9+. For vLLM / Ollama / local models see `03-lm-configuration.md`.

## 60-second quickstart

```python
import dspy

# 1. Configure a default LM once
lm = dspy.LM("openai/gpt-4o-mini", api_key="sk-...")
dspy.configure(lm=lm)

# 2. Declare a signature — inline string form
qa = dspy.Predict("question -> answer")

# 3. Call it like a function
result = qa(question="What is the capital of France?")
print(result.answer)  # -> "Paris"
```

Behind the scenes DSPy synthesised an instruction-style prompt, sent it to the LM, parsed the structured output, and returned a `Prediction` object whose fields match your signature's output fields.

## Upgrading from prompting to programming

The same task with a class-based signature, chain-of-thought, and a metric-driven compile step:

```python
import dspy

class GenerateAnswer(dspy.Signature):
    """Answer a factual question concisely."""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="one short sentence")

# Add reasoning trace automatically
program = dspy.ChainOfThought(GenerateAnswer)

# Training set — dspy.Example objects
trainset = [
    dspy.Example(question="Capital of France?", answer="Paris").with_inputs("question"),
    dspy.Example(question="Largest ocean?", answer="Pacific Ocean").with_inputs("question"),
    # ... ~20–200 examples
]

def exact_match(example, pred, trace=None) -> bool:
    return example.answer.lower() in pred.answer.lower()

# Compile: search over few-shot demos that maximise the metric
from dspy.teleprompt import BootstrapFewShot
compiler = BootstrapFewShot(metric=exact_match, max_bootstrapped_demos=4)
compiled = compiler.compile(program, trainset=trainset)

print(compiled(question="What is 2+2?"))
```

The key insight: you never wrote a prompt. DSPy wrote it, demonstrated good examples from the trainset, and optimised the selection.

## Core concepts cheat sheet

| Concept | What it is | Reference |
|---------|-----------|-----------|
| `dspy.Signature` | Declarative I/O spec (inline string or class) | `01-signatures.md` |
| `dspy.Predict` | Simplest module: signature → one LM call | `02-modules.md` |
| `dspy.ChainOfThought` | Adds a `rationale` field, forcing step-by-step reasoning | `02-modules.md` |
| `dspy.ReAct` | Tool-using agent loop (reason → act → observe) | `02-modules.md` |
| `dspy.ProgramOfThought` | Generates Python code to solve the task | `02-modules.md` |
| `dspy.Module` | Base class for composing multi-step programs | `02-modules.md` |
| `dspy.LM` | Unified LM client (OpenAI, Anthropic, Ollama, vLLM, HF) | `03-lm-configuration.md` |
| `dspy.Retrieve` | Retrieval module (ColBERT, vector DBs) | `06-rag-retrieval.md` |
| `dspy.Example` | Typed example row — used for training & eval | `05-metrics-evaluation.md` |
| `dspy.Evaluate` | Runs a metric over a devset | `05-metrics-evaluation.md` |
| `dspy.teleprompt.*` | Optimizers (a.k.a. teleprompters / compilers) | `04-optimizers.md` |
| `dspy.Assert` / `dspy.Suggest` | Runtime constraints with auto-retry | `07-assertions.md` |

## The compile loop (mental model)

DSPy pipelines go through three phases:

1. **Define** — write modules with signatures. At this stage the prompts are generic defaults.
2. **Compile** — run an optimizer against a trainset + metric. The optimizer mutates the internal prompt state (few-shot demos, sometimes the instruction) and picks the best version.
3. **Save & load** — the compiled program is just a JSON state file; load it in production and call it like any other Python function.

```python
compiled.save("qa_compiled.json")

# Later, in prod:
program = dspy.ChainOfThought(GenerateAnswer)
program.load("qa_compiled.json")
program(question="...")
```

See `08-deployment.md` for serving patterns.

## Typical pipeline structure

```python
class RAGPipeline(dspy.Module):
    def __init__(self, num_passages: int = 3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question: str) -> dspy.Prediction:
        passages = self.retrieve(question).passages
        context = "\n\n".join(passages)
        return self.generate(context=context, question=question)
```

This is idiomatic DSPy: submodules in `__init__`, orchestration in `forward`. You can then `compile` the *whole* pipeline end-to-end — the optimizer will tune demos for each inner module.

## Common pitfalls

- **Forgetting `.with_inputs(...)` on `dspy.Example`** — without it, DSPy doesn't know which fields are inputs vs labels, and optimizers will silently treat your labels as inputs.
- **Using a metric that returns `None` for most examples** — optimizers need *positive* signal to bootstrap demos. If your metric is too strict, `BootstrapFewShot` won't find any good traces.
- **Compiling a huge pipeline on a huge trainset with MIPROv2** — it is expensive. Start with `BootstrapFewShot` on a small trainset, move to MIPROv2 only after the pipeline is stable.
- **Calling `dspy.configure(lm=...)` inside a request handler** — it mutates global state. Configure once at startup.
- **Mixing Signatures across modules expecting different output fields** — `ChainOfThought` injects a `rationale` field; your downstream consumer must accept it.
- **Shipping an uncompiled program to production** — the default prompts are fine for prototypes but leave a lot of quality on the table. Always compile before shipping.

## Related topics

- **Optimizers and when to pick which one:** `04-optimizers.md`
- **Writing a good metric:** `05-metrics-evaluation.md`
- **Production deployment, saving/loading, async, streaming:** `08-deployment.md`
- **Multi-hop RAG patterns:** `06-rag-retrieval.md`
