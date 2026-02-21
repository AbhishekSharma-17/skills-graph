# Agno Guardrails — Reference Router

Guardrails are built-in safeguards that validate input before agents and teams process it. They are implemented as **pre-hooks** that execute after the session loads but before any LLM processing begins. When a guardrail detects undesired content, it raises an `InputCheckError` to block the request.

## Docs Hierarchy

```
Guardrails
├── Overview (/guardrails/overview)
├── Included Guardrails
│   ├── PII Detection (/guardrails/included/pii)
│   ├── Prompt Injection (/guardrails/included/prompt-injection)
│   └── OpenAI Moderation (/guardrails/included/openai-moderation)
├── Usage
│   ├── Agent
│   │   ├── PII Detection (/guardrails/usage/agent/pii-detection)
│   │   ├── Prompt Injection (/guardrails/usage/agent/prompt-injection)
│   │   └── OpenAI Moderation (/guardrails/usage/agent/openai-moderation)
│   └── Team
│       ├── PII Detection (/guardrails/usage/team/pii-detection)
│       ├── Prompt Injection (/guardrails/usage/team/prompt-injection)
│       └── OpenAI Moderation (/guardrails/usage/team/openai-moderation)
└── Reference
    ├── BaseGuardrail (/reference/hooks/base-guardrail)
    ├── PIIDetectionGuardrail (/reference/hooks/pii-guardrail)
    ├── PromptInjectionGuardrail (/reference/hooks/prompt-injection-guardrail)
    └── OpenAIModerationGuardrail (/reference/hooks/openai-moderation-guardrail)
```

## How Guardrails Work

1. User sends a message to an Agent or Team
2. Session is loaded from database (if configured)
3. **Pre-hooks execute** — guardrails validate input
4. If guardrail detects undesired content → raises `InputCheckError` → request blocked
5. If all guardrails pass → Agent/Team processes normally
6. Post-hooks execute after response is generated

## Sub-References

Read only what the current task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Built-in Guardrails** | `references/guardrails/builtin-guardrails.md` | Using PII Detection, Prompt Injection, or OpenAI Moderation guardrails — all parameters, configuration, patterns, masking |
| **Custom Guardrails** | `references/guardrails/custom-guardrails.md` | Creating custom guardrails with BaseGuardrail, hooks integration, exceptions (InputCheckError, CheckTrigger), sync/async patterns |
| **Usage Examples** | `references/guardrails/usage-examples.md` | Full working examples for agents and teams — PII detection, prompt injection, OpenAI moderation, combining multiple guardrails, error handling |

## Guardrail Parameters

### PIIDetectionGuardrail

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mask_pii` | `bool` | `False` | Mask PII with asterisks instead of raising an error |
| `enable_ssn_check` | `bool` | `True` | Check for Social Security Numbers |
| `enable_credit_card_check` | `bool` | `True` | Check for credit card numbers |
| `enable_email_check` | `bool` | `True` | Check for email addresses |
| `enable_phone_check` | `bool` | `True` | Check for phone numbers |
| `custom_patterns` | `dict` | `{}` | Additional PII patterns to detect (name → regex) |

### PromptInjectionGuardrail

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `injection_patterns` | `Optional[List[str]]` | `None` | Custom patterns list (replaces defaults if provided). Default checks 17 patterns including "ignore previous instructions", "jailbreak", "admin override", etc. |

### OpenAIModerationGuardrail

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `moderation_model` | `str` | `"omni-moderation-latest"` | OpenAI moderation model to use |
| `raise_for_categories` | `Optional[List[str]]` | `None` | Specific categories to block (None = all flagged categories). Categories: `violence`, `violence/graphic`, `hate`, `hate/threatening`, `sexual`, `sexual/minors`, `self-harm`, `self-harm/intent`, `self-harm/instructions`, `harassment`, `harassment/threatening` |
| `api_key` | `Optional[str]` | `None` | OpenAI API key (defaults to `OPENAI_API_KEY` env var) |

### BaseGuardrail (Custom Guardrails)

Extend `BaseGuardrail` and implement `check()` or `async_check()`:

```python
from agno.guardrails import BaseGuardrail
from agno.run.agent import RunInput
from agno.exceptions import InputCheckError, CheckTrigger

class MyGuardrail(BaseGuardrail):
    def check(self, run_input: RunInput) -> None:
        if "blocked_word" in run_input.input_content:
            raise InputCheckError(
                "Blocked content detected",
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )
```

## Quick Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.exceptions import InputCheckError

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    pre_hooks=[
        PIIDetectionGuardrail(),
        PromptInjectionGuardrail(),
    ],
)

try:
    agent.print_response(input="My SSN is 123-45-6789")
except InputCheckError as e:
    print(f"Blocked: {e.message}")
```

## Key Imports

```python
from agno.guardrails import PIIDetectionGuardrail       # PII detection
from agno.guardrails import PromptInjectionGuardrail     # Prompt injection defense
from agno.guardrails import OpenAIModerationGuardrail    # OpenAI content moderation
from agno.guardrails import BaseGuardrail                # Custom guardrail base class
from agno.exceptions import InputCheckError, CheckTrigger  # Exceptions
from agno.run.agent import RunInput                       # Input object for custom guardrails
```
