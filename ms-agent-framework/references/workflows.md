# Workflows — Graph-Based Orchestration

## Table of Contents
1. [Workflow Fundamentals](#workflow-fundamentals)
2. [Creating Workflows](#creating-workflows)
3. [Workflow Patterns](#workflow-patterns)
4. [Conditional Routing](#conditional-routing)
5. [Checkpointing & Recovery](#checkpointing--recovery)
6. [Human-in-the-Loop](#human-in-the-loop)
7. [Nested Workflows](#nested-workflows)
8. [Workflow with Agents](#workflow-with-agents)
9. [Error Handling](#error-handling)

---

## Workflow Fundamentals

A Workflow is a directed graph of execution units (agents or functions) connected by edges. Data flows from unit to unit, with optional conditions on edges.

### When to Use Workflows (vs Agents)

| Use Workflows When | Use Agents When |
|-------------------|-----------------|
| Process has well-defined steps | Task is open-ended |
| Need explicit control over execution order | Agent should autonomously decide |
| Multiple agents must coordinate | Single LLM call suffices |
| Need checkpointing/recovery | Simple request-response |
| Human approval gates needed | Conversational interaction |

### Anatomy

```
Entry Point → Unit A → [Condition?] → Unit B → Unit C → Exit Point
                                    ↘ Unit D ↗
```

- **ExecutionUnit**: A node — either an agent or an async function
- **Edge**: Connection between units, optionally conditional
- **Entry Point**: Where execution starts
- **Exit Point**: Where execution ends and results return

---

## Creating Workflows

### Minimal Workflow

```python
from agent_framework import Workflow

async def step1(input_data: dict) -> dict:
    return {"processed": input_data["raw"].upper()}

async def step2(input_data: dict) -> dict:
    return {"result": f"Final: {input_data['processed']}"}

wf = Workflow("SimpleWorkflow")
wf.add_execution_unit("process", step1)
wf.add_execution_unit("finalize", step2)
wf.add_edge("process", "finalize")
wf.set_entry_point("process")
wf.set_exit_point("finalize")

result = await wf.run_from_input({"raw": "hello world"})
# result = {"result": "Final: HELLO WORLD"}
```

### Workflow API

```python
class Workflow:
    def __init__(self, name: str)

    def add_execution_unit(
        self,
        name: str,                          # Unique identifier
        executor: Union[Agent, Callable],   # Agent or async function
    ) -> ExecutionUnit

    def add_edge(
        self,
        from_name: str,                     # Source unit
        to_name: str,                       # Target unit
        condition: Optional[Callable] = None,  # Optional gate
    ) -> None

    def set_entry_point(self, unit_name: str) -> None
    def set_exit_point(self, unit_name: str) -> None

    async def run_from_input(self, input_data: dict) -> dict
    async def checkpoint(self, checkpoint_id: str, state: dict) -> None
    async def restore_from_checkpoint(self, checkpoint_id: str) -> dict
```

---

## Workflow Patterns

### Sequential Pipeline

```
A → B → C → D
```

```python
wf = Workflow("Pipeline")

async def extract(data): return {"text": data["document"]}
async def transform(data): return {"cleaned": clean(data["text"])}
async def analyze(data): return {"insights": analyze(data["cleaned"])}
async def report(data): return {"report": format_report(data["insights"])}

for name, fn in [("extract", extract), ("transform", transform),
                  ("analyze", analyze), ("report", report)]:
    wf.add_execution_unit(name, fn)

wf.add_edge("extract", "transform")
wf.add_edge("transform", "analyze")
wf.add_edge("analyze", "report")
wf.set_entry_point("extract")
wf.set_exit_point("report")
```

### Fan-Out / Fan-In (Concurrent)

```
       ├→ B ┐
  A ───┤    ├──→ D (merge)
       └→ C ┘
```

```python
import asyncio

wf = Workflow("FanOutFanIn")

async def distribute(data):
    return {"items": data["items"]}

async def process_batch_1(data):
    return {"results_1": [process(x) for x in data["items"][:5]]}

async def process_batch_2(data):
    return {"results_2": [process(x) for x in data["items"][5:]]}

async def merge_results(data):
    all_results = data.get("results_1", []) + data.get("results_2", [])
    return {"final": all_results}

wf.add_execution_unit("distribute", distribute)
wf.add_execution_unit("batch1", process_batch_1)
wf.add_execution_unit("batch2", process_batch_2)
wf.add_execution_unit("merge", merge_results)

wf.add_edge("distribute", "batch1")
wf.add_edge("distribute", "batch2")
wf.add_edge("batch1", "merge")
wf.add_edge("batch2", "merge")
wf.set_entry_point("distribute")
wf.set_exit_point("merge")
```

### Loop / Iteration

```
A → B → [Check] → B (retry) OR → C (done)
```

```python
async def generate_draft(data):
    # Generate or regenerate content
    return {"draft": await llm_generate(data["prompt"]), "attempts": data.get("attempts", 0) + 1}

async def review_draft(data):
    score = await evaluate(data["draft"])
    return {**data, "score": score, "passed": score > 0.8}

async def finalize(data):
    return {"final_output": data["draft"]}

wf = Workflow("IterativeRefinement")
wf.add_execution_unit("generate", generate_draft)
wf.add_execution_unit("review", review_draft)
wf.add_execution_unit("finalize", finalize)

wf.add_edge("generate", "review")
wf.add_edge("review", "finalize", condition=lambda d: d["passed"] or d["attempts"] >= 3)
wf.add_edge("review", "generate", condition=lambda d: not d["passed"] and d["attempts"] < 3)
wf.set_entry_point("generate")
wf.set_exit_point("finalize")
```

---

## Conditional Routing

### Simple Condition

```python
def is_high_priority(output):
    return output.get("priority") == "high"

def is_low_priority(output):
    return output.get("priority") != "high"

wf.add_edge("classify", "urgent_handler", condition=is_high_priority)
wf.add_edge("classify", "normal_handler", condition=is_low_priority)
```

### Multi-Way Routing

```python
async def classify_intent(data):
    intent = await detect_intent(data["message"])
    return {**data, "intent": intent}

wf.add_execution_unit("classify", classify_intent)
wf.add_execution_unit("handle_sales", sales_agent)
wf.add_execution_unit("handle_support", support_agent)
wf.add_execution_unit("handle_general", general_agent)

wf.add_edge("classify", "handle_sales", condition=lambda d: d["intent"] == "sales")
wf.add_edge("classify", "handle_support", condition=lambda d: d["intent"] == "support")
wf.add_edge("classify", "handle_general", condition=lambda d: d["intent"] == "general")
```

---

## Checkpointing & Recovery

Workflows can save state at any point and resume from that state later.

### Save Checkpoint

```python
class CheckpointedWorkflow(Workflow):
    async def run(self, input_data):
        result1 = await self.execute_unit("step1", input_data)
        await self.checkpoint("after_step1", result1)

        result2 = await self.execute_unit("step2", result1)
        await self.checkpoint("after_step2", result2)

        return await self.execute_unit("step3", result2)
```

### Resume from Checkpoint

```python
# If step2 failed, resume from after_step1
state = await wf.restore_from_checkpoint("after_step1")
result = await wf.run_from_input(state)  # Resumes from step2
```

### Durable Workflow (Azure)

```python
from agent_framework.durabletask import DurableWorkflow

class LongRunningWorkflow(DurableWorkflow):
    """Automatically persists to Azure Durable Tasks"""

    async def run(self, input_data):
        # Each step is automatically checkpointed
        data = await self.call_activity("fetch_data", input_data)
        analysis = await self.call_activity("analyze", data)
        report = await self.call_activity("generate_report", analysis)
        return report
```

---

## Human-in-the-Loop

Pause workflow for human approval:

```python
async def generate_email(data):
    return {"email_draft": await draft_email(data)}

async def await_approval(data):
    """This function pauses and waits for human input"""
    # Framework handles the pause/resume
    return {**data, "approved": True}  # Human sets this

async def send_email(data):
    if data["approved"]:
        await actually_send(data["email_draft"])
        return {"status": "sent"}
    return {"status": "cancelled"}

wf = Workflow("EmailApproval")
wf.add_execution_unit("draft", generate_email)
wf.add_execution_unit("approve", await_approval)  # Pauses here
wf.add_execution_unit("send", send_email)

wf.add_edge("draft", "approve")
wf.add_edge("approve", "send")
wf.set_entry_point("draft")
wf.set_exit_point("send")
```

---

## Nested Workflows

Compose workflows inside other workflows:

```python
# Sub-workflow: Data Processing
data_wf = Workflow("DataProcessing")
data_wf.add_execution_unit("clean", clean_data)
data_wf.add_execution_unit("validate", validate_data)
data_wf.add_edge("clean", "validate")
data_wf.set_entry_point("clean")
data_wf.set_exit_point("validate")

# Sub-workflow: Report Generation
report_wf = Workflow("ReportGeneration")
report_wf.add_execution_unit("analyze", analyze_data)
report_wf.add_execution_unit("format", format_report)
report_wf.add_edge("analyze", "format")
report_wf.set_entry_point("analyze")
report_wf.set_exit_point("format")

# Parent workflow
main_wf = Workflow("MainPipeline")
main_wf.add_execution_unit("ingest", ingest_data)
main_wf.add_execution_unit("process", data_wf)       # Nested workflow
main_wf.add_execution_unit("report", report_wf)       # Nested workflow
main_wf.add_execution_unit("deliver", deliver_report)

main_wf.add_edge("ingest", "process")
main_wf.add_edge("process", "report")
main_wf.add_edge("report", "deliver")
main_wf.set_entry_point("ingest")
main_wf.set_exit_point("deliver")
```

---

## Workflow with Agents

Mix agents and functions in the same workflow:

```python
# Agent-based units
research_agent = client.as_agent(
    name="Researcher",
    instructions="Research the given topic thoroughly.",
    tools=[search_web],
)

writer_agent = client.as_agent(
    name="Writer",
    instructions="Write a clear, engaging article from research notes.",
)

# Function-based units
async def format_output(data):
    return {"article": add_formatting(data["raw_article"])}

# Compose
wf = Workflow("ContentPipeline")
wf.add_execution_unit("research", research_agent)
wf.add_execution_unit("write", writer_agent)
wf.add_execution_unit("format", format_output)

wf.add_edge("research", "write")
wf.add_edge("write", "format")
wf.set_entry_point("research")
wf.set_exit_point("format")

result = await wf.run_from_input({"topic": "quantum computing breakthroughs 2026"})
```

---

## Error Handling

### Try/Catch in Units

```python
async def resilient_step(data):
    try:
        result = await risky_operation(data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Route based on success/failure
wf.add_edge("risky", "continue", condition=lambda d: d["success"])
wf.add_edge("risky", "fallback", condition=lambda d: not d["success"])
```

### Retry Pattern

```python
async def with_retry(data):
    for attempt in range(3):
        try:
            return await external_api_call(data)
        except Exception as e:
            if attempt == 2:
                return {"error": f"Failed after 3 attempts: {e}"}
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Workflow-Level Error Handling

```python
try:
    result = await wf.run_from_input(input_data)
except WorkflowExecutionError as e:
    print(f"Workflow failed at step: {e.failed_unit}")
    print(f"Error: {e.message}")

    # Try to resume from last checkpoint
    if e.last_checkpoint:
        state = await wf.restore_from_checkpoint(e.last_checkpoint)
        result = await wf.run_from_input(state)
```
