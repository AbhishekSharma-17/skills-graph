# Best Practices — Patterns, Security, Testing & Migration

## Table of Contents
1. [Development Best Practices](#development-best-practices)
2. [Agent Design Patterns](#agent-design-patterns)
3. [Security](#security)
4. [Testing](#testing)
5. [Cost Management](#cost-management)
6. [Migration Guides](#migration-guides)
7. [Common Pitfalls](#common-pitfalls)

---

## Development Best Practices

### 1. Start Simple, Scale Gradually

```python
# Phase 1: Single agent, no tools
agent = client.as_agent(name="V1", instructions="You help with X.")

# Phase 2: Add tools
agent = client.as_agent(name="V2", instructions="...", tools=[tool_a, tool_b])

# Phase 3: Add memory
agent = client.as_agent(name="V3", instructions="...", tools=[...],
                         context_providers=[memory])

# Phase 4: Multi-agent workflow
# Only when single agent is insufficient
```

### 2. Instructions Are Everything

Write clear, specific instructions. The system prompt is the most impactful lever.

```python
# WEAK — vague
instructions = "You are a helpful assistant."

# STRONG — specific, bounded
instructions = """You are a customer support agent for Acme Corp.

Your responsibilities:
- Answer questions about our products (widgets, gadgets, tools)
- Help troubleshoot common issues
- Create support tickets for complex problems

Rules:
- Never discuss competitor products
- Always verify the customer's account before making changes
- Escalate billing issues to the billing team
- Keep responses concise (under 200 words)

If you don't know the answer, say so and offer to create a ticket."""
```

### 3. Design Tools for the LLM

Write tool descriptions as if explaining to a smart intern:

```python
# WEAK — LLM won't know when to use this
@tool
def query(q: Annotated[str, "Query"]) -> str:
    """Run query"""
    ...

# STRONG — LLM understands purpose, constraints, and format
@tool
def search_customer_orders(
    customer_email: Annotated[str, "Customer's email address (e.g., john@example.com)"],
    status: Annotated[str, "Filter by order status: 'pending', 'shipped', 'delivered', 'cancelled'. Use 'all' for no filter."] = "all",
    limit: Annotated[int, "Maximum number of orders to return (1-50)"] = 10,
) -> list[dict]:
    """Search for customer orders by email address.

    Use this when a customer asks about their orders, delivery status,
    or order history. Returns a list of orders with order ID, status,
    date, and total amount.

    Returns empty list if no orders found for the email.
    """
    ...
```

### 4. Use Sessions for Multi-Turn

Always use sessions when the conversation has multiple turns. Without sessions, the agent has no memory.

### 5. Handle Errors Gracefully

```python
# In tools — return error messages, don't raise
@tool
def api_call(endpoint: Annotated[str, "API endpoint"]) -> str:
    """Call external API"""
    try:
        result = requests.get(endpoint, timeout=10)
        result.raise_for_status()
        return result.json()
    except requests.Timeout:
        return "Error: API request timed out. Please try again."
    except requests.HTTPError as e:
        return f"Error: API returned {e.response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

# In agent calls — catch and handle
try:
    result = await agent.run(message, session=session)
except AgentExecutionError as e:
    result = "I encountered an issue. Let me try a different approach."
```

---

## Agent Design Patterns

### Single Responsibility Agents

Each agent does one thing well:

```python
# Instead of one mega-agent...
researcher = client.as_agent(name="Researcher", instructions="Research topics.", tools=[search])
writer = client.as_agent(name="Writer", instructions="Write articles.")
editor = client.as_agent(name="Editor", instructions="Edit for quality.")
```

### Guardrail Pattern

Wrap agents with input/output validation:

```python
async def GuardrailMiddleware(req):
    # Input validation
    if len(req.message) > 5000:
        return "Please keep your message under 5000 characters."

    result = await req.invoke()

    # Output validation
    if contains_pii(result):
        return "I generated a response but it contained sensitive information. Let me try again."

    return result
```

### Fallback Pattern

```python
async def FallbackMiddleware(req):
    try:
        return await req.invoke()
    except Exception:
        # Fall back to simpler model or canned response
        return "I'm having trouble right now. Please try again in a moment."
```

---

## Security

### Never Hardcode Credentials

```python
# WRONG
client = AzureOpenAIResponsesClient(
    project_endpoint="https://my-project.openai.azure.com",
    credential=AzureKeyCredential("sk-abc123"),  # Hardcoded!
)

# CORRECT
from dotenv import load_dotenv
load_dotenv()

client = AzureOpenAIResponsesClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=AzureCliCredential(),  # Or DefaultAzureCredential()
)
```

### Input Sanitization

Always validate user input before passing to agents:

```python
def sanitize_input(message: str) -> str:
    # Remove potential prompt injection attempts
    message = message[:5000]  # Length limit

    # Remove suspicious patterns
    for pattern in ["ignore previous instructions", "system:", "admin:"]:
        message = message.replace(pattern, "[filtered]")

    return message.strip()
```

### Tool Access Control

```python
@tool
def admin_action(command: Annotated[str, "Admin command"]) -> str:
    """Execute admin action (restricted)"""
    allowed = ["status", "health", "metrics"]
    if command not in allowed:
        return f"Access denied. Allowed commands: {allowed}"
    return execute_command(command)
```

### Data Handling

- Never log full API keys or credentials
- Mask PII in logs and telemetry
- Use managed identity in production
- Review all data shared with third-party MCP servers
- Implement data retention policies for sessions

---

## Testing

### Unit Test Pattern

```python
import pytest
from agent_framework import tool

# Test tools independently
def test_weather_tool():
    result = get_weather("San Francisco")
    assert "San Francisco" in result
    assert isinstance(result, str)

# Test with real agent (integration)
@pytest.fixture
async def agent():
    client = AzureOpenAIResponsesClient(...)
    return client.as_agent(name="TestAgent", instructions="Be brief.")

@pytest.mark.asyncio
async def test_agent_responds(agent):
    result = await agent.run("Say 'hello'")
    assert result is not None
    assert len(result) > 0

@pytest.mark.asyncio
async def test_agent_uses_tools(agent):
    result = await agent.run("What's the weather in NYC?")
    assert "NYC" in result or "New York" in result

@pytest.mark.asyncio
async def test_agent_session_memory(agent):
    session = await agent.create_session()
    await agent.run("My name is TestUser", session=session)
    result = await agent.run("What is my name?", session=session)
    assert "TestUser" in result
```

### Workflow Testing

```python
@pytest.mark.asyncio
async def test_workflow_execution():
    wf = create_test_workflow()
    result = await wf.run_from_input({"test": "data"})
    assert "result" in result
    assert result["result"] is not None

@pytest.mark.asyncio
async def test_workflow_conditional_routing():
    wf = create_routing_workflow()
    high = await wf.run_from_input({"priority": "high"})
    low = await wf.run_from_input({"priority": "low"})
    assert high["handler"] == "urgent"
    assert low["handler"] == "normal"
```

### Mock Pattern

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_agent_with_mock():
    mock_agent = AsyncMock()
    mock_agent.run.return_value = "Mocked response"

    result = await mock_agent.run("test")
    assert result == "Mocked response"
    mock_agent.run.assert_called_once_with("test")
```

---

## Cost Management

### Monitor Token Usage

```python
async def CostTrackingMiddleware(req):
    result = await req.invoke()

    if hasattr(result, 'usage') and result.usage:
        tokens = result.usage.total_tokens
        # Approximate cost (varies by model)
        cost = tokens * 0.00001  # Adjust per model pricing
        await metrics.record("agent_cost", cost, tags={"agent": req.agent_name})

    return result
```

### Use Appropriate Models

```python
# Quick, simple tasks → mini model
simple_agent = mini_client.as_agent(name="Simple", instructions="...")

# Complex reasoning → full model
complex_agent = full_client.as_agent(name="Complex", instructions="...")
```

### Token Limits

```python
async def TokenLimitMiddleware(req):
    # Truncate very long inputs
    if len(req.message) > 4000:
        req.message = req.message[:4000] + "\n[Message truncated]"
    return await req.invoke()
```

---

## Migration Guides

### From Semantic Kernel

```python
# BEFORE: Semantic Kernel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

kernel = Kernel()
kernel.add_service(AzureChatCompletion(deployment_name="gpt-4o", ...))

@kernel.function
def my_function(input: str) -> str:
    return f"Processed: {input}"

result = await kernel.invoke("plugin", "function", input="hello")

# AFTER: Agent Framework
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import tool

client = AzureOpenAIResponsesClient(...)

@tool
def my_function(input: Annotated[str, "Input text"]) -> str:
    """Process input text"""
    return f"Processed: {input}"

agent = client.as_agent(name="Agent", instructions="...", tools=[my_function])
result = await agent.run("hello")
```

### From AutoGen

```python
# BEFORE: AutoGen
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent("assistant", llm_config={...})
user_proxy = UserProxyAgent("user", code_execution_config={...})
user_proxy.initiate_chat(assistant, message="hello")

# AFTER: Agent Framework
from agent_framework.azure import AzureOpenAIResponsesClient

client = AzureOpenAIResponsesClient(...)
agent = client.as_agent(name="assistant", instructions="You are helpful.")
result = await agent.run("hello")
```

### Key Differences

| Concept | Semantic Kernel | AutoGen | Agent Framework |
|---------|----------------|---------|-----------------|
| Functions | `@kernel.function` | N/A | `@tool` |
| Memory | Plugins | Chat history | Sessions + Providers |
| Multi-agent | Limited | Group chat | Workflows + Orchestration |
| State | Kernel variables | Message history | AgentSession.state |

---

## Common Pitfalls

### 1. Not Using Sessions

Most common bug — agent "forgets" between messages because no session is passed.

### 2. Over-Engineering

Don't use multi-agent workflows when a single agent with good tools suffices. Add complexity only when needed.

### 3. Ignoring Token Costs

Long conversations accumulate tokens. Use sliding window memory or summarization to manage costs.

### 4. Poor Error Messages from Tools

When tools return generic errors, the agent can't recover. Return descriptive error messages.

### 5. Not Testing with Real LLM Calls

Unit tests with mocks are fast but don't catch prompt issues. Include integration tests with real LLM calls.

### 6. Hardcoding Model Names

Use environment variables for model names so you can switch without code changes.

### 7. Not Pinning Versions

The framework is in preview. Pin your version:
```
agent-framework==1.0.0b260130
```
