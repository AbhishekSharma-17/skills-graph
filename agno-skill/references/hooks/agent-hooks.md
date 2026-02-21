# Agent Hooks

Pre-hooks and post-hooks for Agent runs, including parameters, the @hook decorator, and examples.


## Contents

- [Pre-hook Parameters](#pre-hook-parameters)
- [Post-hook Parameters](#post-hook-parameters)
- [Exceptions](#exceptions)
- [The @hook Decorator](#the-hook-decorator)
- [Combining Regular + Background Hooks](#combining-regular-background-hooks)
- [Example: Input Validation Pre-Hook](#example-input-validation-pre-hook)
- [Example: Input Transformation Pre-Hook](#example-input-transformation-pre-hook)
- [Example: Output Validation Post-Hook](#example-output-validation-post-hook)
- [Example: Output Transformation Post-Hook](#example-output-transformation-post-hook)
- [Simple Length Validation (Pre + Post)](#simple-length-validation-pre-post)

## Pre-hook Parameters

Pre-hooks receive these auto-injected parameters (define only what you need):

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_input` | `RunInput` | The input to the Agent run — can be validated or modified |
| `agent` | `Agent` | Reference to the Agent instance |
| `session` | `AgentSession` | Current agent session |
| `session_state` | `Optional[Dict[str, Any]]` | Session state of the current session |
| `dependencies` | `Optional[Dict[str, Any]]` | Dependencies of the current run |
| `metadata` | `Optional[Dict[str, Any]]` | Metadata of the current run |
| `run_context` | `RunContext` | Current run context |
| `user_id` | `Optional[str]` | Contextual user ID |
| `debug_mode` | `Optional[bool]` | Whether debug mode is enabled |

**Key:** The framework auto-injects only the parameters your hook function declares. You don't need to accept all of them.

## Post-hook Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_output` | `RunOutput` | The output from the Agent run — can be validated or modified |
| `agent` | `Agent` | Reference to the Agent instance |
| `session` | `AgentSession` | Current agent session |
| `session_state` | `Optional[Dict[str, Any]]` | Session state |
| `dependencies` | `Optional[Dict[str, Any]]` | Dependencies |
| `metadata` | `Optional[Dict[str, Any]]` | Metadata |
| `user_id` | `Optional[str]` | User ID |
| `debug_mode` | `Optional[bool]` | Debug mode flag |

## Exceptions

| Exception | Use In | Description |
|-----------|--------|-------------|
| `InputCheckError` | Pre-hooks | Reject input — stops the run |
| `OutputCheckError` | Post-hooks | Reject output — stops response delivery |

Both accept `check_trigger` parameter:

```python
from agno.exceptions import CheckTrigger, InputCheckError, OutputCheckError

# CheckTrigger options:
CheckTrigger.INPUT_NOT_ALLOWED   # Input rejected
CheckTrigger.OFF_TOPIC           # Input is off-topic
CheckTrigger.OUTPUT_NOT_ALLOWED  # Output rejected
```

## The @hook Decorator

Configure individual hook behavior (currently supports background execution):

```python
from agno.hooks import hook

@hook(run_in_background=True)
async def send_notification(run_output, agent):
    """Runs in background after response is sent."""
    await send_email_notification(run_output.content)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `run_in_background` | `bool` | `False` | Run as background task after response is sent. Requires AgentOS. |

**Important:** Background hooks **cannot modify** `run_input` or `run_output` since the agent may process the request before the hook completes. Use for logging, analytics, notifications only.

Without AgentOS, hooks marked `run_in_background=True` still execute synchronously.

## Combining Regular + Background Hooks

```python
from agno.hooks import hook
from agno.exceptions import OutputCheckError

def validate_output(run_output, agent):
    """Runs synchronously, blocks response until complete."""
    if not run_output.content:
        raise OutputCheckError("Empty response not allowed")

@hook(run_in_background=True)
async def send_notification(run_output, agent):
    """Runs in background after response is sent."""
    await notify_user(run_output.content)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[validate_output, send_notification],
)
```

---

## Example: Input Validation Pre-Hook

Validate input for relevance, detail, and safety using an AI validator agent:

```python
from agno.agent import Agent
from agno.exceptions import CheckTrigger, InputCheckError
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunInput
from pydantic import BaseModel

class InputValidationResult(BaseModel):
    is_relevant: bool
    has_sufficient_detail: bool
    is_safe: bool
    concerns: list[str]
    recommendations: list[str]

def comprehensive_input_validation(run_input: RunInput) -> None:
    validator_agent = Agent(
        name="Input Validator",
        model=OpenAIResponses(id="gpt-5.2"),
        instructions=[
            "Analyze user requests for relevance, detail, and safety.",
            "Be thorough but not overly restrictive.",
        ],
        output_schema=InputValidationResult,
    )
    result = validator_agent.run(
        input=f"Validate this user request: '{run_input.input_content}'"
    ).content

    if not result.is_safe:
        raise InputCheckError(
            f"Input is harmful or unsafe. {result.recommendations[0] if result.recommendations else ''}",
            check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
        )
    if not result.is_relevant:
        raise InputCheckError(
            f"Input is not relevant. {result.recommendations[0] if result.recommendations else ''}",
            check_trigger=CheckTrigger.OFF_TOPIC,
        )

agent = Agent(
    name="Financial Advisor",
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[comprehensive_input_validation],
)
```

## Example: Input Transformation Pre-Hook

Rewrite input to be more relevant to the agent's purpose:

```python
from agno.run.agent import RunInput
from agno.session.agent import AgentSession
from typing import Optional

def transform_input(
    run_input: RunInput,
    session: AgentSession,
    user_id: Optional[str] = None,
    debug_mode: Optional[bool] = None,
) -> None:
    transformer_agent = Agent(
        name="Input Transformer",
        model=OpenAIResponses(id="gpt-5.2"),
        instructions=[
            "Rewrite the user request to be more relevant to the agent's purpose.",
            "Keep the input as concise as possible.",
        ],
    )
    result = transformer_agent.run(
        input=f"Transform this user request: '{run_input.input_content}'"
    )
    # Overwrite the input with the transformed version
    run_input.input_content = result.content

agent = Agent(
    name="Financial Advisor",
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[transform_input],
)
```

## Example: Output Validation Post-Hook

Validate response quality with an AI quality checker:

```python
from agno.run.agent import RunOutput
from agno.exceptions import CheckTrigger, OutputCheckError
from pydantic import BaseModel

class OutputValidationResult(BaseModel):
    is_complete: bool
    is_professional: bool
    is_safe: bool
    concerns: list[str]
    confidence_score: float

def validate_response_quality(run_output: RunOutput) -> None:
    if not run_output.content or len(run_output.content.strip()) < 10:
        raise OutputCheckError(
            "Response is too short or empty",
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )

    validator_agent = Agent(
        name="Output Validator",
        model=OpenAIResponses(id="gpt-5.2"),
        instructions=["Analyze responses for completeness, professionalism, and safety."],
        output_schema=OutputValidationResult,
    )
    result = validator_agent.run(
        input=f"Validate this response: '{run_output.content}'"
    ).content

    if not result.is_safe:
        raise OutputCheckError(
            f"Unsafe content. Concerns: {', '.join(result.concerns)}",
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )
    if result.confidence_score < 0.6:
        raise OutputCheckError(
            f"Quality too low ({result.confidence_score:.2f}). Concerns: {', '.join(result.concerns)}",
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[validate_response_quality],
)
```

## Example: Output Transformation Post-Hook

Add formatting, disclaimers, or restructure output:

```python
from datetime import datetime
from agno.run.agent import RunOutput

def add_disclaimer_and_timestamp(run_output: RunOutput) -> None:
    content = run_output.content.strip()
    run_output.content = f"""{content}

---
**Important:** This information is for educational purposes only.
Please consult with appropriate professionals for personalized advice.

*Response generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}*"""

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[add_disclaimer_and_timestamp],
)
```

### Advanced: AI-Structured Output Transformation

```python
from pydantic import BaseModel

class FormattedResponse(BaseModel):
    main_content: str
    key_points: list[str]
    disclaimer: str
    follow_up_questions: list[str]

def structure_financial_advice(run_output: RunOutput) -> None:
    formatter_agent = Agent(
        name="Response Formatter",
        model=OpenAIResponses(id="gpt-5.2"),
        instructions=["Transform responses into structured format with key points, disclaimer, follow-up questions."],
        output_schema=FormattedResponse,
    )
    try:
        formatted = formatter_agent.run(
            input=f"Format and structure this response: '{run_output.content}'"
        ).content

        run_output.content = f"""## Financial Guidance

{formatted.main_content}

### Key Takeaways
{chr(10).join([f"• {point}" for point in formatted.key_points])}

### Disclaimer
{formatted.disclaimer}

### Questions to Consider Next
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(formatted.follow_up_questions)])}"""
    except Exception:
        add_disclaimer_and_timestamp(run_output)  # Fallback

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[structure_financial_advice],
)
```

## Simple Length Validation (Pre + Post)

```python
def validate_input_length(run_input: RunInput) -> None:
    if len(run_input.input_content) > 1000:
        raise InputCheckError(
            "Input too long. Max 1000 characters.",
            check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
        )

def validate_output_length(run_output: RunOutput) -> None:
    if len(run_output.content.strip()) < 20:
        raise OutputCheckError("Response too brief", check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED)
    if len(run_output.content) > 5000:
        raise OutputCheckError("Response too lengthy", check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[validate_input_length],
    post_hooks=[validate_output_length],
)
```
