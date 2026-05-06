# CrewAI Collaboration & Delegation

> Source: https://docs.crewai.com/en/concepts/collaboration

## Overview

Collaboration enables agents to work as a true team — delegating tasks and asking questions to leverage each other's expertise. When `allow_delegation=True`, agents gain automatic tools for inter-agent communication.

## Delegation Mechanism

When an agent has `allow_delegation=True`, CrewAI automatically provides two tools:

1. **Delegate work to co-worker** — Assign a sub-task to another agent
2. **Ask question to co-worker** — Query another agent for specific information

```python
from crewai import Agent

# Agent that can delegate
manager = Agent(
    role="Project Manager",
    goal="Coordinate the team to deliver high-quality results",
    backstory="Experienced manager who delegates effectively.",
    allow_delegation=True,
    verbose=True,
)

# Specialist agents (available for delegation)
researcher = Agent(
    role="Research Specialist",
    goal="Provide thorough research on any topic",
    backstory="Expert researcher with academic background.",
    allow_delegation=False,  # Focus on own work
)

writer = Agent(
    role="Content Writer",
    goal="Write clear, engaging content",
    backstory="Professional writer with 10 years experience.",
    allow_delegation=False,
)
```

## How Delegation Works

1. Agent A (with `allow_delegation=True`) receives a task
2. Agent A decides another agent is better suited for part of the work
3. Agent A uses "Delegate work to co-worker" tool, specifying:
   - The co-worker's role
   - The task to delegate
   - Context/instructions
4. The co-worker (Agent B) executes the delegated work
5. Agent A receives the result and incorporates it

## Delegation in Sequential Process

```python
from crewai import Agent, Task, Crew, Process

# All agents in the crew
lead = Agent(
    role="Lead Engineer",
    goal="Design and coordinate the implementation",
    backstory="Senior engineer who delegates implementation details.",
    allow_delegation=True,
    verbose=True,
)

backend_dev = Agent(
    role="Backend Developer",
    goal="Implement robust API endpoints",
    backstory="Expert in Python and FastAPI.",
    allow_delegation=False,
)

frontend_dev = Agent(
    role="Frontend Developer",
    goal="Build responsive UI components",
    backstory="Expert in React and TypeScript.",
    allow_delegation=False,
)

# The lead can delegate parts of this task to specialists
design_task = Task(
    description="Design and coordinate the implementation of a user dashboard.",
    expected_output="Complete implementation plan with delegated components.",
    agent=lead,
)

crew = Crew(
    agents=[lead, backend_dev, frontend_dev],
    tasks=[design_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()
```

## Delegation in Hierarchical Process

In hierarchical mode, the manager agent automatically has delegation capabilities:

```python
from crewai import Agent, Task, Crew, Process, LLM

# Worker agents
analyst = Agent(
    role="Data Analyst",
    goal="Analyze data and provide insights",
    backstory="Expert in statistical analysis.",
)

engineer = Agent(
    role="ML Engineer",
    goal="Build and optimize machine learning models",
    backstory="Expert in scikit-learn and PyTorch.",
)

reporter = Agent(
    role="Report Writer",
    goal="Create clear technical reports",
    backstory="Expert at communicating technical findings.",
)

# Tasks (no agent assignment needed — manager delegates)
tasks = [
    Task(description="Analyze the dataset for patterns.", expected_output="Analysis report."),
    Task(description="Build a predictive model.", expected_output="Model performance metrics."),
    Task(description="Write the final report.", expected_output="Technical report."),
]

crew = Crew(
    agents=[analyst, engineer, reporter],
    tasks=tasks,
    process=Process.hierarchical,
    manager_llm=LLM(model="openai/gpt-4o"),
    verbose=True,
)
```

## Asking Questions Between Agents

```python
# An agent can ask questions to co-workers
researcher = Agent(
    role="Market Researcher",
    goal="Understand market dynamics",
    backstory="Experienced market analyst.",
    allow_delegation=True,  # Can ask questions too
)

domain_expert = Agent(
    role="Industry Expert",
    goal="Provide domain-specific expertise",
    backstory="20 years in the fintech industry.",
    allow_delegation=False,
)

# During execution, researcher might:
# "Ask question to co-worker: Industry Expert, 
#  What are the regulatory requirements for fintech in EU?"
```

## Controlling Delegation Scope

```python
# Only specific agents should delegate
lead = Agent(role="Lead", ..., allow_delegation=True)    # Can delegate
worker1 = Agent(role="Worker 1", ..., allow_delegation=False)  # Cannot
worker2 = Agent(role="Worker 2", ..., allow_delegation=False)  # Cannot

# All workers are available as delegation targets
crew = Crew(
    agents=[lead, worker1, worker2],
    tasks=[...],
    process=Process.sequential,
)
```

## Verbose Mode for Debugging Collaboration

```python
# Enable verbose to see delegation in action
crew = Crew(
    agents=[manager, dev, tester],
    tasks=[task],
    process=Process.sequential,
    verbose=True,  # Shows which agent delegates to whom
)
```

Output example:
```
[Manager] Thinking... I need a backend expert for the API design.
[Manager] Using tool: Delegate work to co-worker
  > Co-worker: Backend Developer
  > Task: Design the REST API endpoints for user management
  > Context: We need CRUD operations with proper auth...
[Backend Developer] Working on delegated task...
[Backend Developer] Completed: Here are the endpoints...
[Manager] Received delegation result. Continuing...
```

## Collaboration Patterns

### Hub-and-Spoke

One coordinator delegates to specialists:

```python
coordinator = Agent(role="Coordinator", ..., allow_delegation=True)
specialist_a = Agent(role="Specialist A", ..., allow_delegation=False)
specialist_b = Agent(role="Specialist B", ..., allow_delegation=False)
specialist_c = Agent(role="Specialist C", ..., allow_delegation=False)
```

### Chain of Command

Each level can delegate down:

```python
director = Agent(role="Director", ..., allow_delegation=True)
manager = Agent(role="Manager", ..., allow_delegation=True)
developer = Agent(role="Developer", ..., allow_delegation=False)
```

### Peer Consultation

Multiple agents can ask each other questions:

```python
agent_a = Agent(role="Frontend Expert", ..., allow_delegation=True)
agent_b = Agent(role="Backend Expert", ..., allow_delegation=True)
# Both can ask questions to each other
```

## Preventing Delegation Loops

```python
# Set max_iter to prevent infinite delegation chains
agent = Agent(
    role="Manager",
    goal="...",
    backstory="...",
    allow_delegation=True,
    max_iter=15,  # Prevents infinite delegation loops
)
```

## Common Pitfalls

1. **allow_delegation without peers** — Agent needs other agents in the crew to delegate to
2. **All agents delegating** — Creates confusion; have clear hierarchy
3. **No max_iter** — Delegation chains can loop indefinitely
4. **Vague delegation instructions** — Agents need clear co-worker roles to delegate effectively
5. **Missing verbose in development** — Can't debug delegation without seeing the interactions
6. **Delegation in single-agent crews** — Pointless; needs 2+ agents to be useful
