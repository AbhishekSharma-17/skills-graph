# Reasoning — Complete Examples

## 1. Basic Reasoning Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    name="Reasoning Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=6,
)

agent.print_response(
    "A bat and ball cost $1.10 total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    stream=True,
    show_full_reasoning=True,
)
```

## 2. Split Reasoning + Response Models

Use a fast model for reasoning, a capable model for the final response:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    reasoning_model=OpenAIResponses(id="gpt-5-mini"),
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=5,
    markdown=True,
)

agent.print_response(
    "A farmer has 17 sheep. All but 9 die. How many sheep are left?",
    stream=True,
    show_full_reasoning=True,
)
```

## 3. DeepSeek-R1 + Claude

Use DeepSeek for reasoning (via Groq for speed), Claude for the polished response:

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.groq import Groq

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    reasoning_model=Groq(
        id="deepseek-r1-distill-llama-70b",
        temperature=0.6,
        max_tokens=1024,
        top_p=0.95,
    ),
)

agent.print_response("9.11 and 9.9 -- which is bigger?", stream=True, show_full_reasoning=True)
```

## 4. Claude Extended Thinking

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

agent = Agent(
    reasoning_model=Claude(
        id="claude-sonnet-4-5",
        thinking={"type": "enabled", "budget_tokens": 1024},
    ),
    reasoning=True,
    instructions="Think step by step about the problem.",
)

agent.print_response("What are the ethical implications of autonomous vehicles?", stream=True)
```

## 5. Reasoning Model with reasoning_effort

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2", reasoning_effort="high"),
    tools=[HackerNewsTools()],
    markdown=True,
)

agent.print_response("What are the top stories on HN and why are they significant?", stream=True)
```

## 6. ReasoningTools with Any Model

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ReasoningTools(add_instructions=True)],
)

agent.print_response(
    "Which is bigger: 9.11 or 9.9? Explain your reasoning.",
    stream=True,
)
```

## 7. KnowledgeTools with Reasoning

```python
from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.models.openai import OpenAIResponses
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.pgvector import PgVector

knowledge = PDFKnowledgeBase(
    path="data/research_papers/",
    vector_db=PgVector(
        table_name="research_papers",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    ),
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[KnowledgeTools(knowledge=knowledge, add_instructions=True)],
    instructions="Search thoroughly and cite your sources",
)
agent.print_response("What are the latest findings on quantum entanglement?", stream=True)
```

## 8. Combined Reasoning + Knowledge + Memory

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.memory import MemoryTools

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[
        ReasoningTools(add_instructions=True),
        KnowledgeTools(
            knowledge=my_knowledge,
            enable_think=False, enable_analyze=False,
            add_instructions=False,
        ),
        MemoryTools(
            db=db,
            enable_think=False, enable_analyze=False,
            add_instructions=False,
        ),
    ],
    db=db,
    instructions="Use reasoning for planning, knowledge for facts, memory for personalization",
)
```

## 9. Reasoning Agent with Tools

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    instructions=["Use tables to display data"],
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=15,
    markdown=True,
)

agent.print_response(
    "Compare NVDA, AMD, and INTC. What are the key drivers?",
    stream=True,
    show_full_reasoning=True,
)
```

## 10. Streaming Reasoning Events

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunEvent

agent = Agent(model=OpenAIResponses(id="gpt-5.2"), reasoning=True)

for event in agent.run("What is 25 * 37? Show your reasoning.", stream=True, stream_events=True):
    if event.event == RunEvent.reasoning_started:
        print("--- Reasoning ---")
    elif event.event == RunEvent.reasoning_content_delta:
        print(event.reasoning_content, end="", flush=True)
    elif event.event == RunEvent.run_content:
        if event.content:
            print(event.content, end="", flush=True)
    elif event.event == RunEvent.run_completed:
        print("\n--- Done ---")
```

## 11. WorkflowTools with Reasoning

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.workflow import WorkflowTools
from agno.workflow import Workflow
from agno.workflow.step import Step

research_workflow = Workflow(
    name="research-workflow",
    steps=[
        Step(name="search", agent=search_agent),
        Step(name="summarize", agent=summary_agent),
        Step(name="fact-check", agent=fact_check_agent),
    ],
)

orchestrator = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[WorkflowTools(workflow=research_workflow, add_instructions=True)],
)
orchestrator.print_response("Research climate change impacts on agriculture", stream=True)
```

## When to Use What

| Scenario | Approach |
|----------|----------|
| Model already has reasoning (GPT-5, DeepSeek-R1) | Reasoning Models — just use the model |
| Need structured thinking with any model | ReasoningTools — explicit think/analyze |
| Multi-step problems with tool use | Reasoning Agents — `reasoning=True` |
| Reasoning + knowledge search | KnowledgeTools |
| Reasoning + user personalization | MemoryTools |
| Reasoning + workflow orchestration | WorkflowTools |
| Want cheap reasoning + quality response | Split models: `reasoning_model` + `model` |
| Need full control over reasoning process | Custom `reasoning_agent` |
