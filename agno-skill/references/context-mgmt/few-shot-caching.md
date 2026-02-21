# Few-Shot Learning & Context Caching

## Few-Shot Learning

Few-shot examples teach the agent desired response patterns by providing input-output pairs. Agno adds these as `additional_input` — Message objects prepended to the conversation.

### Basic Few-Shot Example

```python
from agno.agent import Agent
from agno.models.message import Message
from agno.models.openai import OpenAIResponses

support_examples = [
    Message(role="user", content="I forgot my password and can't log in"),
    Message(
        role="assistant",
        content="""
I'll help you reset your password right away.

**Steps to Reset Your Password:**
1. Go to the login page and click "Forgot Password"
2. Enter your email address
3. Check your email for the reset link
4. Follow the link to create a new password
5. Use a strong password with uppercase, lowercase, numbers, and symbols

If you don't receive the email within 5 minutes, please check your spam folder.
Let me know if you need any assistance!
        """.strip(),
    ),
    Message(
        role="user",
        content="I've been charged twice for the same order and I'm frustrated!",
    ),
    Message(
        role="assistant",
        content="""
I sincerely apologize for the billing error and the frustration this has caused you.

**Immediate Action Plan:**
1. I'll investigate your account to confirm the duplicate charge
2. Process a full refund for the duplicate transaction
3. Ensure this doesn't happen again by checking your payment method settings
4. Provide you with a confirmation number once the refund is processed

The refund typically takes 3-5 business days to appear on your statement.
As an apology for this inconvenience, I'd also like to offer you a 10% discount on your next order.

Is there anything else I can help you with?
        """.strip(),
    ),
]

agent = Agent(
    name="Customer Support Specialist",
    model=OpenAIResponses(id="gpt-5.2"),
    additional_input=support_examples,  # Few-shot examples
    instructions=[
        "You are an expert customer support specialist.",
        "Always be empathetic, professional, and solution-oriented.",
        "Provide clear, actionable steps to resolve customer issues.",
        "Follow the established patterns for consistent, high-quality support.",
    ],
    markdown=True,
)

agent.print_response("My package arrived damaged and I want a replacement")
```

### Few-Shot Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `additional_input` | `List[Message]` | `None` | Few-shot examples as alternating user/assistant Message pairs |

### How Few-Shot Examples Are Added

Few-shot examples are placed **after** the system message and **before** the actual user message and chat history. This means:

```
[System Message]           ← Compiled from description, instructions, etc.
[Few-Shot User 1]          ← additional_input examples
[Few-Shot Assistant 1]
[Few-Shot User 2]
[Few-Shot Assistant 2]
[Chat History]             ← Previous conversation turns
[Current User Message]     ← Actual user query
```

### Best Practices for Few-Shot

- **Use 2-4 examples** — Enough to establish the pattern, not so many that they consume excessive tokens
- **Cover edge cases** — Include examples of tricky scenarios the agent should handle
- **Show the exact format** — If you want structured output, demonstrate it in examples
- **Alternate user/assistant** — Each example should be a user-assistant pair
- **Keep examples concise** — Long examples waste tokens; focus on demonstrating the pattern

---

## Context Caching

Most model providers support prompt caching, where repeated prefixes of the context are cached for faster, cheaper subsequent calls. Agno's context construction is designed to maximize cache hits.

### How Agno Optimizes for Caching

Agno places content in the system message by stability:

```
[STATIC — Cached]
├── description          ← Never changes
├── role                 ← Never changes
├── instructions         ← Rarely changes
├── tool definitions     ← Rarely changes
├── team member info     ← Rarely changes

[DYNAMIC — After cached prefix]
├── memories             ← Changes per user
├── session summary      ← Changes per run
├── session state        ← Changes per run
├── knowledge refs       ← Changes per query
└── user message         ← Always unique
```

The longer the cached prefix, the more tokens are reused on subsequent calls.

### Provider-Specific Caching

Prompt caching is handled by the model provider, not by Agno. Each provider has its own caching mechanism:

- **OpenAI** — Automatic prompt caching (no configuration needed)
- **Anthropic** — Prompt caching with explicit cache breakpoints
- **OpenRouter** — Prompt caching support varies by underlying model

### Monitoring Cache Performance

```python
response = agent.run("Tell me about AI")
print(f"Cache write: {response.metrics.cache_write_tokens}")  # First call
print(f"Cache read:  {response.metrics.cache_read_tokens}")   # Subsequent calls
```

**First call:** Cache write tokens > 0 (prefix stored)
**Subsequent calls:** Cache read tokens > 0 (prefix reused, lower cost)

### Caching Best Practices

- **Keep static content stable** — Avoid changing description/instructions between runs
- **Use the same model instance** — Caching is per-model, per-provider
- **Batch similar requests** — Requests with the same prefix maximize cache hits
- **Monitor with metrics** — Track `cache_read_tokens` to verify caching is working
- **Long instructions benefit most** — The more static content, the more cache savings

---

## Debug Mode

Enable `debug_mode=True` to inspect the fully compiled system message:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    description="You are a helpful assistant",
    instructions=["Be concise", "Use examples"],
    additional_context="The user prefers technical language.",
    debug_mode=True,  # Logs the compiled system message
)

agent.print_response("Explain recursion")
# Check logs for the full system message that was sent to the model
```

Debug mode is essential during development to verify:

- All context flags are producing expected output
- Instructions are formatted correctly
- Memories, state, and summaries are being injected
- Tool instructions are present
- System message isn't too long
