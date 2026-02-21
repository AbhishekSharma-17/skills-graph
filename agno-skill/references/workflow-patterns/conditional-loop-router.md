# Conditional, Loop & Router Workflow Patterns

## Contents
- [Conditional Workflow](#1-conditional-workflow)
- [If/Else Branching](#ifelse-branching)
- [Loop Workflow](#2-loop-workflow)
- [Router Workflow](#3-router-workflow)
- [Early Stopping (Security Gate)](#4-early-stopping)

Complete code examples — each is self-contained and runnable.

---

## 1. Conditional Workflow

Execute steps only when a condition is met. Supports both if and if/else branching.

**Use when:** quality gates, content-specific processing, adaptive pipelines.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Condition, Step, Workflow
from agno.workflow.types import StepInput
from agno.tools.hackernews import HackerNewsTools

researcher = Agent(
    name="Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Research the given topic thoroughly"],
)

summarizer = Agent(
    name="Summarizer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Create a concise summary of the research findings"],
)

fact_checker = Agent(
    name="Fact Checker",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Verify facts and check for accuracy in the research"],
)

writer = Agent(
    name="Writer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Write a comprehensive article based on all available research"],
)


def needs_fact_checking(step_input: StepInput) -> bool:
    """Check if the research contains claims that need verification."""
    summary = step_input.previous_step_content or ""
    indicators = [
        "study shows", "research indicates", "statistics",
        "data shows", "survey", "million", "billion", "%",
    ]
    return any(ind in summary.lower() for ind in indicators)


workflow = Workflow(
    name="Research Workflow",
    steps=[
        Step(name="research", agent=researcher),
        Step(name="summarize", agent=summarizer),
        Condition(
            name="fact_check_condition",
            description="Check if fact-checking is needed",
            evaluator=needs_fact_checking,
            steps=[Step(name="fact_check", agent=fact_checker)],
        ),
        Step(name="write_article", agent=writer),
    ],
)

workflow.print_response("Recent breakthroughs in quantum computing", stream=True)
```

### If/Else Branching

```python
def is_technical_issue(step_input: StepInput) -> bool:
    text = (step_input.input or "").lower()
    tech_keywords = ["error", "bug", "crash", "not working", "api", "timeout"]
    return any(kw in text for kw in tech_keywords)

workflow = Workflow(
    name="Support Router",
    steps=[
        Condition(
            name="TechnicalTriage",
            evaluator=is_technical_issue,
            steps=[
                Step(name="Diagnose", agent=diagnostic_agent),
                Step(name="Engineer", agent=engineering_agent),
            ],
            else_steps=[
                Step(name="GeneralSupport", agent=general_support_agent),
            ],
        ),
        Step(name="FollowUp", agent=followup_agent),
    ],
)
```

---

## 2. Loop Workflow

Repeat steps until a condition is met or max iterations are reached.

**Use when:** iterative refinement, quality-driven research, retry logic.

```python
from typing import List
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Loop, Step, Workflow
from agno.workflow.types import StepOutput
from agno.tools.hackernews import HackerNewsTools

research_agent = Agent(
    name="Researcher",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Research the topic and provide detailed findings"],
)

content_agent = Agent(
    name="Content Creator",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Write an article based on all research gathered"],
)


def research_evaluator(outputs: List[StepOutput]) -> bool:
    """Return True to stop the loop (research is sufficient)."""
    if not outputs:
        return False

    for output in outputs:
        if output.content and len(output.content) > 200:
            print(f"Research sufficient - {len(output.content)} chars")
            return True  # Stop looping

    print("Research insufficient - continuing loop")
    return False  # Keep looping


workflow = Workflow(
    name="Iterative Research",
    steps=[
        Loop(
            name="Research Loop",
            steps=[
                Step(name="Research HackerNews", agent=research_agent),
                Step(name="Research Web", agent=research_agent),
            ],
            end_condition=research_evaluator,
            max_iterations=3,
        ),
        Step(name="Create Content", agent=content_agent),
    ],
)

workflow.print_response("Research latest trends in AI and machine learning")
```

**How end_condition works:**
- Receives `List[StepOutput]` — outputs from steps within the current iteration
- Return `True` to break the loop
- Return `False` to continue looping
- `max_iterations` is a safety cap

---

## 3. Router Workflow

Dynamically select which step(s) to execute based on input analysis.

**Use when:** topic-specific pipelines, expertise routing, different subjects need different strategies.

```python
from typing import List
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Router, Step, Workflow
from agno.workflow.types import StepInput
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools

hackernews_agent = Agent(
    name="HackerNews Agent",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions=["Research tech trends from HackerNews"],
)

finance_agent = Agent(
    name="Finance Agent",
    model=OpenAIResponses(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True)],
    instructions=["Get financial data and market analysis"],
)

content_agent = Agent(
    name="Content Writer",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Write an article based on the research provided"],
)

# Define the possible routes as Steps
research_hackernews = Step(
    name="research_hackernews",
    agent=hackernews_agent,
    description="Research tech from HackerNews",
)

research_finance = Step(
    name="research_finance",
    agent=finance_agent,
    description="Research financial data",
)


def research_router(step_input: StepInput) -> List[Step]:
    """Select research strategy based on topic."""
    topic = (step_input.previous_step_content or step_input.input or "").lower()

    tech_keywords = ["startup", "programming", "ai", "machine learning", "software", "tech"]

    if any(kw in topic for kw in tech_keywords):
        return [research_hackernews]
    else:
        return [research_finance]


workflow = Workflow(
    name="Intelligent Research",
    steps=[
        Router(
            name="research_strategy_router",
            selector=research_router,
            choices=[research_hackernews, research_finance],
            description="Select research method based on topic",
        ),
        Step(name="publish", agent=content_agent),
    ],
)

workflow.print_response("Latest developments in artificial intelligence")
```

**Router vs Condition:**
- **Router** selects which path to take (mutually exclusive choices)
- **Condition** decides whether to run additional steps (additive)

---

## 4. Early Stopping

Use `stop=True` in a StepOutput to immediately halt the workflow.

```python
from agno.workflow import Step, Workflow, StepInput, StepOutput

def security_gate(step_input: StepInput) -> StepOutput:
    """Block deployment if vulnerabilities are found."""
    scan_result = step_input.previous_step_content or ""

    if "VULNERABLE" in scan_result.upper():
        return StepOutput(
            content="SECURITY ALERT: Critical vulnerabilities. Deployment blocked.",
            stop=True,  # Entire workflow stops here
        )

    return StepOutput(content="Security check passed.", stop=False)

workflow = Workflow(
    name="Secure Deployment",
    steps=[
        Step(name="Security Scan", agent=security_scanner),
        Step(name="Security Gate", executor=security_gate),   # May stop here
        Step(name="Deploy Code", agent=code_deployer),        # Only runs if secure
        Step(name="Setup Monitoring", agent=monitoring_agent),
    ],
)
```
