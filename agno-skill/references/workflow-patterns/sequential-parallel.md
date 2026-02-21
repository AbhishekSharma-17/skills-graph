# Sequential & Parallel Workflow Patterns

## Contents
- [Sequential Workflow](#1-sequential-workflow)
- [Parallel Workflow](#2-parallel-workflow)
- [Parallel to Sequential Pipeline](#3-parallel-to-sequential-pipeline)

Complete code examples — each is self-contained and runnable.

---

## 1. Sequential Workflow

Steps run one after another. Output from each step flows as input to the next.

**Use when:** linear processes with clear phases (research -> summarize -> write).

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Step, Workflow
from agno.tools.hackernews import HackerNewsTools

researcher = Agent(
    name="Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Find relevant information about the topic", "Provide detailed findings"],
)

writer = Agent(
    name="Writer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Write a clear, engaging article based on the research provided"],
)

workflow = Workflow(
    name="Content Creation",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Write Article", agent=writer),
    ],
)

workflow.print_response("Write an article about AI trends", stream=True, markdown=True)
```

**Minimal form** — agents directly in steps list (auto-wrapped):
```python
workflow = Workflow(
    name="Content Creation",
    steps=[researcher, writer],
)
```

---

## 2. Parallel Workflow

Independent steps execute simultaneously. Outputs are joined before the next sequential step.

**Use when:** multiple independent data sources, parallel research, or tasks that don't depend on each other.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Parallel, Step, Workflow
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools

news_researcher = Agent(
    name="News Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Find trending tech news and summarize key stories"],
)

finance_researcher = Agent(
    name="Finance Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True)],
    instructions=["Get stock data and analyst recommendations"],
)

writer = Agent(
    name="Writer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Combine research from all sources into a cohesive article"],
)

workflow = Workflow(
    name="Research Pipeline",
    steps=[
        Parallel(
            Step(name="Research News", agent=news_researcher),
            Step(name="Research Finance", agent=finance_researcher),
            name="Research Phase",
        ),
        Step(name="Write Article", agent=writer),
    ],
)

workflow.print_response(
    "Write about latest AI developments and how NVDA stock is performing",
    stream=True,
    markdown=True,
)
```

**Accessing parallel results in a function step:**
```python
from agno.workflow import StepInput, StepOutput

def combine_research(step_input: StepInput) -> StepOutput:
    # Access individual parallel step outputs by name
    news = step_input.get_step_content("Research News") or ""
    finance = step_input.get_step_content("Research Finance") or ""

    # Or get the parallel group output (dict of all results)
    parallel_data = step_input.get_step_content("Research Phase")

    return StepOutput(
        content=f"News Summary:\n{news}\n\nFinance Summary:\n{finance}",
        step_name="combine_research",
        success=True,
    )
```

---

## 3. Parallel to Sequential Pipeline

A common pattern: gather data from multiple sources in parallel, then synthesize sequentially.

```python
from agno.workflow import Parallel, Step, Workflow

workflow = Workflow(
    name="Market Intelligence",
    steps=[
        # Phase 1: Parallel data gathering
        Parallel(
            Step(name="Tech News", agent=hackernews_agent),
            Step(name="Stock Data", agent=finance_agent),
            Step(name="Social Sentiment", agent=social_agent),
            name="Data Gathering",
        ),
        # Phase 2: Sequential synthesis
        Step(name="Analyze", agent=analyst_agent),
        Step(name="Write Report", agent=report_writer),
    ],
)
```
