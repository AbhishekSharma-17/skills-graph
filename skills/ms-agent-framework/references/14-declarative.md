# Declarative Agents — YAML-Based Agent Definition

## Overview

Declarative agents are defined via YAML configuration instead of Python code. This enables no-code agent creation and configuration-driven deployments.

## YAML Agent Definition

```yaml
# agent.yaml
name: WeatherAssistant
instructions: |
  You are a helpful weather assistant.
  Always provide temperature in both Celsius and Fahrenheit.
  Be concise in your responses.

tools:
  - name: get_weather
    description: Get weather for a location
    parameters:
      location:
        type: string
        description: City name

options:
  temperature: 0.7
  max_tokens: 500
```

## Loading a Declarative Agent

```python
from agent_framework import Agent

# Load agent from YAML file
agent = Agent.from_yaml("agent.yaml", client=client)

# Use like any other agent
result = await agent.run("What's the weather in Seattle?")
```

## Declarative Agent with Tools

Tools referenced in YAML must be registered in Python:

```python
from agent_framework import tool
from typing import Annotated

@tool
def get_weather(location: Annotated[str, "City name"]) -> str:
    """Get weather for a location."""
    return f"Sunny, 72°F in {location}"

# Load YAML agent and bind tools
agent = Agent.from_yaml("agent.yaml", client=client, tools=[get_weather])
```

## When to Use Declarative Agents

| Scenario | Declarative | Code |
|---|:-:|:-:|
| Quick prototyping | ✅ | |
| Non-developer agent creation | ✅ | |
| Config-driven deployments | ✅ | |
| Complex tool logic | | ✅ |
| Custom middleware | | ✅ |
| Dynamic agent behavior | | ✅ |

## Tips

- Declarative agents are a convenience layer — they produce the same `Agent` objects as code
- Mix declarative config with code-based tools and middleware
- Use for simpler agents; use code for complex orchestration
- YAML definition supports all `as_agent()` parameters
