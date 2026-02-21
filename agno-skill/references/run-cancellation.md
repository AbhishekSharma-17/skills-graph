# Run Cancellation

Cancel running agent, team, or workflow executions gracefully.

## Docs Hierarchy

```
Run Cancellation
├── Overview                    ← this file
├── Cancel Agent Run            ← Agent section below
├── Cancel Team Run             ← Team section below
└── Cancel Workflow Run         ← Workflow section below
```

## How It Works

`cancel_run(run_id)` marks a run for cancellation. Execution stops gracefully once the current step completes — no resources left in an inconsistent state.

| Run Mode | Cancellation Behavior |
|----------|----------------------|
| **Non-streaming** | `RunOutput` returned with `status = RunStatus.cancelled` |
| **Streaming** | A `RunCancelledEvent` is emitted when cancellation occurs |

## Common Pattern (All Types)

1. Start a run in a **separate thread** (streaming)
2. Capture the `run_id` from the first chunk
3. Call `cancel_run(run_id)` from another thread
4. Handle the cancellation event in the streaming loop

## Key Imports

```python
from agno.run.base import RunStatus
from agno.run.agent import RunEvent           # Agent cancellation events
from agno.run.team import TeamRunEvent        # Team cancellation events
from agno.run.workflow import WorkflowRunEvent  # Workflow cancellation events
```

## Cancellation Events

| Entity | Content Event | Cancelled Event |
|--------|--------------|-----------------|
| **Agent** | `RunEvent.run_content` | `RunEvent.run_cancelled` |
| **Team** | `TeamRunEvent.run_content` / `RunEvent.run_content` | `TeamRunEvent.run_cancelled` / `RunEvent.run_cancelled` |
| **Workflow** | `RunEvent.run_content` | `WorkflowRunEvent.workflow_cancelled` / `RunEvent.run_cancelled` |

---

## Agent Run Cancellation

### cancel_run() Method

```python
success: bool = agent.cancel_run(run_id)
```

Returns `True` if marked for cancellation, `False` if run not found or already completed.

### Streaming Example

```python
import threading
import time

from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunEvent
from agno.run.base import RunStatus

agent = Agent(
    name="StorytellerAgent",
    model=OpenAIResponses(id="gpt-5.2"),
    description="An agent that writes detailed stories",
)

run_id_container = {}

def long_running_task():
    content_pieces = []
    for chunk in agent.run(
        "Write a very long story about a dragon who learns to code.",
        stream=True,
    ):
        if "run_id" not in run_id_container and chunk.run_id:
            run_id_container["run_id"] = chunk.run_id

        if chunk.event == RunEvent.run_content:
            print(chunk.content, end="", flush=True)
            content_pieces.append(chunk.content)
        elif chunk.event == RunEvent.run_cancelled:
            print(f"\nRun was cancelled: {chunk.run_id}")
            return

def cancel_after_delay():
    time.sleep(8)
    run_id = run_id_container.get("run_id")
    if run_id:
        success = agent.cancel_run(run_id)
        print(f"\nCancelled: {success}")

agent_thread = threading.Thread(target=long_running_task)
cancel_thread = threading.Thread(target=cancel_after_delay)

agent_thread.start()
cancel_thread.start()

agent_thread.join()
cancel_thread.join()
```

### API Endpoint

```
POST /agents/{agent_id}/runs/{run_id}/cancel
```

```bash
curl --location 'http://localhost:7777/agents/story-writer-agent/runs/123/cancel' \
    --request POST
```

---

## Team Run Cancellation

### cancel_run() Method

```python
success: bool = team.cancel_run(run_id)
```

### Key Differences from Agent

- Team emits **both** `TeamRunEvent.run_cancelled` (team-level) and `RunEvent.run_cancelled` (member-level)
- Content comes from both `TeamRunEvent.run_content` and `RunEvent.run_content`
- Cancelling the team run also cancels any running member agent runs

### Streaming Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunEvent
from agno.run.base import RunStatus
from agno.run.team import TeamRunEvent
from agno.team import Team

