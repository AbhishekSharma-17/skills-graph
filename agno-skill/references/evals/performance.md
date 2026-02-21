# Performance Evals

Measure the latency and memory footprint of an Agent or Team.

## How It Works

1. Wrap your agent/team execution in a function
2. Pass the function to `PerformanceEval`
3. The eval runs it `num_iterations` times (with optional warmup)
4. Reports runtime (seconds) and memory usage per iteration

**Requires:** `pip install memory_profiler`

## PerformanceEval Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `Optional[str]` | Name for this evaluation |
| `func` | `Callable` | Function to benchmark (must return something) |
| `num_iterations` | `int` | Number of times to run (default: 1) |
| `warmup_runs` | `int` | Warmup iterations before measuring (default: 0) |
| `measure_runtime` | `bool` | Measure execution time (default: True) |
| `memory_growth_tracking` | `bool` | Track memory growth across iterations (default: False) |
| `debug_mode` | `bool` | Enable detailed logging (default: False) |
| `db` | `Optional[BaseDb]` | Database for persisting results |

## Basic Example — Agent Response

```python
from agno.agent import Agent
from agno.eval.performance import PerformanceEval
from agno.models.openai import OpenAIResponses

def run_agent():
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        system_message="Be concise, reply with one sentence.",
    )
    response = agent.run("What is the capital of France?")
    return response

simple_response_perf = PerformanceEval(
    name="Simple Performance Evaluation",
    func=run_agent,
    num_iterations=1,
    warmup_runs=0,
)

simple_response_perf.run(print_results=True, print_summary=True)
```

## Tool Usage Performance

Compare how tools affect agent performance:

```python
from typing import Literal

def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"

def instantiate_agent():
    return Agent(model=OpenAIResponses(id="gpt-5.2"), tools=[get_weather])

instantiation_perf = PerformanceEval(
    name="Tool Instantiation Performance",
    func=instantiate_agent,
    num_iterations=1000,
)

instantiation_perf.run(print_results=True, print_summary=True)
```

## Agent Instantiation Performance

Measure how fast agents are created (no API calls):

```python
def instantiate_agent():
    return Agent(system_message="Be concise, reply with one sentence.")

instantiation_perf = PerformanceEval(
    name="Instantiation Performance",
    func=instantiate_agent,
    num_iterations=1000,
)
```

## Team Instantiation Performance

```python
from agno.team import Team

team_member = Agent(model=OpenAIResponses(id="gpt-5.2"))

def instantiate_team():
    return Team(members=[team_member])

instantiation_perf = PerformanceEval(
    name="Instantiation Performance Team",
    func=instantiate_team,
    num_iterations=1000,
)
```

## Memory Updates Performance

Test impact of memory updates on agent performance:

```python
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/memory.db")

def run_agent():
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        system_message="Be concise, reply with one sentence.",
        db=db,
        update_memory_on_run=True,
    )
    response = agent.run("My name is Tom! I'm 25 years old and I live in New York.")
    return response

response_with_memory_updates_perf = PerformanceEval(
    name="Memory Updates Performance",
    func=run_agent,
    num_iterations=5,
    warmup_runs=0,
)
```

## Storage Performance

Test impact of chat history storage:

```python
db = SqliteDb(db_file="tmp/storage.db")

def run_agent():
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        system_message="Be concise, reply with one sentence.",
        add_history_to_context=True,
        db=db,
    )
    response_1 = agent.run("What is the capital of France?")
    response_2 = agent.run("How many people live there?")
    return response_2.content

response_with_storage_perf = PerformanceEval(
    name="Storage Performance",
    func=run_agent,
    num_iterations=1,
    warmup_runs=0,
)
```

## Team Memory Growth Tracking

Track memory growth across iterations with `memory_growth_tracking=True`:

```python
import asyncio
from agno.eval.performance import PerformanceEval

async def run_team():
    random_city = random.choice(cities)
    _ = team.arun(input=f"What weather in {random_city}?", stream=True, stream_events=True)
    return "Successfully ran team"

team_response_with_memory_impact = PerformanceEval(
    name="Team Memory Impact",
    func=run_team,
    num_iterations=5,
    warmup_runs=0,
    measure_runtime=False,
    debug_mode=True,
    memory_growth_tracking=True,
)

asyncio.run(team_response_with_memory_impact.arun(print_results=True, print_summary=True))
```

## Async Support

For async functions, use `arun()`:

```python
async def arun_agent():
    agent = Agent(model=OpenAIResponses(id="gpt-5.2"), system_message="Be concise.")
    response = await agent.arun("What is the capital of France?")
    return response

performance_eval = PerformanceEval(func=arun_agent, num_iterations=10)
asyncio.run(performance_eval.arun(print_summary=True, print_results=True))
```

## Database Logging

Persist results to a database:

```python
from agno.db.postgres.postgres import PostgresDb

db_url = "postgresql+psycopg://ai:ai@localhost:5432/ai"
db = PostgresDb(db_url=db_url, eval_table="eval_runs_cookbook")

simple_response_perf = PerformanceEval(
    db=db,
    name="Simple Performance Evaluation",
    func=run_agent,
    num_iterations=1,
    warmup_runs=0,
)
```

## Methods

| Method | Description |
|--------|-------------|
| `run(print_results=False, print_summary=False)` | Run synchronously |
| `arun(print_results=False, print_summary=False)` | Run asynchronously (for async functions) |

## Key Imports

```python
from agno.eval.performance import PerformanceEval
```

## Install

```bash
uv pip install -U agno memory_profiler
```
