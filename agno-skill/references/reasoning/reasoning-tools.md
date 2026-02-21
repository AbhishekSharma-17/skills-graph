# Reasoning Tools

Explicit tools for structured thinking. Give any model chain-of-thought capabilities via `think()` and `analyze()` tools.

## ReasoningTools — General Purpose Thinking

```python
from agno.tools.reasoning import ReasoningTools

ReasoningTools(
    enable_think=True,                   # Enable think() tool (default True)
    enable_analyze=True,                 # Enable analyze() tool (default True)
    all=False,                           # Legacy: enable both
    instructions=None,                   # Custom instructions string
    add_instructions=False,              # Add default instructions to agent
    add_few_shot=False,                  # Add few-shot examples
    few_shot_examples=None,              # Custom few-shot examples string
)
```

### think() Method

Plans next action with structured reasoning:

```python
think(
    session_state: Dict[str, Any],       # Auto-injected
    title: str,                          # Concise title
    thought: str,                        # Detailed reasoning
    action: Optional[str] = None,        # What to do based on thought
    confidence: float = 0.8,             # 0.0 to 1.0
) -> str  # Returns formatted reasoning steps
```

### analyze() Method

Evaluates results and decides next step:

```python
analyze(
    session_state: Dict[str, Any],       # Auto-injected
    title: str,                          # Analysis title
    result: str,                         # Outcome of previous action
    analysis: str,                       # Evaluation of results
    next_action: str = "continue",       # "continue" | "validate" | "final_answer"
    confidence: float = 0.8,             # 0.0 to 1.0
) -> str  # Returns formatted reasoning steps
```

### Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ReasoningTools(add_instructions=True)],
)
agent.print_response("Which is bigger: 9.11 or 9.9?", stream=True)
```

### Configuration Patterns

```python
# Only thinking, no analysis
ReasoningTools(enable_think=True, enable_analyze=False)

# Only analysis
ReasoningTools(enable_think=False, enable_analyze=True)

# Custom instructions
ReasoningTools(
    instructions="""
Use think and analyze for rigorous reasoning:
- Always think before making claims
- Cite evidence in your analysis
- Acknowledge uncertainty
""",
    add_instructions=False,
)

# Custom few-shot examples
ReasoningTools(
    add_instructions=True,
    add_few_shot=True,
    few_shot_examples="""
Example: Medical Diagnosis
User: Patient has fever and cough for 3 days.
Agent thinks:
think(title="Gather Symptoms", thought="Need to collect all symptoms...", action="Ask about additional symptoms", confidence=0.9)
""",
)
```

---

## KnowledgeTools — Reasoning with Knowledge Bases

Combines reasoning with knowledge base search:

```python
from agno.tools.knowledge import KnowledgeTools

KnowledgeTools(
    knowledge=knowledge_base,            # Required: knowledge base instance
    enable_think=True,
    enable_analyze=True,
    add_instructions=False,
    add_few_shot=False,
)
```

**Methods**: `think()`, `search_knowledge()`, `analyze()`

```python
from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.models.openai import OpenAIResponses
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.pgvector import PgVector

knowledge = PDFKnowledgeBase(
    path="data/research_papers/",
    vector_db=PgVector(table_name="papers", db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"),
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[KnowledgeTools(knowledge=knowledge, add_instructions=True)],
    instructions="Search thoroughly and cite your sources",
)
agent.print_response("What are the latest findings on quantum entanglement?", stream=True)
```

---

## MemoryTools — Reasoning about User Memories

Combines reasoning with memory operations:

```python
from agno.tools.memory import MemoryTools

MemoryTools(
    db=database,                         # Required: database instance
    enable_think=True,
    enable_analyze=True,
    add_instructions=False,
    add_few_shot=False,
)
```

**Methods**: `think()`, `get_memories()`, `add_memory()`, `update_memory()`, `delete_memory()`, `analyze()`

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIResponses
from agno.tools.memory import MemoryTools

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[MemoryTools(db=db, add_instructions=True)],
    db=db,
)
agent.print_response("I prefer vegetarian recipes and I'm allergic to nuts.", user_id="user_123")
```

---

## WorkflowTools — Reasoning about Workflow Execution

Combines reasoning with workflow orchestration:

```python
from agno.tools.workflow import WorkflowTools

WorkflowTools(
    workflow=workflow_instance,           # Required: workflow to execute
    enable_think=True,
    enable_analyze=True,
    add_instructions=False,
    add_few_shot=False,
)
```

**Methods**: `think()`, `run_workflow()`, `analyze()`

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

---

## Combining Multiple Reasoning Toolkits

When combining, disable think/analyze on secondary toolkits to avoid duplication:

```python
from agno.tools.reasoning import ReasoningTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.memory import MemoryTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[
        ReasoningTools(add_instructions=True),        # Primary: has think + analyze
        KnowledgeTools(
            knowledge=my_knowledge,
            enable_think=False, enable_analyze=False,  # Disable: use ReasoningTools instead
            add_instructions=False,
        ),
        MemoryTools(
            db=my_db,
            enable_think=False, enable_analyze=False,
            add_instructions=False,
        ),
    ],
    instructions="Use reasoning for planning, knowledge for facts, memory for personalization",
)
```
