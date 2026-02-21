# Workflow Sessions

Workflow sessions differ from agent/team sessions. Instead of storing individual messages, they track complete pipeline executions — inputs, outputs, and step results.

## Agent/Team vs Workflow Sessions

| Feature | Agent/Team Sessions | Workflow Sessions |
|---------|-------------------|-------------------|
| **What's stored** | Messages and conversation turns | Complete workflow runs with step results |
| **History type** | Message-based (chat history) | Run-based (execution history) |
| **Summaries** | Supported (`enable_session_summaries`) | Not supported (stores complete runs) |
| **History format** | Messages in LLM context | Previous run results prepended to step inputs |

## Basic Workflow Session

```python
from agno.workflow import Workflow
from agno.db.sqlite import SqliteDb

workflow = Workflow(
    name="Research Pipeline",
    db=SqliteDb(db_file="workflows.db"),
    steps=[...],
)

# Each run creates or updates the workflow session
result = workflow.run(input="AI trends", session_id="session_123")
```

Each execution:
1. Creates a unique `run_id`
2. Stores input, output, and all step results
3. Updates the session with the new run
4. Makes history available for future runs

## WorkflowSession Structure

```python
@dataclass
class WorkflowSession:
    session_id: str                          # Unique session identifier
    user_id: Optional[str] = None            # User who owns this session
    workflow_id: Optional[str] = None        # Which workflow this belongs to
    workflow_name: Optional[str] = None      # Name of the workflow
    runs: Optional[List[WorkflowRunOutput]] = None  # All workflow executions
    session_data: Optional[Dict] = None      # Includes session_name, session_state
    workflow_data: Optional[Dict] = None     # Workflow configuration
    metadata: Optional[Dict] = None          # Custom metadata
    created_at: Optional[int] = None         # Unix timestamp
    updated_at: Optional[int] = None         # Unix timestamp
```

## What Gets Stored Per Run

Each workflow run stores:
- **Input:** Data passed to `workflow.run()`
- **Output:** Final result from the workflow
- **Step results:** Output from each step in the pipeline
- **Session data:** Execution time, status, metrics
- **Session state:** Shared data between steps

## Enable History for Steps

Make previous run results available to workflow steps:

```python
workflow = Workflow(
    name="Content Pipeline",
    db=SqliteDb(db_file="workflows.db"),
    steps=[...],
    add_workflow_history_to_steps=True,  # Include previous runs in step context
    num_history_runs=5,                  # Limit how many past runs to load
)
```

## History Format

Agno wraps past runs in structured XML before injecting into each step's input:

```xml
<workflow_history_context>
[Workflow Run-1]
User input: Create a blog post about AI
Workflow output: [Full output from run]

[Workflow Run-2]
User input: Write about machine learning
Workflow output: [Full output from run]
</workflow_history_context>
```

This lets each step in the pipeline understand what the workflow has produced before.

## Workflow Session Naming

### Manual

```python
workflow.run(input="Analyze AI trends", session_id="session_123")
workflow.set_session_name(
    session_id="session_123",
    session_name="AI Trends Analysis Q4 2024",
)
name = workflow.get_session_name(session_id="session_123")
print(name)  # "AI Trends Analysis Q4 2024"
```

### Auto-Generated

```python
workflow.set_session_name(session_id="session_123", autogenerate=True)
name = workflow.get_session_name(session_id="session_123")
print(name)  # "Automated research and analysis pipel - 2024-11-19 14:30"
```
