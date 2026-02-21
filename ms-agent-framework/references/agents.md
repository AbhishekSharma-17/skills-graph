# Agents — Types, Configuration, and Patterns

## Table of Contents
1. [Agent Fundamentals](#agent-fundamentals)
2. [Agent Creation Patterns](#agent-creation-patterns)
3. [Agent Configuration Options](#agent-configuration-options)
4. [Agent Patterns](#agent-patterns)
5. [Agent-as-Tool Pattern](#agent-as-tool-pattern)
6. [Agent Lifecycle](#agent-lifecycle)

---

## Agent Fundamentals

An Agent is the core building block — an LLM-powered entity that processes inputs, calls tools, and generates responses. Every agent has:

- **Name** — identifier for logging and multi-agent scenarios
- **Instructions** — system prompt defining behavior
- **Tools** (optional) — functions the agent can call
- **Context Providers** (optional) — dynamic context injected per turn
- **Response Format** (optional) — Pydantic model for structured output

### Mental Model

```
User Message → [Context Providers] → [Instructions + Tools] → LLM → [Tool Calls?] → Response
                                                                        ↓
                                                                   [Execute Tools]
                                                                        ↓
                                                                   [LLM again with results]
```

The agent loops tool calls automatically until the LLM produces a final text response.

---

## Agent Creation Patterns

### Pattern 1: Basic Conversational Agent

```python
agent = client.as_agent(
    name="Assistant",
    instructions="You are a helpful general assistant.",
)

result = await agent.run("What is quantum computing?")
```

### Pattern 2: Tool-Using Agent

```python
from agent_framework import tool
from typing import Annotated

@tool
def search_web(query: Annotated[str, "Search query"]) -> str:
    """Search the web for information"""
    return f"Results for: {query}"

@tool
def calculate(expression: Annotated[str, "Math expression"]) -> float:
    """Evaluate a mathematical expression"""
    return eval(expression)

agent = client.as_agent(
    name="ResearchAssistant",
    instructions="You help with research. Use search_web for current info and calculate for math.",
    tools=[search_web, calculate],
)
```

### Pattern 3: Multi-Turn with Session

```python
session = await agent.create_session()

r1 = await agent.run("I'm planning a trip to Japan", session=session)
r2 = await agent.run("What's the best time to visit?", session=session)
r3 = await agent.run("How about budget tips?", session=session)
# Agent has full context of the conversation
```

### Pattern 4: Streaming Agent

```python
agent = client.as_agent(
    name="Storyteller",
    instructions="You write creative stories.",
)

async for chunk in agent.run("Write a short story about a robot", stream=True):
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

### Pattern 5: Structured Output Agent

```python
from pydantic import BaseModel, Field

class TripPlan(BaseModel):
    destination: str = Field(description="Travel destination")
    duration_days: int = Field(description="Trip length in days")
    budget_estimate: float = Field(description="Estimated budget in USD")
    activities: list[str] = Field(description="Recommended activities")

agent = client.as_agent(
    name="TripPlanner",
    instructions="You create detailed trip plans.",
    response_format=TripPlan,
)

plan: TripPlan = await agent.run("Plan a 5-day trip to Tokyo")
print(f"Budget: ${plan.budget_estimate}")
```

### Pattern 6: Context-Aware Agent

```python
from agent_framework import BaseContextProvider

class UserPreferencesProvider(BaseContextProvider):
    async def get_context(self, session, **kwargs) -> str:
        prefs = session.state.get("preferences", {})
        return f"User preferences: {prefs}"

class TimeContextProvider(BaseContextProvider):
    async def get_context(self, session, **kwargs) -> str:
        from datetime import datetime
        return f"Current time: {datetime.now().isoformat()}"

agent = client.as_agent(
    name="PersonalAssistant",
    instructions="You are a personal assistant. Use provided context.",
    context_providers=[UserPreferencesProvider(), TimeContextProvider()],
)
```

---

## Agent Configuration Options

### `client.as_agent()` Parameters

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `name` | `str` | ✓ | Agent identifier |
| `instructions` | `str` | ✓ | System prompt |
| `tools` | `List[Callable]` | | Functions decorated with `@tool` |
| `context_providers` | `List[BaseContextProvider]` | | Dynamic context sources |
| `response_format` | `Type[BaseModel]` | | Pydantic model for structured output |
| `mcp_servers` | `List[str]` | | MCP server names (Azure AI Foundry) |

### `agent.run()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | required | User message |
| `session` | `AgentSession` | `None` | Session for multi-turn context |
| `stream` | `bool` | `False` | Enable token streaming |

---

## Agent Patterns

### Specialist Agent Factory

Create multiple agents with shared configuration:

```python
def create_specialist(name: str, domain: str, tools: list) -> Agent:
    return client.as_agent(
        name=name,
        instructions=f"""You are an expert in {domain}.
        Answer questions only about {domain}.
        If asked about other topics, say you can only help with {domain}.""",
        tools=tools,
    )

weather_agent = create_specialist("WeatherBot", "weather forecasting", [get_weather])
finance_agent = create_specialist("FinanceBot", "financial analysis", [get_stock_price])
travel_agent = create_specialist("TravelBot", "travel planning", [search_flights, book_hotel])
```

### Router Agent (Supervisor Pattern)

One agent routes to specialists:

```python
supervisor = client.as_agent(
    name="Supervisor",
    instructions="""You route requests to specialist agents.
    For weather: use the weather_agent tool.
    For finance: use the finance_agent tool.
    For travel: use the travel_agent tool.""",
    tools=[
        weather_agent.as_tool(),
        finance_agent.as_tool(),
        travel_agent.as_tool(),
    ],
)
```

### Guardrail Agent

Agent that validates output before returning:

```python
@tool
def validate_response(response: Annotated[str, "Response to validate"]) -> str:
    """Check response for PII, profanity, or policy violations"""
    # Validation logic
    if contains_pii(response):
        return "BLOCKED: Response contains personal information"
    return f"APPROVED: {response}"

safe_agent = client.as_agent(
    name="SafeAgent",
    instructions="Always validate your responses using the validate_response tool before answering.",
    tools=[validate_response, *other_tools],
)
```

---

## Agent-as-Tool Pattern

Any agent can be exposed as a tool for other agents:

```python
# Create specialist
research_agent = client.as_agent(
    name="Researcher",
    instructions="You research topics thoroughly.",
    tools=[search_web],
)

# Expose as tool for another agent
writer_agent = client.as_agent(
    name="Writer",
    instructions="You write articles. Use the researcher for facts.",
    tools=[research_agent.as_tool()],
)

# Writer can now delegate research to the research agent
result = await writer_agent.run("Write an article about quantum computing")
```

This is the simplest way to compose agents — no workflow needed for basic delegation.

---

## Agent Lifecycle

### Creation → Configuration → Execution → Teardown

```python
# 1. Creation — client connects to model provider
client = AzureOpenAIResponsesClient(...)

# 2. Configuration — define agent behavior
agent = client.as_agent(
    name="MyAgent",
    instructions="...",
    tools=[...],
)

# 3. Execution — run with messages
session = await agent.create_session()
result = await agent.run("message", session=session)

# 4. Persistence — save state if needed
session_data = session.to_dict()
# Store session_data to database

# 5. Resumption — restore later
restored = AgentSession.from_dict(session_data)
result = await agent.run("continue", session=restored)
```

### Event Flow During `agent.run()`

1. Context providers generate context strings
2. System message assembled: instructions + context
3. Message sent to LLM with available tools
4. If LLM returns tool calls → execute tools → send results back to LLM
5. Repeat step 4 until LLM produces final text response
6. Middleware post-processing (if configured)
7. Session updated with new messages
8. Response returned
