# Hooks (Pre-hooks & Post-hooks)

Execute custom logic before and after Agent/Team runs.

## Docs Hierarchy

```
Hooks
├── Overview                              ← this router
├── Usage
│   ├── Agent
│   │   ├── Input Validation Pre-Hook     → agent-hooks.md
│   │   ├── Input Transformation Pre-Hook → agent-hooks.md
│   │   ├── Output Validation Post-Hook   → agent-hooks.md
│   │   └── Output Transformation Post-Hook → agent-hooks.md
│   └── Team
│       ├── Input Transformation Pre-Hook → team-hooks.md
│       └── Output Transformation Post-Hook → team-hooks.md
└── Reference
    ├── Pre-hooks (parameters)            → agent-hooks.md
    ├── Post-hooks (parameters)           → agent-hooks.md
    └── @hook Decorator                   → agent-hooks.md
```

## When Hooks Are Triggered

| Hook Type | Timing | Can Modify |
|-----------|--------|------------|
| **Pre-hooks** | After session loaded, **before** LLM execution | `run_input`, session state, dependencies |
| **Post-hooks** | **After** response generated, before returned to user | `run_output` content |

In streaming, post-hooks run after each chunk is generated.

## Use Cases

- **Security guardrails** — PII detection, prompt injection defense (see Guardrails)
- **Input validation** — format, length, content checks
- **Input transformation** — rewrite/enrich input before LLM
- **Output validation** — quality, safety, compliance checks
- **Output transformation** — add formatting, disclaimers, metadata
- **Logging/debugging** — record metrics, duration, analytics

## Sub-References

| File | Read When |
|------|-----------|
| `hooks/agent-hooks.md` | Pre/post-hook parameters, @hook decorator, background execution, agent examples (input validation, input transformation, output validation, output transformation) |
| `hooks/team-hooks.md` | Team-specific hooks — input transformation, output transformation, team examples |

## Quick Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.exceptions import CheckTrigger, InputCheckError
from agno.run.agent import RunInput

def validate_input_length(run_input: RunInput) -> None:
    if len(run_input.input_content) > 1000:
        raise InputCheckError(
            "Input too long. Max 1000 characters.",
            check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
        )

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[validate_input_length],
)
```

## Hook Function Signatures

### Pre-hook (Agent)

```python
from agno.run.agent import RunInput

def my_pre_hook(run_input: RunInput) -> None:
    """Receives RunInput, can modify or raise InputCheckError to block."""
    pass

async def my_async_pre_hook(run_input: RunInput) -> None:
    """Async version."""
    pass
```

### Post-hook (Agent)

```python
from agno.run.agent import RunOutput

def my_post_hook(run_output: RunOutput) -> None:
    """Receives RunOutput, can modify or raise OutputCheckError to block."""
    pass
```

### RunInput Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `input_content` | `str` | The user's input text |
| `session_id` | `Optional[str]` | Current session ID |
| `user_id` | `Optional[str]` | Current user ID |
| `dependencies` | `Optional[Dict]` | Runtime dependencies |
| `session_state` | `Optional[Dict]` | Current session state |

### RunOutput Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `str` | The agent's response text |
| `session_id` | `Optional[str]` | Current session ID |
| `metrics` | `Optional[Metrics]` | Token usage, timing metrics |

### @hook Decorator

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `run_in_background` | `bool` | `False` | When True, hook runs as a background task (requires AgentOS) |

```python
from agno.hooks import hook

@hook(run_in_background=True)
def my_background_hook(run_output: RunOutput) -> None:
    """Runs in background — won't block the response."""
    log_to_analytics(run_output)
```

## Key Imports

```python
from agno.run.agent import RunInput, RunOutput
from agno.run.team import RunInput as TeamRunInput, RunOutput as TeamRunOutput
from agno.exceptions import CheckTrigger, InputCheckError, OutputCheckError
from agno.hooks import hook  # @hook decorator
```

## Cross-References

- **Guardrails** → `references/guardrails.md` (built-in guardrails as hooks)
- **Evals as hooks** → `references/evals/agent-as-judge.md` (AgentAsJudgeEval as post-hook)
- **Tool hooks** → `references/tools.md` (tool-level pre/post hooks — separate from agent hooks)
