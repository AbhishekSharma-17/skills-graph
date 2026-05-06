# CrewAI Agents

> Source: https://docs.crewai.com/en/concepts/agents

## Overview

An Agent in CrewAI is an autonomous unit with a defined role, goal, and backstory that determines how it approaches tasks. Agents are the building blocks of crews — think of them as specialized team members with specific expertise.

## Agent Definition

```python
from crewai import Agent, LLM

agent = Agent(
    role="Senior Data Analyst",
    goal="Analyze datasets and extract actionable insights",
    backstory=(
        "You have 15 years of experience in data science. "
        "You excel at finding patterns in complex datasets "
        "and communicating findings to non-technical stakeholders."
    ),
    llm=LLM(model="openai/gpt-4o", temperature=0.2),
    tools=[],
    verbose=True,
    memory=True,
    max_iter=15,
    max_rpm=10,
    allow_delegation=False,
)
```

## Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `role` | str | required | The agent's job title / function |
| `goal` | str | required | What the agent is trying to achieve |
| `backstory` | str | required | Context that shapes the agent's behavior |
| `llm` | LLM/str | default model | Language model to use |
| `tools` | list[Tool] | [] | Tools available to the agent |
| `verbose` | bool | False | Print execution details |
| `memory` | bool | True | Enable memory for the agent |
| `max_iter` | int | 25 | Maximum iterations before forced answer |
| `max_rpm` | int | None | Rate limit (requests per minute) |
| `allow_delegation` | bool | False | Can delegate to other agents |
| `step_callback` | callable | None | Called after each agent step |
| `cache` | bool | True | Enable tool result caching |
| `system_template` | str | None | Custom system prompt template |
| `prompt_template` | str | None | Custom prompt template |
| `response_template` | str | None | Custom response template |
| `max_retry_limit` | int | 2 | Max retries on error |
| `respect_context_window` | bool | True | Auto-summarize if context overflow |
| `code_execution_mode` | str | "safe" | "safe" (Docker) or "unsafe" (local) |

## Writing Effective Roles

```python
# BAD: Too generic
agent = Agent(role="Helper", goal="Help with things", backstory="You help.")

# GOOD: Specific and focused
agent = Agent(
    role="Senior Python Backend Engineer",
    goal="Design and implement high-performance REST APIs with FastAPI",
    backstory=(
        "You have 8 years of experience building production Python services. "
        "You follow SOLID principles, write comprehensive tests, and always "
        "consider security implications. You prefer async patterns and "
        "Pydantic for data validation."
    ),
)
```

## LLM Configuration per Agent

```python
from crewai import Agent, LLM

# Using string shorthand
agent = Agent(role="...", goal="...", backstory="...", llm="openai/gpt-4o")

# Using LLM class for full control
agent = Agent(
    role="...",
    goal="...",
    backstory="...",
    llm=LLM(
        model="anthropic/claude-sonnet-4-20250514",
        temperature=0.7,
        max_tokens=4096,
        top_p=0.9,
    ),
)

# Different agents can use different models
cheap_agent = Agent(role="...", goal="...", backstory="...", llm="openai/gpt-4o-mini")
smart_agent = Agent(role="...", goal="...", backstory="...", llm="anthropic/claude-sonnet-4-20250514")
```

## Agent with Tools

```python
from crewai import Agent
from crewai_tools import SerperDevTool, WebsiteSearchTool

researcher = Agent(
    role="Research Specialist",
    goal="Find accurate, up-to-date information on any topic",
    backstory="Expert researcher who cross-references multiple sources.",
    tools=[SerperDevTool(), WebsiteSearchTool()],
    verbose=True,
)
```

## Agent with Delegation

```python
manager = Agent(
    role="Project Manager",
    goal="Coordinate the team to deliver high-quality outputs",
    backstory="Experienced PM who knows how to delegate effectively.",
    allow_delegation=True,  # Can delegate to other crew members
    verbose=True,
)
```

When `allow_delegation=True`, the agent gains two automatic tools:
- **Delegate work to co-worker** — Assign a sub-task to another agent
- **Ask question to co-worker** — Query another agent for information

## Agent with Custom System Template

```python
agent = Agent(
    role="Code Reviewer",
    goal="Review code for bugs, security issues, and best practices",
    backstory="Senior engineer with expertise in secure coding.",
    system_template="""<|start_header_id|>system<|end_header_id|>
{{ .System }}

You MUST respond in the following format:
1. Summary of issues found
2. Severity (Critical/High/Medium/Low)
3. Suggested fixes
<|eot_id|>""",
)
```

## Agent Step Callback

```python
def my_callback(step_output):
    print(f"Agent step: {step_output}")

agent = Agent(
    role="Analyst",
    goal="Analyze data",
    backstory="Data expert.",
    step_callback=my_callback,
)
```

## YAML-Based Agent Configuration

When using the CLI project structure, agents are defined in `config/agents.yaml`:

```yaml
researcher:
  role: "Senior Research Analyst"
  goal: "Find comprehensive information about {topic}"
  backstory: >
    You are an expert researcher with deep experience in
    finding and synthesizing information from multiple sources.
    You are thorough and always verify your findings.
  tools:
    - SerperDevTool
    - WebsiteSearchTool
  verbose: true

writer:
  role: "Technical Content Writer"
  goal: "Create engaging content about {topic}"
  backstory: >
    You are a skilled writer who transforms complex technical
    information into clear, engaging content.
  verbose: true
```

## Agents with Code Execution

```python
agent = Agent(
    role="Data Scientist",
    goal="Analyze data using Python code",
    backstory="Expert in pandas, numpy, and data visualization.",
    allow_code_execution=True,
    code_execution_mode="safe",  # Uses Docker sandbox
)
```

## Agent Context Window Management

```python
agent = Agent(
    role="Researcher",
    goal="Research complex topics",
    backstory="Expert researcher.",
    respect_context_window=True,  # Auto-summarize on overflow
    max_tokens=4096,              # Per-response token limit
)
```

## Common Patterns

### Specialist Team

```python
analysts = [
    Agent(role="Financial Analyst", goal="Analyze financial data", backstory="..."),
    Agent(role="Market Analyst", goal="Analyze market trends", backstory="..."),
    Agent(role="Risk Analyst", goal="Identify potential risks", backstory="..."),
]
```

### Agent Factory

```python
def create_agent(specialty: str, model: str = "openai/gpt-4o") -> Agent:
    return Agent(
        role=f"Senior {specialty} Specialist",
        goal=f"Provide expert {specialty} analysis and recommendations",
        backstory=f"You have 10+ years of experience in {specialty}.",
        llm=LLM(model=model),
        verbose=True,
    )

seo_agent = create_agent("SEO")
security_agent = create_agent("Security", model="anthropic/claude-sonnet-4-20250514")
```

## Common Pitfalls

1. **Vague backstory** — The more specific the backstory, the better the agent performs
2. **Too many tools** — Agents get confused with >5-7 tools; keep it focused
3. **Forgetting max_iter** — Without it, agents can loop indefinitely on hard tasks
4. **allow_delegation without peers** — Delegation needs other agents in the crew
5. **Same LLM for all agents** — Use cheaper models for simple tasks, powerful ones for complex reasoning
