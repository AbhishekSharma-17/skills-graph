# Custom Guardrails

Create custom guardrails by extending `BaseGuardrail`. Custom guardrails integrate into the same pre-hook system as built-in guardrails and work identically with both Agents and Teams.

---

## BaseGuardrail Class

All guardrails (built-in and custom) extend `BaseGuardrail`:

```python
from agno.guardrails import BaseGuardrail
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `check` | `check(self, run_input: RunInput) -> None` | Synchronous guardrail check. Raise `InputCheckError` to block. |
| `async_check` | `async async_check(self, run_input: RunInput) -> None` | Async guardrail check. Raise `InputCheckError` to block. |

Agno automatically calls `check()` for `.run()` / `.print_response()` and `async_check()` for `.arun()` / `.aprint_response()`.

### RunInput Object

The `run_input` parameter provides access to the user's input:

```python
from agno.run.agent import RunInput

# Key attributes:
run_input.input_content  # str — The user's message text
```

---

## Creating a Custom Guardrail

### Basic Structure

```python
import re
from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail
from agno.run.agent import RunInput

class URLGuardrail(BaseGuardrail):
    """Guardrail to identify and block inputs containing URLs."""

    def check(self, run_input: RunInput) -> None:
        """Raise InputCheckError if the input contains any URLs."""
        if isinstance(run_input.input_content, str):
            url_pattern = r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
            if re.search(url_pattern, run_input.input_content):
                raise InputCheckError(
                    "The input contains URLs, which are not allowed.",
                    check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
                )

    async def async_check(self, run_input: RunInput) -> None:
        """Async version — same logic."""
        if isinstance(run_input.input_content, str):
            url_pattern = r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
            if re.search(url_pattern, run_input.input_content):
                raise InputCheckError(
                    "The input contains URLs, which are not allowed.",
                    check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
                )
```

### Using Custom Guardrail

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.exceptions import InputCheckError

agent = Agent(
    name="URL-Protected Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[URLGuardrail()],
)

try:
    agent.run("Can you check what's in https://fake.com?")
except InputCheckError as e:
    print(f"Blocked: {e.message}")
```

---

## More Custom Guardrail Examples

### Input Length Guardrail

```python
from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail
from agno.run.agent import RunInput

class InputLengthGuardrail(BaseGuardrail):
    """Block inputs that exceed a maximum character length."""

    def __init__(self, max_length: int = 1000):
        self.max_length = max_length

    def check(self, run_input: RunInput) -> None:
        if isinstance(run_input.input_content, str):
            if len(run_input.input_content) > self.max_length:
                raise InputCheckError(
                    f"Input too long. Max {self.max_length} characters allowed, got {len(run_input.input_content)}.",
                    check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
                )

    async def async_check(self, run_input: RunInput) -> None:
        self.check(run_input)
```

### Language Filter Guardrail

```python
import re
from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail
from agno.run.agent import RunInput

class ProfanityGuardrail(BaseGuardrail):
    """Block inputs containing profanity."""

    def __init__(self, blocked_words: list[str] | None = None):
        self.blocked_words = blocked_words or ["badword1", "badword2"]

    def check(self, run_input: RunInput) -> None:
        if isinstance(run_input.input_content, str):
            content_lower = run_input.input_content.lower()
            for word in self.blocked_words:
                if word.lower() in content_lower:
                    raise InputCheckError(
                        f"Input contains inappropriate language.",
                        check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
                    )

    async def async_check(self, run_input: RunInput) -> None:
        self.check(run_input)
```

### Topic Restriction Guardrail

```python
from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail
from agno.run.agent import RunInput

class TopicRestrictionGuardrail(BaseGuardrail):
    """Block inputs about restricted topics."""

    def __init__(self, restricted_topics: list[str]):
        self.restricted_topics = [t.lower() for t in restricted_topics]

    def check(self, run_input: RunInput) -> None:
        if isinstance(run_input.input_content, str):
            content_lower = run_input.input_content.lower()
            for topic in self.restricted_topics:
                if topic in content_lower:
                    raise InputCheckError(
                        f"Questions about '{topic}' are not allowed.",
                        check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
                    )

    async def async_check(self, run_input: RunInput) -> None:
        self.check(run_input)

# Usage
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[TopicRestrictionGuardrail(restricted_topics=["politics", "religion"])],
)
```

---

## Exceptions

### InputCheckError

Raised by guardrails to block a request:

```python
from agno.exceptions import InputCheckError, CheckTrigger

raise InputCheckError(
    "Description of why the input was blocked",
    check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
)
```

### CheckTrigger Enum

| Value | Description |
|-------|-------------|
| `CheckTrigger.INPUT_NOT_ALLOWED` | Input validation failed (guardrail blocked it) |
| `CheckTrigger.OUTPUT_NOT_ALLOWED` | Output validation failed (post-hook blocked it) |

### Handling Guardrail Errors

```python
from agno.exceptions import InputCheckError

try:
    agent.print_response(input="My SSN is 123-45-6789")
except InputCheckError as e:
    print(f"Message: {e.message}")
    print(f"Trigger: {e.check_trigger}")
    # e.check_trigger == CheckTrigger.INPUT_NOT_ALLOWED
```

---

## Hooks Integration

Guardrails are implemented as **pre-hooks**. They execute in the agent/team lifecycle at a specific point:

```
1. User sends message
2. Session loaded from DB (if configured)
3. ▶ PRE-HOOKS EXECUTE (guardrails check input here)
4. Agent/Team processes input with LLM
5. ▶ POST-HOOKS EXECUTE (output validation here)
6. Response returned to user
```

### Pre-hook Auto-Injected Parameters

When creating guardrails as functions (not classes), these parameters are auto-injected:

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_input` | `RunInput` | Input to validate/modify |
| `agent` | `Agent` | Agent instance reference |
| `session` | `Session` | Current agent session |
| `run_context` | `RunContext` | Current run context |
| `debug_mode` | `bool` (optional) | Debug mode status |

### Function-Based Pre-hook (Alternative to Class)

```python
from agno.exceptions import CheckTrigger, InputCheckError
from agno.run.agent import RunInput

def validate_input_length(run_input: RunInput) -> None:
    """Pre-hook function to validate input length."""
    max_length = 1000
    if isinstance(run_input.input_content, str):
        if len(run_input.input_content) > max_length:
            raise InputCheckError(
                f"Input too long. Max {max_length} characters.",
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[validate_input_length],  # Function, not class instance
)
```

### Combining Classes and Functions

```python
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[
        PromptInjectionGuardrail(),   # Built-in class
        PIIDetectionGuardrail(),       # Built-in class
        URLGuardrail(),                # Custom class
        validate_input_length,         # Custom function
    ],
)
```

---

## Best Practices

- **Always implement both `check` and `async_check`** — ensures guardrail works with both sync and async agent execution
- **Use `CheckTrigger.INPUT_NOT_ALLOWED`** for input guardrails, `OUTPUT_NOT_ALLOWED` for output guardrails
- **Check `isinstance(run_input.input_content, str)`** — input may not always be a string (e.g., multimodal)
- **Order matters** — place fast regex-based guardrails before API-based guardrails (like OpenAI Moderation)
- **Keep guardrails focused** — one concern per guardrail for composability
- **Provide clear error messages** — users see the `InputCheckError.message` when blocked
- **Reuse via composition** — stack multiple guardrails in `pre_hooks` rather than building monolithic validators
