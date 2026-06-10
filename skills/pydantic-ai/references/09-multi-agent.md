# Multi-Agent Patterns

> Source: [pydantic.dev/docs/ai/multi-agent](https://pydantic.dev/docs/ai/multi-agent/)

## Table of Contents

- [Overview](#overview)
- [Agent Delegation](#agent-delegation)
- [Programmatic Handoff](#programmatic-handoff)
- [Agent as Tool](#agent-as-tool)
- [Parallel Agent Execution](#parallel-agent-execution)
- [Shared Dependencies](#shared-dependencies)
- [Usage Tracking Across Agents](#usage-tracking-across-agents)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic AI supports two primary multi-agent patterns:

1. **Agent Delegation** — one agent calls another as a tool, with the sub-agent's result returned to the calling model
2. **Programmatic Handoff** — application code calls multiple agents in sequence, deciding which agent to invoke next

Both patterns maintain type safety through the dependency and output type system.

## Agent Delegation

A parent agent delegates tasks to specialized sub-agents by wrapping them as tools:

```python
from pydantic_ai import Agent, RunContext

# Specialist agents
research_agent = Agent(
    'openai:gpt-5.2',
    instructions='You are a research specialist. Provide detailed factual answers.',
    output_type=str,
)

math_agent = Agent(
    'openai:gpt-5.2',
    instructions='You are a math specialist. Solve problems step by step.',
    output_type=str,
)

# Orchestrator agent
orchestrator = Agent(
    'openai:gpt-5.2',
    instructions='Route tasks to the appropriate specialist.',
)

@orchestrator.tool_plain
async def delegate_research(query: str) -> str:
    """Delegate a research question to the research specialist."""
    result = await research_agent.run(query)
    return result.output

@orchestrator.tool_plain
async def delegate_math(problem: str) -> str:
    """Delegate a math problem to the math specialist."""
    result = await math_agent.run(problem)
    return result.output
```

### Delegation With Shared Dependencies

When both parent and child agents need the same dependencies:

```python
from dataclasses import dataclass
import httpx

@dataclass
class AppDeps:
    http_client: httpx.AsyncClient

research_agent = Agent('openai:gpt-5.2', deps_type=AppDeps)

@research_agent.tool
async def web_lookup(ctx: RunContext[AppDeps], url: str) -> str:
    """Fetch content from a URL."""
    resp = await ctx.deps.http_client.get(url)
    return resp.text

orchestrator = Agent('openai:gpt-5.2', deps_type=AppDeps)

@orchestrator.tool
async def research(ctx: RunContext[AppDeps], query: str) -> str:
    """Research a topic using the research agent."""
    result = await research_agent.run(query, deps=ctx.deps)
    return result.output
```

## Programmatic Handoff

Application code controls which agent runs next — useful for multi-step workflows:

```python
from pydantic import BaseModel

class TriageResult(BaseModel):
    category: str
    priority: int
    summary: str

triage_agent = Agent(
    'openai:gpt-5-mini',
    output_type=TriageResult,
    instructions='Categorize and prioritize the support ticket.',
)

resolution_agent = Agent(
    'openai:gpt-5.2',
    instructions='Resolve the support ticket based on category.',
)

async def handle_ticket(ticket: str) -> str:
    # Step 1: Triage
    triage = await triage_agent.run(ticket)
    category = triage.output.category

    # Step 2: Route to specialist
    if category == 'billing':
        result = await billing_agent.run(
            f'Resolve billing issue: {triage.output.summary}'
        )
    elif category == 'technical':
        result = await tech_agent.run(
            f'Resolve technical issue: {triage.output.summary}'
        )
    else:
        result = await general_agent.run(ticket)

    return result.output
```

### Handoff With Message History

Pass conversation context between agents:

```python
async def multi_turn_handoff():
    # Agent 1 gathers information
    result1 = await intake_agent.run('Customer has billing issue')

    # Agent 2 continues with context
    result2 = await billing_agent.run(
        'Resolve this billing issue',
        message_history=result1.all_messages(),
    )
    return result2.output
```

## Agent as Tool

Wrap an agent so it appears as a single tool to a parent agent:

```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    summary: str

search_agent = Agent(
    'openai:gpt-5.2',
    output_type=list[SearchResult],
    instructions='Search for information and return structured results.',
)

main_agent = Agent('openai:gpt-5.2')

@main_agent.tool_plain
async def search(query: str) -> list[dict]:
    """Search for information on a topic."""
    result = await search_agent.run(query)
    return [r.model_dump() for r in result.output]
```

## Parallel Agent Execution

Run multiple agents concurrently with `asyncio.gather`:

```python
import asyncio

async def parallel_analysis(text: str) -> dict:
    sentiment_task = sentiment_agent.run(text)
    summary_task = summary_agent.run(text)
    entities_task = entities_agent.run(text)

    sentiment, summary, entities = await asyncio.gather(
        sentiment_task, summary_task, entities_task
    )

    return {
        'sentiment': sentiment.output,
        'summary': summary.output,
        'entities': entities.output,
    }
```

### Parallel With Error Handling

```python
async def safe_parallel(text: str) -> dict:
    results = await asyncio.gather(
        sentiment_agent.run(text),
        summary_agent.run(text),
        return_exceptions=True,
    )

    return {
        'sentiment': results[0].output if not isinstance(results[0], Exception) else None,
        'summary': results[1].output if not isinstance(results[1], Exception) else None,
    }
```

## Shared Dependencies

Multiple agents can share the same dependency type for consistent access:

```python
@dataclass
class SharedDeps:
    db: Database
    cache: Cache
    http: httpx.AsyncClient

agent_a = Agent('openai:gpt-5.2', deps_type=SharedDeps)
agent_b = Agent('anthropic:claude-sonnet-4-6', deps_type=SharedDeps)

async def workflow(prompt: str, deps: SharedDeps):
    result_a = await agent_a.run(prompt, deps=deps)
    result_b = await agent_b.run(
        f'Verify: {result_a.output}',
        deps=deps,
    )
    return result_b.output
```

## Usage Tracking Across Agents

Track total token usage across a multi-agent workflow:

```python
from pydantic_ai import Usage

async def tracked_workflow(prompt: str) -> tuple[str, Usage]:
    total_usage = Usage()

    result1 = await agent_a.run(prompt)
    total_usage += result1.usage()

    result2 = await agent_b.run(result1.output)
    total_usage += result2.usage()

    return result2.output, total_usage
```

## Common Pitfalls

- **Circular delegation** — agent A calls agent B which calls agent A; use explicit tools or instructions to prevent recursion
- **Dependency type mismatch** — sub-agents may need different dependency types; map dependencies explicitly when delegating
- **Usage limits** — `usage_limits` only apply to a single agent run; track usage manually across agents
- **Message history compatibility** — different agents may produce incompatible message formats; only share history between agents using the same model
- **Concurrency limits** — parallel agent execution can hit API rate limits; use `ConcurrencyLimitedModel` or limit concurrency

## Related

- `01-agents.md` — Agent creation and run methods
- `02-dependencies.md` — Dependency injection
- `08-models.md` — Model configuration and fallbacks
