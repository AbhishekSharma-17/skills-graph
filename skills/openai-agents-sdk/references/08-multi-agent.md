# Multi-Agent — Orchestration Patterns

> Source: [openai.github.io/openai-agents-python/multi_agent](https://openai.github.io/openai-agents-python/multi_agent/)

## Overview

The SDK supports two primary orchestration patterns for multi-agent systems. Both can be combined within a single application.

## Pattern 1: Handoffs (Decentralized)

Peer agents hand off control to specialists. The receiving agent takes over the conversation.

```
User → Triage Agent → Billing Agent → (responds to user)
                    → Support Agent → (responds to user)
```

```python
from agents import Agent

billing_agent = Agent(
    name="Billing Agent",
    handoff_description="Handles billing, invoices, and payment questions",
    instructions="You are a billing specialist. Help with payments and invoices.",
)

support_agent = Agent(
    name="Support Agent",
    handoff_description="Handles technical support and troubleshooting",
    instructions="You are a tech support specialist. Debug and resolve issues.",
)

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "You are a triage agent. Determine what the user needs and "
        "hand off to the appropriate specialist."
    ),
    handoffs=[billing_agent, support_agent],
)

result = await Runner.run(triage_agent, "I was charged twice for my subscription")
```

### When to Use Handoffs

- Specialist should own the entire response
- Full conversation context needed by the specialist
- User-facing agents with distinct domains
- Customer support routing, language-based routing

## Pattern 2: Agents as Tools (Centralized)

A manager agent invokes specialists as tools, retaining control of the conversation.

```
User → Manager Agent ──┬── calls Analyst (tool) ──→ gets result
                       ├── calls Writer (tool)  ──→ gets result
                       └── synthesizes final response to user
```

```python
from agents import Agent

analyst_agent = Agent(
    name="Data Analyst",
    instructions="Analyze data and return insights. Be concise.",
)

writer_agent = Agent(
    name="Content Writer",
    instructions="Write polished content based on provided information.",
)

manager_agent = Agent(
    name="Project Manager",
    instructions=(
        "You coordinate analysis and content creation. "
        "Use the analyst for data insights, then the writer to polish the output."
    ),
    tools=[
        analyst_agent.as_tool(
            tool_name="analyze_data",
            tool_description="Analyze data and provide insights",
        ),
        writer_agent.as_tool(
            tool_name="write_content",
            tool_description="Write polished content from raw information",
        ),
    ],
)

result = await Runner.run(manager_agent, "Create a report on Q2 sales trends")
```

### When to Use Agents as Tools

- Manager needs to synthesize results from multiple specialists
- Specialists are called selectively based on the task
- Orchestrator should control the narrative
- Complex workflows requiring multiple sub-agent calls

## Combining Patterns

Mix handoffs and agents-as-tools in the same system:

```python
# Specialists that work as tools for the support agent
knowledge_agent = Agent(
    name="Knowledge Base",
    instructions="Search the knowledge base and return relevant articles.",
)

diagnostics_agent = Agent(
    name="Diagnostics",
    instructions="Run diagnostic checks on the user's account.",
)

# Support agent uses specialists as tools
support_agent = Agent(
    name="Support Agent",
    handoff_description="Handles technical support",
    instructions="Help users resolve technical issues.",
    tools=[
        knowledge_agent.as_tool(
            tool_name="search_kb",
            tool_description="Search the knowledge base",
        ),
        diagnostics_agent.as_tool(
            tool_name="run_diagnostics",
            tool_description="Run account diagnostics",
        ),
    ],
)

# Triage hands off to support
triage_agent = Agent(
    name="Triage",
    instructions="Route users to the appropriate department.",
    handoffs=[support_agent, billing_agent],
)
```

## Pattern Comparison

| Aspect | Handoffs | Agents as Tools |
|--------|----------|-----------------|
| Control | Transferred to specialist | Retained by caller |
| History | Full conversation passed | Scoped to tool call |
| Response | Specialist responds directly | Caller synthesizes |
| Parallelism | Sequential (one active agent) | Can call multiple tools |
| Complexity | Simple routing | Complex orchestration |
| Token usage | Full history per agent | Minimal per sub-call |

## Hierarchical Teams

Build multi-level agent hierarchies:

```python
# Level 3: Leaf specialists
api_agent = Agent(name="API Specialist", instructions="Debug API issues.")
db_agent = Agent(name="DB Specialist", instructions="Debug database issues.")

# Level 2: Team leads with specialists
backend_lead = Agent(
    name="Backend Lead",
    instructions="Coordinate backend debugging.",
    tools=[
        api_agent.as_tool(tool_name="api_debug", tool_description="Debug API issues"),
        db_agent.as_tool(tool_name="db_debug", tool_description="Debug DB issues"),
    ],
)

frontend_lead = Agent(
    name="Frontend Lead",
    instructions="Handle frontend issues.",
)

# Level 1: Triage routes to team leads
triage = Agent(
    name="Triage",
    instructions="Route to the appropriate team.",
    handoffs=[backend_lead, frontend_lead],
)
```

## Pipeline Pattern

Chain agents sequentially for multi-step processing:

```python
async def pipeline(user_input: str) -> str:
    # Step 1: Extract structured data
    extractor = Agent(
        name="Extractor",
        instructions="Extract key entities from the text.",
        output_type=ExtractedData,
    )
    extract_result = await Runner.run(extractor, user_input)

    # Step 2: Analyze the extracted data
    analyzer = Agent(
        name="Analyzer",
        instructions="Analyze the extracted entities and provide insights.",
        output_type=Analysis,
    )
    analysis_result = await Runner.run(
        analyzer,
        f"Analyze this data: {extract_result.final_output.model_dump_json()}",
    )

    # Step 3: Generate final report
    reporter = Agent(
        name="Reporter",
        instructions="Write a clear report from the analysis.",
    )
    report_result = await Runner.run(
        reporter,
        f"Write a report based on: {analysis_result.final_output.model_dump_json()}",
    )
    return report_result.final_output
```

## Parallel Execution

Run independent agents concurrently:

```python
import asyncio

async def parallel_analysis(data: str) -> dict:
    sentiment_agent = Agent(name="Sentiment", output_type=SentimentResult, ...)
    topic_agent = Agent(name="Topics", output_type=TopicResult, ...)
    entity_agent = Agent(name="Entities", output_type=EntityResult, ...)

    sentiment, topics, entities = await asyncio.gather(
        Runner.run(sentiment_agent, data),
        Runner.run(topic_agent, data),
        Runner.run(entity_agent, data),
    )

    return {
        "sentiment": sentiment.final_output,
        "topics": topics.final_output,
        "entities": entities.final_output,
    }
```

## Agent Visualization

Generate visual representations of agent relationships:

```python
from agents import Agent
# The SDK supports generating Graphviz/Mermaid diagrams
# of agent networks showing handoffs and tool connections
```

## Common Pitfalls

- **Circular handoffs**: A → B → A creates infinite loops. Use `max_turns` as a safety net
- **Over-orchestration**: Not every task needs multiple agents — a single agent with tools is often simpler
- **Context explosion**: Handoffs transfer full history. For long conversations, use `input_filter` or `nest_handoff_history`
- **Inconsistent instructions**: Ensure handoff descriptions match what agents actually do, or the triage agent will misroute

## Related Topics

- **Handoffs:** `04-handoffs.md` — Detailed handoff configuration
- **Tools:** `02-tools.md` — Agents as tools
- **Agents:** `01-agents.md` — Agent definition and configuration
