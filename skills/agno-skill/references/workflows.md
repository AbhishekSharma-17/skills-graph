# Agno Workflows


## Contents

- [What Are Workflows?](#what-are-workflows)
- [Building Blocks](#building-blocks)
- [Data Flow: StepInput and StepOutput](#data-flow-stepinput-and-stepoutput)
- [Workflow Class](#workflow-class)
- [Step Class](#step-class)
- [Parallel Class](#parallel-class)
- [Loop Class](#loop-class)
- [Condition Class](#condition-class)
- [Router Class](#router-class)
- [Steps Class](#steps-class)
- [WorkflowAgent Class](#workflowagent-class)
- [Streaming & Events](#streaming-events)
- [Background Execution](#background-execution)
- [Conversational Workflows (Beta)](#conversational-workflows-beta)
- [Persistence](#persistence)
- [Install](#install)
- [Quick Reference: When to Read What](#quick-reference-when-to-read-what)

## What Are Workflows?

Workflows orchestrate agents, teams, and functions through defined steps for repeatable tasks. A Workflow is a collection of steps that run sequentially, in parallel, in loops, or conditionally based on results. Output from each step flows to the next, creating a predictable pipeline.

**Use workflows when:** you need predictable, repeatable execution with clear sequential phases, audit trails, and explicit branching logic.

**Use teams when:** you need flexible, dynamic collaboration where agents coordinate naturally and the leader decides how to delegate.

| Aspect | Workflows | Teams |
|--------|-----------|-------|
| Execution | Predictable, controlled flow | Flexible, dynamic collaboration |
| Branching | Explicit (Condition, Router, Loop) | Implicit (agent decisions) |
| Audit trail | Strong — named, tracked steps with events | Conversation history |
| State | Session-based, persistent | Conversation-based |

---

## Building Blocks

Workflows compose from these primitives:

| Block | Purpose |
|-------|---------|
| **Step** | Fundamental unit — wraps an Agent, Team, or function |
| **Parallel** | Run multiple steps concurrently, join outputs |
| **Loop** | Repeat steps until a condition is met or max iterations |
| **Condition** | Execute steps only if an evaluator returns True (with optional else branch) |
| **Router** | Dynamically select which step(s) to run based on logic |
| **Steps** | Group multiple steps together for organizational purposes |

A step can wrap one of three executor types:
- **Agent** — individual AI executor with tools and instructions
- **Team** — coordinated group of agents for complex sub-tasks
- **Function** — custom Python function (receives `StepInput`, returns `StepOutput`)

---

## Data Flow: StepInput and StepOutput

Every custom function step receives a `StepInput` and must return a `StepOutput`. This is how data flows between steps.

### StepInput — accessing data from previous steps

```python
from agno.workflow import StepInput, StepOutput

def my_step(step_input: StepInput) -> StepOutput:
    # Original workflow input (the user's message)
    original = step_input.workflow_message or ""

    # Output from the immediately previous step
    previous = step_input.previous_step_content

    # Output from a specific named step (works through nested Parallel/Loop/etc.)
    research = step_input.get_step_content("research_hackernews")

    # Full StepOutput object from a named step
    output_obj = step_input.get_step_output("step_name")

    # ALL previous content combined
    everything = step_input.get_all_previous_content()

    # Additional metadata passed when running the workflow
    extra = step_input.additional_data or {}

    return StepOutput(
        content="Result text",
        step_name="my_step",
        success=True,
    )
```

### StepInput — full attribute reference

| Attribute | Type | Description |
|-----------|------|-------------|
| `input` | `Optional[Union[str, Dict, List, BaseModel]]` | Primary input message — can be string, dict, list, or Pydantic model |
| `previous_step_content` | `Optional[Any]` | Content from the immediately preceding step |
| `previous_step_outputs` | `Optional[Dict[str, StepOutput]]` | All previous step outputs indexed by step name |
| `additional_data` | `Optional[Dict[str, Any]]` | Extra context data passed via `workflow.run(additional_data={...})` |
| `images` | `Optional[List[Image]]` | Image inputs — accumulated from workflow input and previous steps |
| `videos` | `Optional[List[Video]]` | Video inputs — accumulated from workflow input and previous steps |
| `audio` | `Optional[List[Audio]]` | Audio inputs — accumulated from workflow input and previous steps |
| `files` | `Optional[List[File]]` | File inputs — accumulated from workflow input and previous steps |

### StepInput — helper methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_step_output(step_name)` | `Optional[StepOutput]` | Get the complete StepOutput object from a specific named step |
| `get_step_content(step_name)` | `Optional[Union[str, Dict]]` | Get just the content from a specific named step |
| `get_all_previous_content()` | `str` | Get all previous step content combined into one string |
| `get_last_step_content()` | `Optional[str]` | Get content from the immediate previous step |
| `get_workflow_history(num_runs)` | `List[Tuple[str, str]]` | Get workflow history as a list of (input, output) tuples |
| `get_workflow_history_context(num_runs)` | `str` | Get workflow history as a formatted context string |

### StepOutput — returning results

```python
return StepOutput(
    content="Processing result",   # The output content
    step_name="step_identifier",   # Name for referencing later
    success=True,                  # False for errors
    stop=False,                    # True to halt the entire workflow immediately
)
```

**Early stopping** — set `stop=True` to abort the workflow (e.g., a security gate that blocks deployment when vulnerabilities are found).

### StepOutput — full attribute reference

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `step_name` | `Optional[str]` | `None` | Step identification name — used by other steps to reference this output |
| `step_id` | `Optional[str]` | `None` | Unique step identifier (auto-generated) |
| `step_type` | `Optional[str]` | `None` | Type of step: `"Loop"`, `"Condition"`, `"Parallel"`, `"Router"`, `"Steps"`, or `None` for basic steps |
| `executor_type` | `Optional[str]` | `None` | Type of executor: `"agent"`, `"team"`, or `"function"` |
| `executor_name` | `Optional[str]` | `None` | Name of the executor (agent/team/function name) |
| `content` | `Optional[Union[str, Dict, List, BaseModel, Any]]` | `None` | Primary output content — can be any serializable type |
| `step_run_id` | `Optional[str]` | `None` | Link to the run ID of the step execution |
| `images` | `Optional[List[Image]]` | `None` | Image outputs — new or passed-through from input |
| `videos` | `Optional[List[Video]]` | `None` | Video outputs |
| `audio` | `Optional[List[Audio]]` | `None` | Audio outputs |
| `files` | `Optional[List[File]]` | `None` | File outputs |
| `metrics` | `Optional[Metrics]` | `None` | Execution metrics (tokens, timing, etc.) |
| `success` | `bool` | `True` | Whether the step executed successfully |
| `error` | `Optional[str]` | `None` | Error message if execution failed |
| `stop` | `bool` | `False` | If True, halts the entire workflow immediately after this step |
| `steps` | `Optional[List[StepOutput]]` | `None` | Nested step outputs for composite steps (Loop iterations, Condition branches, Parallel branches) |

---

## Workflow Class

### Constructor — full parameter reference

```python
from agno.workflow import Workflow

workflow = Workflow(
    name="My Workflow",
    steps=[step1, step2, ...],
)
```

### Workflow Identity & Metadata

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Workflow name — used for identification, logging, and tracing |
| `id` | `Optional[str]` | `None` | Workflow UUID — auto-generated if not set |
| `description` | `Optional[str]` | `None` | Workflow description — used by WorkflowAgent to decide when to trigger the workflow |
| `metadata` | `Optional[Dict[str, Any]]` | `None` | Arbitrary metadata stored with the workflow |

### Steps

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `steps` | `Optional[WorkflowSteps]` | `None` | The workflow steps to execute. Can be a single Step, list of steps, Steps group, or a callable factory function |

**WorkflowSteps type:** `Union[Callable, Step, List[Any], Steps, Parallel, Condition, Router, Loop]`

### Database & Persistence

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `Optional[BaseDb]` | `None` | Database backend for session persistence — SqliteDb, PostgresDb, MongoDb, etc. |

### Session & User

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `Optional[str]` | `None` | Session identifier — auto-generated UUID if not set |
| `user_id` | `Optional[str]` | `None` | User identifier — used for multi-user isolation |
| `session_state` | `Optional[Dict[str, Any]]` | `None` | Persistent state dict stored in the database. Survives across runs |
| `cache_session` | `bool` | `False` | If True, caches the current session in memory for faster access |

### Input Validation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_schema` | `Optional[Type[BaseModel]]` | `None` | Pydantic model to validate workflow input before execution. Raises error if input doesn't match |

### Conversational (Beta)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | `Optional[WorkflowAgent]` | `None` | WorkflowAgent instance for multi-turn conversational mode. Agent decides whether to run the workflow or answer from history |

### History

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_workflow_history_to_steps` | `bool` | `False` | If True, injects workflow conversation history into each step's StepInput |
| `num_history_runs` | `Optional[int]` | `None` | Number of past runs to include in workflow history. If not provided, all history is included |

### Streaming & Events

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stream` | `Optional[bool]` | `None` | Default streaming mode for this workflow. Can be overridden per-run |
| `stream_events` | `bool` | `False` | Emit workflow-level events (step started/completed, etc.) during streaming |
| `stream_executor_events` | `bool` | `True` | Emit agent/team events from within steps alongside workflow events. Set False to see only workflow-level events |
| `store_events` | `bool` | `False` | Persist events on the WorkflowRunOutput for later inspection/audit |
| `events_to_skip` | `Optional[List[Union[WorkflowRunEvent, RunEvent, TeamRunEvent]]]` | `None` | Event types to exclude when storing events (reduce noise in production) |
| `store_executor_outputs` | `bool` | `True` | Store full agent/team RunResponse objects in flattened run outputs |

### WebSocket

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `websocket_handler` | `Optional[WebSocketHandler]` | `None` | WebSocket handler for real-time bidirectional communication with UI clients |

### Debug & Telemetry

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `debug_mode` | `Optional[bool]` | `False` | Enable detailed debug logging — shows step execution, data flow between steps |
| `telemetry` | `bool` | `True` | Log minimal anonymous telemetry. Set False to opt out |

### Core Methods

#### run() — synchronous execution

```python
response = workflow.run(
    input="Your task description",
    additional_data={"key": "value"},  # Extra context accessible in StepInput
    user_id="user_1",
    session_id="session_1",
    session_state={"counter": 0},
    stream=False,
    markdown=True,
    # Media inputs
    images=None, audio=None, videos=None, files=None,
)

# Response is WorkflowRunOutput
print(response.content)
print(response.status)
```

#### arun() — async execution

```python
response = await workflow.arun(
    input="Your task",
    background=False,     # Set True for non-blocking background execution
    stream=False,
    stream_events=False,
)
```

#### print_response() / aprint_response() — rich formatted output

```python
workflow.print_response(
    input="Your task",
    stream=True,
    markdown=True,
    show_time=True,
    show_step_details=True,
)

# Async version
await workflow.aprint_response(input="Your task", stream=True, markdown=True)
```

#### cli_app() — interactive CLI

```python
workflow.cli_app(
    user="User",
    emoji=":technologist:",
    stream=True,
    markdown=True,
    show_time=True,
    show_step_details=True,
    exit_on=["exit", "quit"],
)
```

### Session & State Management Methods

| Method | Description |
|--------|-------------|
| `get_session(session_id)` | Get session info for a given session ID |
| `get_session_state(session_id)` | Get the session state dict |
| `set_session_name(session_id, session_name)` | Set a friendly name for a session |
| `get_session_metrics(session_id)` | Get execution metrics for a session |
| `get_chat_history(session_id, last_n_runs)` | Get conversation history for a session |
| `delete_session(session_id)` | Delete a session and its data from the database |

### Run Management Methods

| Method | Description |
|--------|-------------|
| `get_run_output(run_id, session_id)` | Get output for a specific run |
| `get_last_run_output(session_id)` | Get the most recent run output |
| `cancel_run(run_id)` | Cancel a currently running workflow execution |

---

## Step Class

The fundamental building block. Each Step wraps an Agent, Team, or custom function.

```python
from agno.workflow import Step

# Agent step
step = Step(name="research", agent=research_agent)

# Team step
step = Step(name="analysis", team=analysis_team)

# Function step
step = Step(name="process", executor=my_function)
```

### Step Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Step name — used for identification and referencing output via `step_input.get_step_content("name")` |
| `step_id` | `Optional[str]` | `None` | Unique step identifier — auto-generated UUID if not provided |
| `description` | `Optional[str]` | `None` | Description of the step's purpose |
| `agent` | `Optional[Agent]` | `None` | Agent instance to execute for this step. Mutually exclusive with `team` and `executor` |
| `team` | `Optional[Team]` | `None` | Team instance to execute for this step. Mutually exclusive with `agent` and `executor` |
| `executor` | `Optional[StepExecutor]` | `None` | Custom function to execute. Receives `StepInput`, returns `StepOutput`. Mutually exclusive with `agent` and `team` |
| `max_retries` | `int` | `3` | Maximum number of retry attempts on failure before giving up |
| `timeout_seconds` | `Optional[int]` | `None` | Timeout for step execution in seconds. Step is aborted if exceeded |
| `skip_on_failure` | `bool` | `False` | If True, skip this step and continue the workflow if it fails after all retries (instead of stopping) |
| `add_workflow_history` | `bool` | `False` | If True, inject workflow conversation history into this step's context |
| `num_history_runs` | `Optional[int]` | `None` | Number of past workflow runs to include in history for this step |

**StepExecutor type:** `Union[Callable[[StepInput], StepOutput], Callable[[StepInput], Iterator[StepOutput]]]`

---

## Parallel Class

Run multiple steps concurrently and join their outputs.

```python
from agno.workflow import Parallel, Step

parallel = Parallel(
    Step(name="news", agent=news_agent),
    Step(name="finance", agent=finance_agent),
    Step(name="social", agent=social_agent),
    name="gather_data",
)
```

### Parallel Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `*steps` | `*WorkflowSteps` | Required | Variable number of steps to execute in parallel (passed as positional args) |
| `name` | `Optional[str]` | `None` | Name of the parallel execution block — used for referencing combined output |
| `description` | `Optional[str]` | `None` | Description of the parallel execution purpose |

**Output:** A single `StepOutput` with `steps` containing a list of individual `StepOutput` objects from each parallel branch. Access individual results via `step_input.get_step_content("branch_name")`.

---

## Loop Class

Repeat steps until a condition is met or max iterations reached.

```python
from agno.workflow import Loop, Step

loop = Loop(
    steps=[Step(name="refine", agent=editor_agent)],
    max_iterations=5,
    end_condition=lambda outputs: "APPROVED" in (outputs[-1].content or ""),
    name="refinement_loop",
)
```

### Loop Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `steps` | `WorkflowSteps` | Required | Steps to execute in each loop iteration |
| `name` | `Optional[str]` | `None` | Name of the loop — used for referencing output |
| `description` | `Optional[str]` | `None` | Description of the loop's purpose |
| `max_iterations` | `int` | `3` | Maximum number of loop iterations before stopping (prevents infinite loops) |
| `end_condition` | `Optional[Union[Callable[[List[StepOutput]], bool], Callable[[List[StepOutput]], Awaitable[bool]]]]` | `None` | Function that receives all iteration outputs and returns True to end the loop early. Supports async. If not provided, loop runs for `max_iterations` |

**End condition receives:** `List[StepOutput]` — all outputs from all iterations so far. Return `True` to stop looping.

---

## Condition Class

Execute steps only if an evaluator returns True, with optional else branch.

```python
from agno.workflow import Condition, Step

condition = Condition(
    evaluator=lambda step_input: "urgent" in (step_input.previous_step_content or "").lower(),
    steps=[Step(name="urgent_handler", agent=urgent_agent)],
    else_steps=[Step(name="normal_handler", agent=normal_agent)],
    name="urgency_check",
)
```

### Condition Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `evaluator` | `Union[Callable[[StepInput], bool], Callable[[StepInput], Awaitable[bool]], bool]` | Required | Function that evaluates the condition. Receives `StepInput`, returns `True`/`False`. Can also be a static `bool`. Supports async |
| `steps` | `WorkflowSteps` | Required | Steps to execute when the evaluator returns `True` (the "if" branch) |
| `else_steps` | `Optional[WorkflowSteps]` | `None` | Steps to execute when the evaluator returns `False` (the "else" branch). If not provided, nothing runs on False |
| `name` | `Optional[str]` | `None` | Name of the condition block |
| `description` | `Optional[str]` | `None` | Description of what the condition checks |

---

## Router Class

Dynamically select which step(s) to run based on logic.

```python
from agno.workflow import Router, Step

def select_expert(step_input: StepInput) -> str:
    content = step_input.previous_step_content or ""
    if "financial" in content.lower():
        return "finance_step"
    elif "technical" in content.lower():
        return "tech_step"
    return "general_step"

router = Router(
    selector=select_expert,
    choices=[
        Step(name="finance_step", agent=finance_agent),
        Step(name="tech_step", agent=tech_agent),
        Step(name="general_step", agent=general_agent),
    ],
    name="expert_router",
)
```

### Router Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `selector` | `Callable[[StepInput], ...] or Callable[[StepInput, list], ...]` | Required | Function that selects which step(s) to run. Supports two signatures (see below) |
| `choices` | `WorkflowSteps` | Required | Available steps for selection. Can be a list of Steps or nested structures |
| `name` | `Optional[str]` | `None` | Name of the router block |
| `description` | `Optional[str]` | `None` | Description of the routing logic |

### Selector function signatures

```python
# Basic — receives only StepInput
def selector(step_input: StepInput) -> Union[str, Step, List[Step]]:
    return "step_name"  # or Step object, or list of Steps

# Extended — receives StepInput + available choices
def selector(step_input: StepInput, step_choices: list) -> Union[str, Step, List[Step]]:
    return step_choices[0]  # select from available choices

# Async (both signatures support async)
async def selector(step_input: StepInput) -> Union[str, Step, List[Step]]:
    return "step_name"
```

**Return types:**
- `str` — step name (Router resolves it from choices)
- `Step` — step object directly
- `List[Step]` — multiple steps executed sequentially

---

## Steps Class

Group multiple steps together for organizational purposes.

```python
from agno.workflow import Steps, Step

group = Steps(
    name="data_pipeline",
    description="Data collection and processing",
    steps=[
        Step(name="collect", agent=collector_agent),
        Step(name="clean", executor=clean_data),
        Step(name="analyze", agent=analyst_agent),
    ],
)
```

### Steps Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Name of the steps group |
| `description` | `Optional[str]` | `None` | Description of the group's purpose |
| `steps` | `Optional[List[Any]]` | `[]` | List of steps to execute sequentially within this group |

---

## WorkflowAgent Class

Specialized Agent subclass that wraps a Workflow for conversational interactions. The agent decides whether to run the full workflow or answer directly from history.

```python
from agno.workflow import WorkflowAgent

workflow_agent = WorkflowAgent(
    model=OpenAIResponses(id="gpt-4o"),
    num_history_runs=4,
    instructions="Answer from history when possible, run workflow for new processing",
)
```

### WorkflowAgent Parameters

WorkflowAgent **inherits all Agent parameters** (see `agents.md`) plus workflow-specific behavior:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Optional[Union[Model, str]]` | `None` | LLM model for the conversational agent |
| `num_history_runs` | `Optional[int]` | `None` | Number of previous workflow runs to include in context for the agent to reference |
| `instructions` | `Optional[Union[str, List[str]]]` | `None` | Instructions guiding when to run the workflow vs. answer from history |

**Usage:** Pass the WorkflowAgent as the `agent` parameter of a Workflow to enable conversational mode.

---

## Streaming & Events

Workflows emit events at every execution boundary. Use streaming to observe progress in real-time.

### Event types

| Category | Events |
|----------|--------|
| **Workflow** | WorkflowStarted, WorkflowCompleted, WorkflowError |
| **Step** | StepStarted, StepCompleted, StepError, StepOutput |
| **Parallel** | ParallelExecutionStarted, ParallelExecutionCompleted |
| **Condition** | ConditionExecutionStarted, ConditionExecutionCompleted |
| **Loop** | LoopExecutionStarted, LoopIterationStarted, LoopIterationCompleted, LoopExecutionCompleted |
| **Router** | RouterExecutionStarted, RouterExecutionCompleted |
| **Steps** | StepsExecutionStarted, StepsExecutionCompleted |

### Consuming events

```python
from agno.run.workflow import WorkflowRunEvent

# Stream with events
for event in workflow.run(input="topic", stream=True, stream_events=True):
    if event.event == WorkflowRunEvent.step_started.value:
        print(f"Step started: {event}")
    elif event.event == WorkflowRunEvent.step_completed.value:
        print(f"Step completed: {event}")

# Async streaming
async for event in workflow.arun(input="topic", stream=True, stream_events=True):
    print(event)
```

### Event storage (for audit/debugging)

```python
# Store events
response = workflow.run(input="...", store_events=True)
for event in response.events:
    print(f"{event.event} at {event.created_at}")

# Skip noisy events in production
workflow = Workflow(
    store_events=True,
    events_to_skip=[
        WorkflowRunEvent.step_started,
        WorkflowRunEvent.parallel_execution_started,
    ],
    steps=[...],
)
```

### Controlling executor events

```python
# Suppress internal agent/team events — only show workflow-level events
workflow = Workflow(
    stream_executor_events=False,
    steps=[...],
)
```

---

## Background Execution

Run workflows asynchronously and poll for completion — useful for long-running pipelines or UI integrations.

```python
import asyncio

async def main():
    # Start in background (non-blocking)
    response = await workflow.arun(input="AI trends", background=True)
    print(f"Run ID: {response.run_id}")

    # Poll for completion
    while True:
        result = workflow.get_run(response.run_id)
        if result and result.has_completed():
            print(f"Done! Content: {result.content}")
            break
        await asyncio.sleep(5)

asyncio.run(main())
```

---

## Conversational Workflows (Beta)

Enable multi-turn chat where a `WorkflowAgent` decides whether to run the workflow or answer from history.

```python
from agno.workflow import WorkflowAgent

workflow_agent = WorkflowAgent(
    model=OpenAIResponses(id="gpt-4o"),
    num_history_runs=4,
    instructions="Answer from history when possible, run workflow for new processing",
)

workflow = Workflow(
    name="Story Generator",
    description="Generates and formats stories",
    agent=workflow_agent,  # Makes it conversational
    steps=[story_writer, story_formatter, add_references],
)

# First call — runs the workflow (new topic)
workflow.print_response("Tell me a story about a dog named Rocky", stream=True)

# Second call — answers directly from history (no re-run)
workflow.print_response("What was Rocky's personality?", stream=True)

# Third call — runs the workflow again (new topic)
workflow.print_response("Now tell me about a cat named Luna", stream=True)
```

---

## Persistence

Workflows support the same database backends as agents and teams for session persistence:

```python
from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

# Development
workflow = Workflow(
    db=SqliteDb(db_file="workflow.db"),
    steps=[...],
)

# Production
workflow = Workflow(
    db=PostgresDb(db_url="postgresql+psycopg://user:pass@host:5432/db"),
    steps=[...],
)
```

Additional supported backends: MongoDB, MySQL, Redis, DynamoDB, and others.

---

## Install

```bash
uv pip install -U agno          # Core
uv pip install -U agno openai   # + OpenAI models
```

For specific tools used in examples:
```bash
uv pip install -U agno hackernews yfinance
```

---

## Quick Reference: When to Read What

| You want to... | Read |
|----------------|------|
| Understand workflow basics and API | This file (you're here) |
| See full code examples for each pattern | `references/workflow-patterns.md` |
| Build agents that go into workflow steps | `references/agents.md` |
| Build teams that go into workflow steps | `references/teams.md` |
