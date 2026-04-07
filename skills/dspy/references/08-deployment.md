# DSPy — Deployment & Production

> Source: https://dspy.ai/tutorials/deployment — Written for DSPy v2.5.x

## Overview

A DSPy program is ultimately a plain Python object with:

1. Source code (the `dspy.Module` subclass and its signatures).
2. A JSON state file produced by `compile(...).save(...)` (instructions, demos, field configs).
3. Runtime LM credentials (never persisted).

Deploying means shipping the code + state file and configuring the LM at startup. There's no special runtime — it works in any Python process: FastAPI, Lambda, Modal, Ray Serve, a cron job, etc.

## Saving and loading compiled programs

```python
# Offline: after compile
compiled.save("programs/qa.json")

# Online: in the service
import dspy
from myapp.programs import QAProgram   # the class you wrote

program = QAProgram()
program.load("programs/qa.json")
```

What's in the state file:
- The optimised instructions for each signature.
- The selected few-shot demos.
- Field and type configuration.

What's **not** in the state file:
- LM credentials / API keys.
- The Python code of your module.
- External resources (retrievers, tools).

You must import and re-construct the module class, then call `.load(...)` to hydrate state.

### Saving the whole program class

If you want a self-contained artefact (class code + state), use `dspy.save` / `dspy.load`:

```python
import dspy

dspy.save(compiled, "programs/qa")    # writes a directory with code + state
# later:
program = dspy.load("programs/qa")
```

This uses `cloudpickle` and is slower but requires no class import on the consumer side.

## Minimal FastAPI service

```python
# main.py
import os
import dspy
from fastapi import FastAPI
from pydantic import BaseModel

# 1. Configure LM once at startup
dspy.configure(
    lm=dspy.LM(
        "openai/gpt-4o-mini",
        api_key=os.environ["OPENAI_API_KEY"],
        cache=False,            # disable cache in prod if you want fresh answers
    ),
)

# 2. Load the compiled program
from myapp.programs import QAProgram
program = QAProgram()
program.load("programs/qa.json")

app = FastAPI()

class Query(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str
    rationale: str | None = None

@app.post("/ask", response_model=Answer)
async def ask(q: Query) -> Answer:
    pred = await program.acall(question=q.question)
    return Answer(
        answer=pred.answer,
        rationale=getattr(pred, "rationale", None),
    )
```

Run with `uvicorn main:app --host 0.0.0.0 --port 8000`.

## Async and concurrency

Recent DSPy versions expose `acall` on every module, which issues the LM requests asynchronously. Prefer it in async servers so you don't block the event loop.

```python
@app.post("/ask")
async def ask(q: Query):
    return await program.acall(question=q.question)
```

For batch workloads, use `asyncio.gather` but respect provider rate limits — or use `dspy.Evaluate` which already parallelises with `num_threads`.

## Streaming

DSPy supports streaming responses by delegating to the underlying LM's stream interface. The common pattern is to use a `dspy.Predict` directly (streaming requires a single LM call; multi-step modules don't stream).

```python
import dspy

lm = dspy.LM("openai/gpt-4o-mini", stream=True)
dspy.configure(lm=lm)

predict = dspy.Predict("question -> answer")

# Yields incremental deltas
async for chunk in predict.astream(question="Explain DSPy"):
    print(chunk, end="", flush=True)
```

For FastAPI Server-Sent Events:

```python
from fastapi.responses import StreamingResponse

@app.post("/stream")
async def stream(q: Query):
    async def gen():
        async for chunk in predict.astream(question=q.question):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

## Observability

Every module stores its recent calls in `lm.history`. Structured observability typically means plugging in a callback-based tracer.

### Langfuse

```python
from langfuse.decorators import observe

@observe()
async def answer_question(question: str):
    return await program.acall(question=question)
```

Langfuse autoinstruments LiteLLM (which DSPy uses under the hood), so you get a span per LM call automatically.

### OpenTelemetry

Wrap each request handler in a span and add the model, prompt length, and metric score as attributes:

```python
from opentelemetry import trace
tracer = trace.get_tracer("dspy-service")

@app.post("/ask")
async def ask(q: Query):
    with tracer.start_as_current_span("ask") as span:
        span.set_attribute("input.question", q.question)
        pred = await program.acall(question=q.question)
        span.set_attribute("output.length", len(pred.answer))
        return {"answer": pred.answer}
```

### Logging LM calls

During debugging, `lm.inspect_history(n=5)` prints the last 5 calls with full prompts and responses. Very useful in a Jupyter-style prod debug session. Disable the LM cache (`cache=False`) before relying on historical counts in production.

## Versioning compiled programs

Treat `programs/qa.json` like a model weight file:

- Store it in object storage (S3/GCS) keyed by commit hash or semantic version.
- Load the version at service startup from `os.environ["PROGRAM_VERSION"]`.
- Keep a *baseline* version in the repo so rollbacks are trivial.

```python
version = os.environ.get("PROGRAM_VERSION", "baseline")
program.load(f"programs/qa-{version}.json")
```

Run A/B tests by loading two versions side-by-side and routing by request header.

## Cost and rate-limit hardening

For each external LM call:
- Set `num_retries` on `dspy.LM` (default 3) for transient 5xx errors.
- Add a short `timeout=` to prevent hanging requests.
- Wrap compile-time calls in a semaphore to respect TPM limits.
- Pre-compute and cache embeddings for retrieval — don't embed on the hot path.

For end-to-end budgets, expose a per-request spend metric using `lm.history[-1]["usage"]` or LiteLLM's cost helpers.

## Containerising

Dockerfile skeleton:

```dockerfile
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir 'dspy' 'fastapi' 'uvicorn'

COPY main.py ./
COPY myapp ./myapp
COPY programs ./programs

ENV OPENAI_API_KEY=""
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build once, deploy anywhere. Mount the compiled programs via a volume or bake them into the image (small JSON files, so baking is fine).

## Testing compiled programs

Lock your compile step behind a CI job that asserts the dev-set score doesn't regress:

```python
def test_qa_quality():
    program = QAProgram()
    program.load("programs/qa.json")
    evaluator = dspy.Evaluate(devset=dev, metric=exact_match, num_threads=4)
    score = evaluator(program)
    assert score >= 0.65, f"regression: {score:.3f} < 0.65"
```

Run this in CI whenever the compiled JSON changes.

## Common pitfalls

- **Loading state into the wrong module class.** Shapes must match — if you changed a signature field, `.load` will raise. Version the module class alongside the state.
- **Calling `dspy.configure` inside a request handler.** It mutates global thread-local state; configure once at startup.
- **Embedding API keys in the saved JSON.** They're not persisted by default — good — but don't add them to the state dict manually either.
- **Shipping an uncompiled program.** Default prompts are fine for prototypes, but you're leaving ~10-30% quality on the table. Always compile before deploy.
- **Relying on `cache=True` in prod.** On-disk cache leaks memory and can return stale results after a prompt change. Turn it off and use an explicit Redis-backed cache if you need one.
- **Forgetting to pin the DSPy version.** Optimizer output formats evolve — pin `dspy==X.Y.Z` and re-compile when upgrading.

## Related topics

- **Compiling the program you're about to deploy:** `04-optimizers.md`
- **Evaluating before shipping:** `05-metrics-evaluation.md`
- **LM configuration (providers, caching, retries):** `03-lm-configuration.md`
- **Runtime constraints via Assert/Suggest:** `07-assertions.md`
