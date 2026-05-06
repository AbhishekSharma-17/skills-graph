# CrewAI Overview & Setup

> Source: https://docs.crewai.com/en/introduction

## What is CrewAI?

CrewAI is a lean, lightning-fast Python framework for orchestrating role-playing, autonomous AI agents. Built entirely from scratch (independent of LangChain), it enables collaborative intelligence where agents work together seamlessly to tackle complex tasks.

CrewAI uses a role-based metaphor: you define **Agents** (specialists with roles), assign them **Tasks**, organize them into **Crews**, and execute using defined **Processes** (sequential or hierarchical).

## When to Use CrewAI

| Use Case | Why CrewAI |
|----------|-----------|
| Multi-step research & analysis | Agents specialize in different aspects |
| Content generation pipelines | Writer, editor, reviewer agents collaborate |
| Customer support automation | Route and escalate with delegation |
| Data processing workflows | Parallel agent execution with structured output |
| Code review & generation | Specialized agents for different concerns |
| Complex business workflows | Event-driven Flows for production systems |

## When NOT to Use CrewAI

- Simple single-agent chat (use raw LLM calls)
- Stateless one-shot tasks (overhead not justified)
- Graph-heavy routing with complex cycles (consider LangGraph)

## Core Architecture

```
┌─────────────────────────────────────────────┐
│                   FLOW                       │
│  (Event-driven orchestration layer)          │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │              CREW                    │    │
│  │  ┌─────────┐  ┌─────────┐          │    │
│  │  │ Agent 1 │  │ Agent 2 │  ...      │    │
│  │  │ (role)  │  │ (role)  │           │    │
│  │  └────┬────┘  └────┬────┘          │    │
│  │       │             │               │    │
│  │  ┌────▼────┐  ┌────▼────┐          │    │
│  │  │ Task 1  │  │ Task 2  │  ...      │    │
│  │  └─────────┘  └─────────┘          │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## Installation

```bash
# Requires Python >=3.10, <3.14
pip install crewai

# With built-in tools (web search, file I/O, etc.)
pip install 'crewai[tools]'

# Using uv (recommended)
uv add crewai
uv add 'crewai[tools]'
```

## Environment Setup

```bash
# Set your LLM provider key
export OPENAI_API_KEY="sk-..."
# Or for Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: specify default model
export OPENAI_MODEL_NAME="gpt-4o"
```

## Quickstart — Minimal Crew

```python
from crewai import Agent, Task, Crew, Process

# 1. Define agents with roles
researcher = Agent(
    role="Senior Research Analyst",
    goal="Find the latest trends in AI agent frameworks",
    backstory="You are an expert analyst with 10 years experience in AI research.",
    verbose=True,
)

writer = Agent(
    role="Technical Writer",
    goal="Create compelling content about AI trends",
    backstory="You specialize in making complex technical topics accessible.",
    verbose=True,
)

# 2. Define tasks
research_task = Task(
    description="Research the top 3 AI agent frameworks in 2026. "
                "Include pros, cons, and use cases for each.",
    expected_output="A detailed report with framework comparisons.",
    agent=researcher,
)

writing_task = Task(
    description="Write a blog post based on the research findings. "
                "Make it engaging and informative for developers.",
    expected_output="A 500-word blog post in markdown format.",
    agent=writer,
)

# 3. Create crew and execute
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()
print(result.raw)
```

## Project Structure (CLI-Generated)

```
my-project/
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── main.py          # Entry point
│       ├── crew.py          # Crew definition with @CrewBase
│       ├── config/
│       │   ├── agents.yaml  # Agent configurations
│       │   └── tasks.yaml   # Task configurations
│       └── tools/
│           └── custom_tool.py
├── tests/
├── pyproject.toml
└── .env
```

## Key Concepts Quick Reference

| Concept | Description |
|---------|-------------|
| **Agent** | Autonomous unit with role, goal, backstory, and tools |
| **Task** | Specific assignment with description and expected output |
| **Crew** | Team of agents executing tasks together |
| **Process** | Execution strategy (sequential or hierarchical) |
| **Flow** | Event-driven orchestration wrapping crews |
| **Tool** | Capability an agent can use (search, file I/O, etc.) |
| **Memory** | Persistent context across agent interactions |
| **Knowledge** | RAG-based information retrieval for agents |

## Version Compatibility

| CrewAI Version | Python | Key Feature |
|----------------|--------|-------------|
| 1.3.x | 3.10-3.13 | Unified Memory, MCP native support |
| 1.2.x | 3.10-3.13 | Flows GA, A2A protocol |
| 1.1.x | 3.10-3.13 | Planning agent, guardrails |
| 1.0.x | 3.10-3.13 | Initial stable release |

## Common Pitfalls

1. **Forgetting `expected_output`** — Tasks require it; without it, agents produce unfocused results
2. **Overly broad roles** — Specific roles produce better outputs than generic ones
3. **Not setting verbose=True during development** — Makes debugging much harder
4. **Ignoring token limits** — Long outputs from one agent can overflow context for the next
5. **Skipping Flows for production** — Raw crews lack error recovery and state management