storyteller_agent = Agent(
    name="StorytellerAgent",
    model=OpenAIResponses(id="gpt-5.2"),
    description="An agent that writes creative stories",
)
editor_agent = Agent(
    name="EditorAgent",
    model=OpenAIResponses(id="gpt-5.2"),
    description="An agent that reviews and improves stories",
)

team = Team(
    name="Storytelling Team",
    members=[storyteller_agent, editor_agent],
    model=OpenAIResponses(id="gpt-5.2"),
)

run_id_container = {}

def long_running_task():
    for chunk in team.run("Write a very long story...", stream=True):
        if "run_id" not in run_id_container and chunk.run_id:
            run_id_container["run_id"] = chunk.run_id

        if chunk.event in [TeamRunEvent.run_content, RunEvent.run_content]:
            print(chunk.content, end="", flush=True)
        elif chunk.event == RunEvent.run_cancelled:
            print(f"\nMember run cancelled: {chunk.run_id}")
            return
        elif chunk.event == TeamRunEvent.run_cancelled:
            print(f"\nTeam run cancelled: {chunk.run_id}")
            return

def cancel_after_delay():
    time.sleep(8)
    run_id = run_id_container.get("run_id")
    if run_id:
        team.cancel_run(run_id)
```

### API Endpoint

```
POST /teams/{team_id}/runs/{run_id}/cancel
```

```bash
curl --location 'http://localhost:7777/teams/storytelling-team/runs/456/cancel' \
    --request POST
```

---

## Workflow Run Cancellation

### cancel_run() Method

```python
success: bool = workflow.cancel_run(run_id)
```

### Key Differences from Agent/Team

- Workflow emits `WorkflowRunEvent.workflow_cancelled` for workflow-level cancellation
- Also emits `RunEvent.run_cancelled` for step-level agent cancellation
- Cancellation stops the workflow at the current step — completed steps are preserved

### Streaming Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunEvent
from agno.run.base import RunStatus
from agno.run.workflow import WorkflowRunEvent
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

researcher = Agent(
    name="Research Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    instructions="Research the given topic.",
)
writer = Agent(
    name="Writing Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="Write a comprehensive article based on the research.",
)

article_workflow = Workflow(
    description="Research -> Write Article",
    steps=[
        Step(name="research", agent=researcher),
        Step(name="writing", agent=writer),
    ],
    debug_mode=True,
)

run_id_container = {}

def long_running_task():
    for chunk in article_workflow.run("Write an article on AI agents", stream=True):
        if "run_id" not in run_id_container and chunk.run_id:
            run_id_container["run_id"] = chunk.run_id

        if chunk.event == RunEvent.run_content:
            print(chunk.content, end="", flush=True)
        elif chunk.event == RunEvent.run_cancelled:
            print(f"\nStep run cancelled: {chunk.run_id}")
            return
        elif chunk.event == WorkflowRunEvent.workflow_cancelled:
            print(f"\nWorkflow cancelled: {chunk.run_id}")
            return

def cancel_after_delay():
    time.sleep(8)
    run_id = run_id_container.get("run_id")
    if run_id:
        article_workflow.cancel_run(run_id)
```

### API Endpoint

```
POST /workflows/{workflow_id}/runs/{run_id}/cancel
```

```bash
curl --location 'http://localhost:7777/workflows/analysis-workflow/runs/789/cancel' \
    --request POST
```

---

## Summary

| Entity | Method | Cancelled Event | API Endpoint |
|--------|--------|-----------------|--------------|
| **Agent** | `agent.cancel_run(run_id)` | `RunEvent.run_cancelled` | `POST /agents/{id}/runs/{run_id}/cancel` |
| **Team** | `team.cancel_run(run_id)` | `TeamRunEvent.run_cancelled` | `POST /teams/{id}/runs/{run_id}/cancel` |
| **Workflow** | `workflow.cancel_run(run_id)` | `WorkflowRunEvent.workflow_cancelled` | `POST /workflows/{id}/runs/{run_id}/cancel` |

All methods return `bool` — `True` if marked for cancellation, `False` if not found or already completed.
