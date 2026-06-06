# Workflows

> Source: [developers.llamaindex.ai — Workflows](https://developers.llamaindex.ai/python/framework/understanding/workflows/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Basic Workflow](#basic-workflow)
- [Events](#events)
- [Steps](#steps)
- [Control Flow](#control-flow)
- [State Management](#state-management)
- [Parallel Execution](#parallel-execution)
- [Streaming Events](#streaming-events)
- [Error Handling](#error-handling)
- [Deployment](#deployment)
- [Common Patterns](#common-patterns)

## Overview

A Workflow is an event-driven, step-based execution system for building complex LLM applications. Unlike DAGs, workflows support loops, branches, and dynamic control flow expressed naturally in code.

Key advantages over simple DAGs:
- Loops and conditional branching in step code
- Simpler data passing between steps via typed events
- Arbitrary logic inside steps (LLM calls, API calls, agent execution)
- First-class async support

```
StartEvent → Step A → CustomEvent → Step B → StopEvent
                ↑                        ↓
                └────── LoopEvent ────────┘
```

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Event** | Pydantic object that carries data between steps |
| **Step** | Method decorated with `@step` that processes events |
| **Workflow** | Class that contains steps and manages execution |
| **StartEvent** | Built-in event that initiates the workflow |
| **StopEvent** | Built-in event that terminates the workflow |
| **Context** | Shared state accessible across all steps |

## Basic Workflow

```python
from llama_index.core.workflow import Workflow, step, Event, StartEvent, StopEvent
from llama_index.llms.openai import OpenAI

class JokeEvent(Event):
    joke: str

class JokeFlow(Workflow):
    llm = OpenAI(model="gpt-4o")

    @step
    async def generate_joke(self, ev: StartEvent) -> JokeEvent:
        topic = ev.topic
        response = await self.llm.acomplete(
            f"Write a short joke about {topic}."
        )
        return JokeEvent(joke=str(response))

    @step
    async def critique_joke(self, ev: JokeEvent) -> StopEvent:
        response = await self.llm.acomplete(
            f"Rate this joke (1-10) and explain:\n{ev.joke}"
        )
        return StopEvent(result=str(response))

async def main():
    flow = JokeFlow(timeout=60, verbose=False)
    result = await flow.run(topic="programming")
    print(result)

import asyncio
asyncio.run(main())
```

How execution works:
1. `flow.run(topic="programming")` creates a `StartEvent` with `topic` attribute
2. `generate_joke` handles `StartEvent`, emits `JokeEvent`
3. `critique_joke` handles `JokeEvent`, emits `StopEvent`
4. `StopEvent.result` is returned from `flow.run()`

## Events

Events are Pydantic models that carry typed data between steps:

```python
from llama_index.core.workflow import Event

class ResearchEvent(Event):
    query: str
    sources: list[str] = []

class AnalysisEvent(Event):
    findings: str
    confidence: float

class ReportEvent(Event):
    title: str
    body: str
    citations: list[str]
```

Built-in events:
- `StartEvent` — Accepts arbitrary kwargs from `workflow.run()`
- `StopEvent` — Has a `result` attribute returned to the caller

## Steps

Steps are async methods decorated with `@step`:

```python
class MyWorkflow(Workflow):
    @step
    async def process(self, ev: StartEvent) -> CustomEvent:
        data = ev.input_data
        result = await some_async_operation(data)
        return CustomEvent(output=result)
```

Type annotations are enforced:
- Input type determines which events the step handles
- Return type determines which events the step emits
- The framework validates the entire event graph at initialization

### Multiple Input Events

A step can wait for multiple events before proceeding:

```python
@step
async def combine(
    self, ctx: Context, ev: ResearchEvent | AnalysisEvent
) -> StopEvent:
    result = ctx.collect_events(ev, [ResearchEvent, AnalysisEvent])
    if result is None:
        return None  # Still waiting for other events
    research, analysis = result
    return StopEvent(result=f"{research.query}: {analysis.findings}")
```

## Control Flow

### Branching

```python
class BranchEvent(Event):
    query: str
    category: str

@step
async def classify(self, ev: StartEvent) -> BranchEvent:
    category = await self.llm.acomplete(
        f"Classify as 'technical' or 'general': {ev.query}"
    )
    return BranchEvent(query=ev.query, category=str(category).strip())

@step
async def handle_technical(self, ev: BranchEvent) -> StopEvent | None:
    if ev.category != "technical":
        return None
    result = await self.technical_engine.aquery(ev.query)
    return StopEvent(result=str(result))

@step
async def handle_general(self, ev: BranchEvent) -> StopEvent | None:
    if ev.category != "general":
        return None
    result = await self.general_engine.aquery(ev.query)
    return StopEvent(result=str(result))
```

### Looping

```python
class RefineEvent(Event):
    draft: str
    iteration: int

@step
async def write_draft(self, ev: StartEvent) -> RefineEvent:
    draft = await self.llm.acomplete(f"Write about: {ev.topic}")
    return RefineEvent(draft=str(draft), iteration=0)

@step
async def refine(self, ev: RefineEvent) -> RefineEvent | StopEvent:
    if ev.iteration >= 3:
        return StopEvent(result=ev.draft)
    
    improved = await self.llm.acomplete(
        f"Improve this draft:\n{ev.draft}"
    )
    return RefineEvent(draft=str(improved), iteration=ev.iteration + 1)
```

## State Management

Use `Context` for shared state across steps:

```python
from llama_index.core.workflow import Context

class StatefulWorkflow(Workflow):
    @step
    async def step_one(self, ctx: Context, ev: StartEvent) -> NextEvent:
        await ctx.set("counter", 0)
        await ctx.set("items", [])
        return NextEvent(data=ev.input)

    @step
    async def step_two(self, ctx: Context, ev: NextEvent) -> StopEvent:
        counter = await ctx.get("counter")
        items = await ctx.get("items")
        items.append(ev.data)
        await ctx.set("items", items)
        await ctx.set("counter", counter + 1)
        return StopEvent(result=f"Processed {counter + 1} items")
```

## Parallel Execution

Emit multiple events to trigger parallel step execution:

```python
@step
async def fan_out(self, ctx: Context, ev: StartEvent) -> SearchEvent:
    ctx.send_event(SearchEvent(query="topic A"))
    ctx.send_event(SearchEvent(query="topic B"))
    ctx.send_event(SearchEvent(query="topic C"))
    return None

@step
async def search(self, ev: SearchEvent) -> ResultEvent:
    result = await self.search_engine.aquery(ev.query)
    return ResultEvent(result=str(result))

@step
async def aggregate(self, ctx: Context, ev: ResultEvent) -> StopEvent:
    results = ctx.collect_events(ev, [ResultEvent] * 3)
    if results is None:
        return None
    combined = "\n".join(r.result for r in results)
    return StopEvent(result=combined)
```

## Streaming Events

Stream events to the user during workflow execution:

```python
handler = workflow.run(input="my query")

async for event in handler.stream_events():
    if isinstance(event, ProgressEvent):
        print(f"Progress: {event.message}")
    elif isinstance(event, ResultEvent):
        print(f"Result: {event.result}")

final_result = await handler
```

## Error Handling

```python
class ErrorWorkflow(Workflow):
    @step
    async def risky_step(self, ev: StartEvent) -> StopEvent:
        try:
            result = await self.external_api.call(ev.query)
            return StopEvent(result=result)
        except TimeoutError:
            return StopEvent(result="Service temporarily unavailable")
```

Workflow-level timeout:

```python
workflow = MyWorkflow(timeout=120)  # seconds
```

## Deployment

Run a workflow as a server:

```python
from llama_index.core.workflow import deploy_workflow

deploy_workflow(MyWorkflow, host="0.0.0.0", port=8000)
```

Call from a client:

```python
from llama_index.core.workflow import WorkflowClient

client = WorkflowClient("http://localhost:8000")
result = await client.run(input="my query")
```

## Common Patterns

### RAG Workflow

```python
class RAGWorkflow(Workflow):
    @step
    async def retrieve(self, ev: StartEvent) -> RetrieveEvent:
        nodes = await self.retriever.aretrieve(ev.query)
        return RetrieveEvent(nodes=nodes)

    @step
    async def synthesize(self, ev: RetrieveEvent) -> StopEvent:
        response = await self.synthesizer.asynthesize(
            query=ev.query, nodes=ev.nodes
        )
        return StopEvent(result=str(response))
```

### Multi-Step Processing

```python
class PipelineWorkflow(Workflow):
    @step
    async def extract(self, ev: StartEvent) -> TransformEvent:
        ...
    @step
    async def transform(self, ev: TransformEvent) -> LoadEvent:
        ...
    @step
    async def load(self, ev: LoadEvent) -> StopEvent:
        ...
```
