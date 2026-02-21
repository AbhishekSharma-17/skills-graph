# Team Hooks

Pre-hooks and post-hooks for Team runs. Teams use the same hook system as Agents, with Team-specific types.

## Key Differences from Agent Hooks

| Aspect | Agent Hooks | Team Hooks |
|--------|------------|------------|
| Input type | `from agno.run.agent import RunInput` | `from agno.run.team import RunInput` |
| Output type | `from agno.run.agent import RunOutput` | `from agno.run.team import RunOutput` |
| Session type | `AgentSession` | `TeamSession` |
| Instance param | `agent: Agent` | `team: Team` |

## Pre-hook Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_input` | `RunInput` (from `agno.run.team`) | Team run input — can be validated or modified |
| `team` | `Team` | Reference to the Team instance |
| `session` | `TeamSession` | Current team session |
| `session_state` | `Optional[Dict[str, Any]]` | Session state |
| `dependencies` | `Optional[Dict[str, Any]]` | Dependencies |
| `metadata` | `Optional[Dict[str, Any]]` | Metadata |
| `user_id` | `Optional[str]` | User ID |
| `debug_mode` | `Optional[bool]` | Debug mode flag |

## Post-hook Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_output` | `RunOutput` or `TeamRunOutput` | Team run output |
| `team` | `Team` | Reference to the Team instance |
| `session` | `TeamSession` | Current team session |
| `session_state` | `Optional[Dict[str, Any]]` | Session state |
| `dependencies` | `Optional[Dict[str, Any]]` | Dependencies |
| `metadata` | `Optional[Dict[str, Any]]` | Metadata |
| `user_id` | `Optional[str]` | User ID |
| `debug_mode` | `Optional[bool]` | Debug mode flag |

## Example: Team Input Transformation Pre-Hook

```python
from typing import Optional
from agno.team import Team
from agno.models.openai import OpenAIResponses
from agno.run.team import RunInput
from agno.session.team import TeamSession

def transform_input(
    run_input: RunInput,
    session: TeamSession,
    user_id: Optional[str] = None,
    debug_mode: Optional[bool] = None,
) -> None:
    """Rewrite input to be more relevant to the team's purpose."""
    transformer_team = Team(
        name="Input Transformer",
        model=OpenAIResponses(id="gpt-5.2"),
        instructions=[
            "Rewrite the user request to be more relevant to the team's purpose.",
            "Keep the input as concise as possible.",
            "The team's purpose is to provide investment guidance.",
        ],
        debug_mode=debug_mode,
    )
    result = transformer_team.run(
        input=f"Transform this user request: '{run_input.input_content}'"
    )
    run_input.input_content = result.content

team = Team(
    name="Financial Advisor",
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[transform_input],
    instructions=["You are a knowledgeable financial advisor."],
)

team.print_response(
    input="I'm 35 and want to start investing for retirement.",
    session_id="test_session",
    user_id="test_user",
    stream=True,
)
```

## Example: Team Output Transformation Post-Hook

Add formatting, disclaimers, or AI-structured restructuring to team output:

### Simple — Disclaimer + Timestamp

```python
from datetime import datetime
from agno.run.team import RunOutput

def add_disclaimer_and_timestamp(run_output: RunOutput) -> None:
    content = run_output.content.strip()
    run_output.content = f"""{content}

---
**Important:** This information is for educational purposes only.
Please consult with appropriate professionals for personalized advice.

*Response generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}*"""

team = Team(
    name="General Advisor",
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[add_disclaimer_and_timestamp],
)
```

### Advanced — AI-Structured Financial Advice

```python
from agno.run.team import RunOutput
from pydantic import BaseModel

class FormattedResponse(BaseModel):
    main_content: str
    key_points: list[str]
    disclaimer: str
    follow_up_questions: list[str]

def structure_financial_advice(run_output: RunOutput) -> None:
    formatter_team = Team(
        name="Response Formatter",
        model=OpenAIResponses(id="gpt-5.2"),
        instructions=[
            "Transform the response into a structured format with:",
            "1. MAIN_CONTENT: Core response, clear and well-formatted",
            "2. KEY_POINTS: 3-4 key takeaways",
            "3. DISCLAIMER: Appropriate financial disclaimer",
            "4. FOLLOW_UP_QUESTIONS: 2-3 relevant follow-up questions",
        ],
        output_schema=FormattedResponse,
    )
    try:
        formatted = formatter_team.run(
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
        add_disclaimer_and_timestamp(run_output)

team = Team(
    name="Financial Advisor",
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[structure_financial_advice],
)
```

### Markdown Formatting

```python
from datetime import datetime
from agno.run.team import RunOutput

def add_markdown_formatting(run_output: RunOutput) -> None:
    content = run_output.content.strip()
    run_output.content = f"""# Response

{content}

---
*Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*"""

team = Team(
    model=OpenAIResponses(id="gpt-5.2"),
    post_hooks=[add_markdown_formatting],
)
```

## Key Imports

```python
from agno.team import Team
from agno.run.team import RunInput, RunOutput
from agno.session.team import TeamSession
from agno.exceptions import CheckTrigger, InputCheckError, OutputCheckError
from agno.hooks import hook  # @hook decorator for background execution
```

## Notes

- Team hooks work identically to agent hooks — same pattern, same auto-injection
- The `@hook(run_in_background=True)` decorator works with team hooks too
- Background hooks require AgentOS
- Team hooks receive `team` parameter instead of `agent`
- All exception types (`InputCheckError`, `OutputCheckError`, `CheckTrigger`) are shared
