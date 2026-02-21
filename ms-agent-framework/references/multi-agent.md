# Multi-Agent Orchestration — Patterns & Implementation

## Table of Contents
1. [Orchestration Overview](#orchestration-overview)
2. [Sequential Orchestration](#sequential-orchestration)
3. [Concurrent Orchestration](#concurrent-orchestration)
4. [Handoff Orchestration](#handoff-orchestration)
5. [Group Chat Orchestration](#group-chat-orchestration)
6. [Magentic Orchestration](#magentic-orchestration)
7. [Pattern Selection Guide](#pattern-selection-guide)
8. [Real-World Examples](#real-world-examples)

---

## Orchestration Overview

Multi-agent orchestration coordinates multiple specialized agents to solve complex tasks. The framework provides five built-in patterns, each suited to different scenarios.

### The Five Patterns

| Pattern | Data Flow | Best For |
|---------|-----------|----------|
| **Sequential** | A → B → C | Linear pipelines, staged processing |
| **Concurrent** | A → [B, C, D] → E | Parallel independent analysis |
| **Handoff** | Router → Specialist | Dynamic task routing |
| **Group Chat** | All ↔ All (managed) | Collaborative problem-solving |
| **Magentic** | Manager ↔ Workers | Complex, open-ended tasks |

---

## Sequential Orchestration

Agents execute one after another, each building on the previous output.

```
Agent A → Agent B → Agent C → Final Result
```

### Implementation

```python
from agent_framework import SequentialOrchestration

# Define specialist agents
researcher = client.as_agent(
    name="Researcher",
    instructions="Research the topic and compile key findings.",
    tools=[search_web, search_academic],
)

analyst = client.as_agent(
    name="Analyst",
    instructions="Analyze research findings and extract insights. Focus on trends and patterns.",
)

writer = client.as_agent(
    name="Writer",
    instructions="Write a polished report from the analysis. Use clear language and structure.",
)

# Create sequential pipeline
pipeline = SequentialOrchestration(
    agents=[researcher, analyst, writer],
)

result = await pipeline.run("Analyze the current state of quantum computing")
```

### When to Use
- Document processing: extract → analyze → summarize
- Content creation: research → draft → edit
- Data pipelines: fetch → clean → transform → load
- Quality assurance: generate → review → approve

### Trade-offs
- Simple and predictable
- Early failures propagate downstream
- No parallelism — total time = sum of all steps
- Each agent only sees output from the previous one

---

## Concurrent Orchestration

Multiple agents work in parallel on the same input, results aggregated.

```
         ├→ Agent B ┐
Input ───┤→ Agent C ├───→ Aggregator → Result
         └→ Agent D ┘
```

### Implementation

```python
from agent_framework import ConcurrentOrchestration

# Multiple analysts with different perspectives
market_analyst = client.as_agent(
    name="MarketAnalyst",
    instructions="Analyze from a market/competitive perspective.",
)

tech_analyst = client.as_agent(
    name="TechAnalyst",
    instructions="Analyze from a technical feasibility perspective.",
)

risk_analyst = client.as_agent(
    name="RiskAnalyst",
    instructions="Analyze potential risks and challenges.",
)

synthesizer = client.as_agent(
    name="Synthesizer",
    instructions="Combine multiple analyses into a balanced, comprehensive assessment.",
)

# Run analyses concurrently, then synthesize
concurrent = ConcurrentOrchestration(
    parallel_agents=[market_analyst, tech_analyst, risk_analyst],
    aggregator=synthesizer,
)

result = await concurrent.run("Should we invest in building an AI agent platform?")
```

### When to Use
- Multi-perspective analysis
- Ensemble methods (multiple LLMs, compare outputs)
- Independent subtasks that can run in parallel
- Voting/consensus systems

### Trade-offs
- Faster than sequential for independent tasks
- Higher cost (multiple LLM calls simultaneously)
- Requires conflict resolution when agents disagree
- Aggregation step adds complexity

---

## Handoff Orchestration

A router agent dynamically transfers control to specialist agents based on context.

```
              ├→ Sales Agent
User → Router ┤→ Support Agent
              └→ Technical Agent
```

### Implementation

```python
from agent_framework import HandoffOrchestration

# Specialist agents
sales_agent = client.as_agent(
    name="SalesAgent",
    instructions="""You handle sales inquiries: pricing, plans, discounts, demos.
    Be enthusiastic and helpful. Always try to understand the customer's needs.""",
    tools=[check_pricing, schedule_demo],
)

support_agent = client.as_agent(
    name="SupportAgent",
    instructions="""You handle technical support: bugs, errors, how-to questions.
    Be patient and thorough. Ask for error messages and reproduction steps.""",
    tools=[search_kb, create_ticket],
)

billing_agent = client.as_agent(
    name="BillingAgent",
    instructions="""You handle billing: invoices, payments, refunds, account changes.
    Be precise with amounts and dates.""",
    tools=[check_invoice, process_refund],
)

# Router decides who handles each request
handoff = HandoffOrchestration(
    agents=[sales_agent, support_agent, billing_agent],
    router_instructions="""Route customer requests to the right specialist:
    - Sales: pricing, plans, demos, new features
    - Support: bugs, errors, how-to, troubleshooting
    - Billing: invoices, payments, refunds, subscriptions""",
)

result = await handoff.run("I'm getting error 500 when I try to upload files")
# → Routes to SupportAgent
```

### When to Use
- Customer support with different departments
- Task routing based on intent classification
- Specialist systems where different agents have different tools
- Tiered support (L1 → L2 → L3)

### Trade-offs
- Flexible and natural
- Routing accuracy depends on LLM quality
- Complexity increases with number of specialists
- Handoff context must be properly transferred

---

## Group Chat Orchestration

Multiple agents collaborate in a shared conversation, coordinated by a manager.

```
Manager → selects speaker
  ↕
Agent A ↔ Agent B ↔ Agent C
  (shared conversation thread)
```

### Implementation

```python
from agent_framework import GroupChatOrchestration

# Team of collaborating agents
planner = client.as_agent(
    name="Planner",
    instructions="You break down complex tasks into steps and assign them.",
)

coder = client.as_agent(
    name="Coder",
    instructions="You write code based on specifications. Ask Planner for clarification.",
)

reviewer = client.as_agent(
    name="Reviewer",
    instructions="You review code for bugs, security issues, and best practices.",
)

tester = client.as_agent(
    name="Tester",
    instructions="You write and run tests for the code.",
)

# Group chat with manager coordination
group = GroupChatOrchestration(
    agents=[planner, coder, reviewer, tester],
    manager_instructions="""Coordinate the team to build software:
    1. Planner breaks down the task
    2. Coder implements
    3. Reviewer reviews
    4. Tester tests
    Repeat until quality is satisfactory.""",
    max_rounds=10,
)

result = await group.run("Build a REST API for a todo list application")
```

### When to Use
- Collaborative problem-solving
- Iterative refinement (draft → review → revise)
- Brainstorming and ideation
- Complex tasks requiring multiple expertise areas

### Trade-offs
- Most flexible pattern
- Token usage can escalate quickly (all agents see full chat)
- Harder to predict execution path
- Manager quality is critical for efficiency

---

## Magentic Orchestration

A manager agent dynamically decomposes tasks and coordinates workers, adapting its plan as it goes.

```
Manager
  ↓ decomposes task
  ├→ Worker A (subtask 1)
  ├→ Worker B (subtask 2)
  ↓ reviews results
  ├→ Worker A (refinement)
  ↓ synthesizes
  Final Result
```

### Implementation

```python
from agent_framework import MagenticOrchestration

# Worker agents with different capabilities
web_researcher = client.as_agent(
    name="WebResearcher",
    instructions="Search the web for current information.",
    tools=[search_web],
)

data_analyst = client.as_agent(
    name="DataAnalyst",
    instructions="Analyze data and create visualizations.",
    tools=[code_interpreter],
)

report_writer = client.as_agent(
    name="ReportWriter",
    instructions="Write clear, professional reports.",
)

# Magentic orchestration — manager plans dynamically
magentic = MagenticOrchestration(
    agents=[web_researcher, data_analyst, report_writer],
    manager_instructions="""You are a project manager. Given a complex task:
    1. Break it into subtasks
    2. Assign subtasks to the most appropriate worker
    3. Review results and iterate if needed
    4. Synthesize into a final deliverable""",
    max_iterations=5,
)

result = await magentic.run(
    "Create a comprehensive market analysis of the AI agent framework space in 2026"
)
```

### When to Use
- Complex, open-ended tasks
- Tasks where the plan isn't clear upfront
- Research projects requiring iterative exploration
- Tasks needing dynamic resource allocation

### Trade-offs
- Most powerful but least predictable
- Higher cost due to iterative planning
- Manager LLM quality is critical
- Harder to debug and control

---

## Pattern Selection Guide

### Decision Tree

```
Is the task a linear pipeline?
  → YES: Sequential

Can subtasks run independently?
  → YES: Concurrent

Does the task need routing to specialists?
  → YES: Handoff

Do agents need to collaborate iteratively?
  → YES: Is the plan known upfront?
    → YES: Group Chat
    → NO: Magentic
```

### Comparison Matrix

| Factor | Sequential | Concurrent | Handoff | Group Chat | Magentic |
|--------|:---------:|:---------:|:-------:|:---------:|:--------:|
| **Complexity** | Low | Medium | Medium | High | High |
| **Speed** | Slow | Fast | Medium | Slow | Variable |
| **Cost** | Low | Higher | Medium | Highest | Variable |
| **Control** | High | Medium | Medium | Low | Medium |
| **Flexibility** | Low | Medium | High | High | Highest |
| **Predictability** | High | High | Medium | Low | Low |

---

## Real-World Examples

### Customer Support System

```python
# Tiered support with handoff
l1_agent = client.as_agent(name="L1", instructions="Basic support. Escalate complex issues.")
l2_agent = client.as_agent(name="L2", instructions="Advanced support with DB access.", tools=[query_db])
l3_agent = client.as_agent(name="L3", instructions="Expert engineering support.", tools=[access_logs, restart_service])

support = HandoffOrchestration(
    agents=[l1_agent, l2_agent, l3_agent],
    router_instructions="Route based on complexity: simple → L1, complex → L2, critical → L3",
)
```

### Content Creation Pipeline

```python
# Sequential content pipeline
pipeline = SequentialOrchestration(agents=[
    client.as_agent(name="TopicResearcher", instructions="Research trending topics"),
    client.as_agent(name="OutlineWriter", instructions="Create article outline"),
    client.as_agent(name="DraftWriter", instructions="Write first draft from outline"),
    client.as_agent(name="Editor", instructions="Edit for clarity, grammar, style"),
    client.as_agent(name="SEOOptimizer", instructions="Optimize for search engines"),
])
```

### Multi-Perspective Analysis

```python
# Concurrent analysis from different angles
analysis = ConcurrentOrchestration(
    parallel_agents=[
        client.as_agent(name="Bull", instructions="Make the strongest bullish case"),
        client.as_agent(name="Bear", instructions="Make the strongest bearish case"),
        client.as_agent(name="Neutral", instructions="Provide balanced, objective analysis"),
    ],
    aggregator=client.as_agent(
        name="Synthesis",
        instructions="Synthesize bull, bear, and neutral perspectives into a balanced report",
    ),
)
```

### Software Development Team

```python
# Group chat for collaborative development
dev_team = GroupChatOrchestration(
    agents=[
        client.as_agent(name="ProductManager", instructions="Define requirements and priorities"),
        client.as_agent(name="Architect", instructions="Design system architecture"),
        client.as_agent(name="Developer", instructions="Implement code", tools=[code_interpreter]),
        client.as_agent(name="QA", instructions="Test and find bugs"),
    ],
    max_rounds=15,
)
```
