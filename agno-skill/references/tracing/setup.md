# Tracing Setup

Configure and enable tracing for Agno agents, teams, and workflows.

## Installation

```bash
uv pip install -U opentelemetry-api opentelemetry-sdk openinference-instrumentation-agno
```

## Two Ways to Enable Tracing

| Method | When to Use |
|--------|-------------|
| `setup_tracing(db=db)` | SDK usage (standalone scripts) |
| `AgentOS(tracing=True, db=db)` | AgentOS deployment |

---

## Option 1: Using `setup_tracing()` (SDK)

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.tracing import setup_tracing

# Set up tracing database
db = SqliteDb(db_file="tmp/traces.db")

# Enable tracing — call ONCE at startup
setup_tracing(db=db)

# Create and run agents — automatically traced!
agent = Agent(
    name="Research Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="You are a research assistant",
)

response = agent.run("What is quantum computing?")
```

### setup_tracing() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `BaseDb` | Required | Database for storing traces |
| `batch_processing` | `bool` | `False` | Enable batch processing mode |
| `max_queue_size` | `int` | `2048` | Max traces in memory (batch mode) |
| `max_export_batch_size` | `int` | `512` | Traces per batch write (batch mode) |
| `schedule_delay_millis` | `int` | `5000` | Export interval in ms (batch mode) |

## Option 2: Using AgentOS

```python
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/traces.db")

agent_os = AgentOS(
    agents=[my_agent],
    tracing=True,  # Enable tracing
    db=db,
)

app = agent_os.get_app()
```

### AgentOS Database Configuration

| Scenario | Configuration | Where Traces Are Stored |
|----------|---------------|------------------------|
| Single shared database | `tracing=True` | The shared `db` |
| Multiple databases | `tracing=True` + `db=...` | The dedicated `db` |
| No `db` specified | `tracing=True` | First database found (not recommended) |

### AgentOS with setup_tracing() (Advanced)

You can combine both for custom configuration:

```python
from agno.tracing import setup_tracing

db = SqliteDb(db_file="tmp/traces.db")

setup_tracing(
    db=db,
    batch_processing=True,
    max_queue_size=2048,
    schedule_delay_millis=3000,
)

agent_os = AgentOS(
    agents=[agent1, agent2],
    db=db,  # Makes traces queryable via AgentOS API
)
```

---

## Dedicated Tracing Database

When agents have their own databases for sessions/memory, use a separate tracing database:

```python
from agno.db.sqlite import SqliteDb
from agno.tracing import setup_tracing

# Each agent has its own database for sessions/memory
agent1_db = SqliteDb(db_file="tmp/agent1.db", id="agent1_db")
agent2_db = SqliteDb(db_file="tmp/agent2.db", id="agent2_db")

# Dedicated database for ALL traces
traces_db = SqliteDb(db_file="tmp/traces.db", id="traces_db")

# Enable tracing to the dedicated database
setup_tracing(
    db=traces_db,
    batch_processing=True,
    max_queue_size=1024,
    max_export_batch_size=256,
)

# Agents use their own databases
hackernews_agent = Agent(
    name="HackerNews Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    db=agent1_db,
)

search_agent = Agent(
    name="Web Search Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    db=agent2_db,
)

# Both agents are traced to the same traces_db
hackernews_agent.run("What's trending on HackerNews?")
search_agent.run("Latest AI news")

# Query traces from one place
traces, count = traces_db.get_traces(limit=20)
print(f"Found {count} traces across all agents")
```

**Database tables created:** `agno_traces` and `agno_spans`.

---

## Processing Modes

### Batch Processing (Production)

```python
setup_tracing(
    db=db,
    batch_processing=True,
    max_queue_size=2048,
    max_export_batch_size=512,
    schedule_delay_millis=5000,  # Export every 5 seconds
)
```

### Simple Processing (Default, Development)

```python
setup_tracing(db=db, batch_processing=False)
```

---

## Agent Tracing Example

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools
from agno.tracing import setup_tracing

db = SqliteDb(db_file="tmp/traces.db")
setup_tracing(db=db)

agent = Agent(
    name="HackerNews Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    instructions="You are a hacker news agent. Answer questions concisely.",
    markdown=True,
    db=db,
)

agent.print_response("What's trending on HackerNews?")

# Query traces
traces, count = db.get_traces(agent_id=agent.id, limit=10)
print(f"\nFound {count} traces for agent '{agent.name}'")
for trace in traces:
    print(f"  - {trace.name}: {trace.duration_ms}ms ({trace.status})")
```

## Team Tracing Example

```python
from agno.team import Team
from agno.tracing import setup_tracing

db = SqliteDb(db_file="tmp/traces.db")
setup_tracing(db=db)

hackernews_agent = Agent(
    name="HackerNews Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    markdown=True,
)

team = Team(
    name="HackerNews Team",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[hackernews_agent],
    instructions="Use the HackerNews Agent to answer questions.",
    db=db,
)

team.print_response("What's trending on HackerNews?")

# Query team traces
traces, count = db.get_traces(team_id=team.id, limit=10)
```

**Note:** No need to set tracing on each member agent — `setup_tracing()` instruments all agents globally.

## Workflow Tracing Example

```python
from agno.workflow.workflow import Workflow
from agno.workflow.step import Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput

db = SqliteDb(db_file="tmp/traces.db")

researcher = Agent(name="Researcher", instructions="Research the topic.", tools=[HackerNewsTools()])
summarizer = Agent(name="Summarizer", instructions="Summarize the research findings.")
writer = Agent(name="Writer", instructions="Write a comprehensive article.")

def needs_fact_checking(step_input: StepInput) -> bool:
    return True

workflow = Workflow(
    name="Research Workflow",
    db=db,
    steps=[
        Step(name="research", agent=researcher),
        Step(name="summarize", agent=summarizer),
        Condition(
            name="fact_check_condition",
            evaluator=needs_fact_checking,
            steps=[Step(name="fact_check", agent=Agent(name="Fact Checker", tools=[HackerNewsTools()]))],
        ),
        Step(name="write_article", agent=writer),
    ],
)

workflow.print_response("Write an article on AI agents?")

# Query workflow traces
traces, count = db.get_traces(workflow_id=workflow.id, limit=10)
```
