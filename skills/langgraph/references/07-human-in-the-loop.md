# LangGraph — Human-in-the-Loop

> Source: [docs.langchain.com/oss/python/langgraph/interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

## Table of Contents

- [Overview](#overview)
- [The interrupt() Function](#the-interrupt-function)
- [Resuming with Command](#resuming-with-command)
- [Static Breakpoints](#static-breakpoints)
- [Approval Workflows](#approval-workflows)
- [Review and Edit Patterns](#review-and-edit-patterns)
- [Tool Call Approval](#tool-call-approval)
- [Input Validation Loops](#input-validation-loops)
- [Multiple Simultaneous Interrupts](#multiple-simultaneous-interrupts)
- [Time-Travel Debugging](#time-travel-debugging)
- [Critical Rules](#critical-rules)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Human-in-the-loop (HITL) lets you pause graph execution, present information to a human, collect their input, and resume. This enables:
- Approval gates before critical actions
- Human review and editing of generated content
- Interactive data collection
- Supervised tool execution

**Requirements:**
- A configured checkpointer (state must persist across the pause)
- A `thread_id` in config (identifies which execution to resume)

## The interrupt() Function

`interrupt()` pauses execution and surfaces a payload to the caller:

```python
from langgraph.types import interrupt

def review_node(state: State):
    decision = interrupt({
        "question": "Do you approve this action?",
        "details": state["proposed_action"],
    })
    # `decision` is whatever the human provides via Command(resume=...)
    return {"approved": decision}
```

**Signature:** `interrupt(value: Any) -> Any`
- `value` — JSON-serializable payload shown to the caller (question, context, options)
- Returns the value passed via `Command(resume=...)` when execution resumes

**When interrupt is hit:**
1. Graph state is saved via checkpointer
2. Execution halts
3. The interrupt payload surfaces in the response
4. The graph waits indefinitely until resumed

## Resuming with Command

### v2 Pattern (LangGraph >= 1.1)

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "thread-1"}}

# First call — runs until interrupt
result = app.invoke({"input": "data"}, config, version="v2")
print(result.interrupts)  # [Interrupt(value={...}, id="...")]

# Resume with human input
result = app.invoke(Command(resume="approved"), config, version="v2")
print(result.value)  # Final result
```

### v1 Pattern (Default)

```python
result = app.invoke({"input": "data"}, config)
print(result["__interrupt__"])  # List of Interrupt objects

# Resume
result = app.invoke(Command(resume="approved"), config)
```

### Streaming Resume

```python
for chunk in app.stream(Command(resume="approved"), config):
    print(chunk)
```

**Critical:** Use the same `thread_id` when resuming. The `Command(resume=...)` value becomes the return value of `interrupt()` inside the node.

## Static Breakpoints

Pause before or after specific nodes without modifying node code:

### At Compile Time

```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["dangerous_node"],
    interrupt_after=["generate_node"],
)
```

### At Runtime

```python
result = app.invoke(
    inputs,
    config,
    interrupt_before=["dangerous_node"],
)

# Inspect state, then resume
state = app.get_state(config)
print(state.values)  # See what the graph produced so far
print(state.next)    # ["dangerous_node"] — what would run next

# Resume by invoking with None
app.invoke(None, config)
```

**Difference from `interrupt()`:**
- Static breakpoints don't exchange data — they just pause
- Resume with `None` (not `Command`)
- Good for debugging and state inspection

## Approval Workflows

The most common HITL pattern — pause before executing a critical action:

```python
def action_node(state: State) -> Command[Literal["execute", "cancel"]]:
    decision = interrupt({
        "action": state["proposed_action"],
        "risk_level": state["risk"],
        "question": "Approve this action?",
    })
    
    if decision == "approve":
        return Command(update={"status": "approved"}, goto="execute")
    elif decision == "modify":
        return Command(update={"status": "needs_modification"}, goto="modify")
    else:
        return Command(update={"status": "cancelled"}, goto="cancel")
```

### With Additional Context

```python
def approval_node(state: State):
    response = interrupt({
        "type": "approval",
        "title": "Database Migration",
        "description": f"About to run migration: {state['migration_name']}",
        "impact": f"Affects {state['affected_rows']} rows",
        "options": ["approve", "reject", "defer"],
    })
    return {"decision": response}
```

## Review and Edit Patterns

Let humans modify agent-generated content:

```python
def review_node(state: State):
    edited_content = interrupt({
        "instruction": "Review and edit this content",
        "content": state["generated_text"],
        "metadata": {"word_count": len(state["generated_text"].split())},
    })
    # edited_content is whatever the human submits
    return {"generated_text": edited_content}
```

### With Diff Tracking

```python
def review_with_diff(state: State):
    original = state["draft"]
    edited = interrupt({"content": original, "action": "edit"})
    
    return {
        "draft": edited,
        "was_edited": edited != original,
        "edit_history": state.get("edit_history", []) + [original],
    }
```

## Tool Call Approval

Gate specific tool calls behind human approval:

```python
from langchain_core.tools import tool

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?",
    })
    
    if response.get("action") == "approve":
        final_to = response.get("to", to)  # Allow edits
        actually_send_email(final_to, subject, body)
        return f"Email sent to {final_to}"
    return "Email cancelled by user"
```

## Input Validation Loops

Repeatedly prompt until valid input is received:

```python
def collect_age(state: State):
    prompt = "What is your age?"
    
    while True:
        answer = interrupt(prompt)
        if isinstance(answer, int) and 0 < answer < 150:
            return {"age": answer}
        prompt = f"'{answer}' is not a valid age. Please enter a number between 1 and 149."
```

### Multi-Step Data Collection

```python
def collect_user_info(state: State):
    name = interrupt({"field": "name", "prompt": "What is your name?"})
    email = interrupt({"field": "email", "prompt": "What is your email?"})
    role = interrupt({
        "field": "role",
        "prompt": "What is your role?",
        "options": ["admin", "user", "viewer"],
    })
    
    return {"user_info": {"name": name, "email": email, "role": role}}
```

Each `interrupt()` pauses independently. Resume each with `Command(resume=...)`.

## Multiple Simultaneous Interrupts

When parallel nodes interrupt, match responses by interrupt ID:

```python
# Graph has parallel nodes that both interrupt
result = app.invoke(inputs, config, version="v2")

# Multiple interrupts returned
for i in result.interrupts:
    print(f"ID: {i.id}, Payload: {i.value}")

# Resume with mapped responses
resume_map = {
    i.id: f"response for {i.value['question']}"
    for i in result.interrupts
}
result = app.invoke(Command(resume=resume_map), config, version="v2")
```

## Time-Travel Debugging

Use checkpoints to replay from any point:

```python
# Get execution history
history = list(app.get_state_history(config))

# Inspect a past state
past = history[3]
print(f"Step {past.metadata['step']}: {past.values}")

# Replay from that point with modified state
app.update_state(past.config, {"context": "corrected"})
result = app.invoke(None, past.config)
```

### Fork and Explore

```python
# Branch from a historical state
fork_config = past.config
app.update_state(fork_config, {"temperature": 0.9})
alternative_result = app.invoke(None, fork_config)
```

## Critical Rules

### Do NOT Wrap interrupt() in try/except

`interrupt()` uses exceptions internally. Catching them suppresses the pause:

```python
# WRONG — interrupt silently swallowed
try:
    result = interrupt("question")
except Exception:
    pass

# CORRECT — catch specific exceptions only
try:
    result = interrupt("question")
except ValueError:
    handle_value_error()
```

### Do NOT Reorder interrupt() Calls

Matching is index-based. Conditional skipping misaligns resume values:

```python
# WRONG — skipping first interrupt on resume misaligns
if condition:
    interrupt("q1")  # May not fire on resume
interrupt("q2")      # Gets q1's resume value

# CORRECT — always call both
r1 = interrupt("q1")
r2 = interrupt("q2")
if condition:
    use(r1)
```

### Side Effects Before interrupt() Must Be Idempotent

The entire node re-executes on resume:

```python
# WRONG — creates duplicate records
db.insert(record)  # Runs again on resume!
approved = interrupt("Approve?")

# CORRECT — move side effects after interrupt
approved = interrupt("Approve?")
if approved:
    db.insert(record)
```

### Do NOT Pass Non-Serializable Values

```python
# WRONG
interrupt({"callback": lambda x: x})

# CORRECT
interrupt({"type": "number", "min": 1, "max": 100})
```

## Common Pitfalls

1. **Missing checkpointer** — `interrupt()` without a checkpointer raises an error.
2. **Wrong thread_id on resume** — Must use the same `thread_id` as the original call.
3. **Catching interrupt exceptions** — Never use bare `except Exception` around interrupts.
4. **Non-idempotent side effects** — Code before `interrupt()` runs again on resume.
5. **Assuming node resumes from interrupt line** — The entire node restarts. Use `@task` for caching.
6. **Subgraph interrupts** — Both parent and subgraph nodes restart fully on resume.

---

> **Related:** [04-persistence-checkpointing.md](04-persistence-checkpointing.md) for checkpointing setup, [06-streaming.md](06-streaming.md) for streaming with interrupts
