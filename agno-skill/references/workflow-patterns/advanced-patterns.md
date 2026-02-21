# Advanced Workflow Patterns

## Contents
- [Mixed Execution (Agents + Teams + Functions)](#1-mixed-execution)
- [Background Execution with Polling](#2-background-execution-with-polling)
- [Conversational Workflow](#3-conversational-workflow)
- [Full Production Example](#4-full-production-example)
- [Passing Additional Data](#5-passing-additional-data)
- [Streaming with Events](#6-streaming-with-events)

Complete code examples — each is self-contained and runnable.

---

## 1. Mixed Execution

Combine agents, teams, and custom functions in a single workflow.

```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIResponses
from agno.workflow import Step, Workflow, StepInput, StepOutput
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools

# Agent
content_planner = Agent(
    name="Content Planner",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Plan a 4-week content schedule with 3 posts per week"],
)

# Team
hackernews_agent = Agent(
    name="HN Agent",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    role="Research tech news from HackerNews",
)

finance_agent = Agent(
    name="Finance Agent",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[YFinanceTools()],
    role="Research financial data",
)

research_team = Team(
    name="Research Team",
    model=OpenAIResponses(id="gpt-4o"),
    members=[hackernews_agent, finance_agent],
    instructions=["Research tech topics and related stocks"],
)


# Custom function
def quality_check(step_input: StepInput) -> StepOutput:
    """Validate the research output meets minimum quality."""
    content = step_input.previous_step_content or ""

    if len(content) < 100:
        return StepOutput(
            content="Content too short - needs more detail",
            step_name="quality_check",
            stop=True,  # Halt the workflow
        )

    return StepOutput(
        content=f"Quality check passed ({len(content)} chars)",
        step_name="quality_check",
        success=True,
    )


workflow = Workflow(
    name="Content Pipeline",
    steps=[
        Step(name="Research", team=research_team),         # Team step
        Step(name="Quality Gate", executor=quality_check), # Function step
        Step(name="Plan Content", agent=content_planner),  # Agent step
    ],
)

workflow.print_response("AI trends in 2024", markdown=True)
```

---

## 2. Background Execution with Polling

Run a workflow in the background and poll for results — useful for APIs and UIs.

```python
import asyncio
from agno.workflow import Workflow
from agno.db.sqlite import SqliteDb

workflow = Workflow(
    name="Long Running Pipeline",
    db=SqliteDb(db_file="workflow.db"),  # Required for background execution
    steps=[research_agent, analysis_agent, report_agent],
)


async def main():
    # Start non-blocking
    response = await workflow.arun(input="Comprehensive AI market report", background=True)
    print(f"Run ID: {response.run_id}")

    # Poll until done
    poll_count = 0
    while poll_count < 200:
        poll_count += 1
        result = workflow.get_run(response.run_id)

        if result and result.has_completed():
            print(f"Done!\n{result.content}")
            break

        print(f"Poll #{poll_count} - still running...")
        await asyncio.sleep(5)


asyncio.run(main())
```

---

## 3. Conversational Workflow

Multi-turn chat where a `WorkflowAgent` decides whether to run the workflow or answer from history.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Workflow, WorkflowAgent

story_writer = Agent(
    name="Story Writer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Write a creative short story based on the given prompt"],
)

story_formatter = Agent(
    name="Formatter",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Format the story with proper chapters, headings, and paragraphs"],
)

workflow_agent = WorkflowAgent(
    model=OpenAIResponses(id="gpt-4o"),
    num_history_runs=4,
    instructions="Answer from history when possible, run workflow for new processing",
)

workflow = Workflow(
    name="Story Generator",
    description="Generates and formats stories",
    agent=workflow_agent,
    steps=[story_writer, story_formatter],
)

# First call - runs workflow
workflow.print_response("Tell me a story about a dog named Rocky", stream=True)

# Second call - answers from history (no re-run)
workflow.print_response("What was Rocky's personality?", stream=True)
```

---

## 4. Full Production Example

A complete workflow combining persistence, parallel research, conditional fact-checking, and additional data.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools
from agno.workflow import Condition, Parallel, Step, Workflow, StepInput, StepOutput


# --- Agents ---

hackernews_agent = Agent(
    name="HN Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Research trending tech news", "Provide links and summaries"],
)

finance_agent = Agent(
    name="Finance Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True)],
    instructions=["Get stock data and analyst consensus", "Use tables for data"],
)

fact_checker = Agent(
    name="Fact Checker",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Verify claims and statistics", "Flag anything unverifiable"],
)

writer = Agent(
    name="Report Writer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=[
        "Write a professional market intelligence report",
        "Combine all research into a cohesive narrative",
        "Use headers, tables, and clear prose",
    ],
)


# --- Custom functions ---

def needs_fact_check(step_input: StepInput) -> bool:
    content = step_input.previous_step_content or ""
    indicators = ["million", "billion", "%", "study", "survey", "data shows"]
    return any(ind in content.lower() for ind in indicators)


def add_metadata(step_input: StepInput) -> StepOutput:
    """Add report metadata from additional_data."""
    extra = step_input.additional_data or {}
    article = step_input.previous_step_content or ""

    header = f"**Client:** {extra.get('client', 'N/A')} | **Priority:** {extra.get('priority', 'normal')}\n\n"

    return StepOutput(
        content=header + article,
        step_name="add_metadata",
        success=True,
    )


# --- Workflow ---

pipeline = Workflow(
    name="Market Intelligence Pipeline",
    description="Research, verify, and write market intelligence reports",
    db=SqliteDb(db_file="market_intel.db"),
    steps=[
        # Phase 1: Parallel research
        Parallel(
            Step(name="Tech Research", agent=hackernews_agent),
            Step(name="Finance Research", agent=finance_agent),
            name="Research Phase",
        ),
        # Phase 2: Conditional fact-checking
        Condition(
            name="Fact Check Gate",
            evaluator=needs_fact_check,
            steps=[Step(name="Fact Check", agent=fact_checker)],
        ),
        # Phase 3: Write report
        Step(name="Write Report", agent=writer),
        # Phase 4: Add metadata
        Step(name="Add Metadata", executor=add_metadata),
    ],
)


if __name__ == "__main__":
    pipeline.print_response(
        input="What's trending in AI and how are NVDA and MSFT performing?",
        additional_data={
            "client": "Enterprise Analytics",
            "priority": "high",
            "deadline": "2024-12-15",
        },
        stream=True,
        markdown=True,
    )
```

---

## 5. Passing Additional Data

Any workflow can receive extra context via `additional_data`, accessible in function steps:

```python
def custom_step(step_input: StepInput) -> StepOutput:
    extra = step_input.additional_data or {}
    email = extra.get("user_email", "unknown")
    priority = extra.get("priority", "normal")
    return StepOutput(content=f"Processing for {email} at {priority} priority")

workflow.print_response(
    input="Generate report",
    additional_data={
        "user_email": "analyst@company.com",
        "priority": "high",
        "budget": "$50000",
    },
)
```

---

## 6. Streaming with Events

```python
from agno.run.workflow import WorkflowRunEvent

for event in workflow.run(input="AI trends", stream=True, stream_events=True):
    match event.event:
        case WorkflowRunEvent.workflow_started.value:
            print("Workflow started")
        case WorkflowRunEvent.step_started.value:
            print(f"  Step started: {event}")
        case WorkflowRunEvent.step_completed.value:
            print(f"  Step completed: {event}")
        case WorkflowRunEvent.parallel_execution_started.value:
            print("  Parallel execution started")
        case WorkflowRunEvent.parallel_execution_completed.value:
            print("  Parallel execution completed")
        case WorkflowRunEvent.condition_execution_started.value:
            print("  Condition evaluation started")
        case WorkflowRunEvent.loop_iteration_started.value:
            print("  Loop iteration started")
        case WorkflowRunEvent.workflow_completed.value:
            print("Workflow completed")
```
