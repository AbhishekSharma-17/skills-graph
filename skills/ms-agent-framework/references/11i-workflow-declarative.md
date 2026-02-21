# Declarative Workflows — YAML Definition, Config-Driven, No-Code

## Overview

Declarative workflows define execution graphs and agent configurations using YAML or JSON instead of Python code. This enables non-developers to create workflows, supports configuration-driven deployments, and makes it easy to modify workflows without code changes.

## YAML Workflow Definition

### Basic Structure

```yaml
# workflow.yaml
name: content_pipeline
description: Process, analyze, and format text content
entry: clean
exit: format

nodes:
  clean:
    executor: text_cleaner
    connects_to: [analyze]

  analyze:
    executor: text_analyzer
    connects_to: [format]

  format:
    executor: output_formatter
```

### Nodes Configuration

Each node specifies:
- **executor**: The executor instance key from registry
- **connects_to**: List of node names to connect to (outgoing edges)
- **type** (optional): "parallel" for concurrent execution

```yaml
nodes:
  input:
    executor: input_processor
    connects_to: [branch_a, branch_b]  # Fan-out

  branch_a:
    executor: processor_a
    connects_to: [merge]

  branch_b:
    executor: processor_b
    connects_to: [merge]

  merge:
    executor: merge_handler
    connects_to: [output]

  output:
    executor: output_formatter
```

### Conditional Routing

Use routing rules to define conditional edges:

```yaml
nodes:
  classifier:
    executor: request_classifier
    routes:
      - condition: "priority == 'high'"
        target: urgent_handler
      - condition: "priority == 'normal'"
        target: normal_handler
      - default: low_priority_handler

  urgent_handler:
    executor: urgent_processor
    connects_to: [format]

  normal_handler:
    executor: normal_processor
    connects_to: [format]

  low_priority_handler:
    executor: low_processor
    connects_to: [format]

  format:
    executor: output_formatter
```

## Loading Workflows with Executor Registry

### Registry Pattern

```python
from agent_framework.workflows import Workflow
import yaml

# Define executors
class TextCleaner(Executor):
    def __init__(self):
        super().__init__(id="cleaner")

    @handler
    async def clean(self, text: str, ctx: WorkflowContext[str]) -> None:
        await ctx.send_message(text.strip().lower())

class TextAnalyzer(Executor):
    def __init__(self):
        super().__init__(id="analyzer")

    @handler
    async def analyze(self, text: str, ctx: WorkflowContext[str]) -> None:
        # Analysis logic
        result = {"text": text, "length": len(text)}
        await ctx.send_message(result)

# Create registry (maps YAML executor names to instances)
executor_registry = {
    "text_cleaner": TextCleaner(),
    "text_analyzer": TextAnalyzer(),
    "output_formatter": OutputFormatter(),
}

def load_workflow_from_yaml(yaml_path: str, registry: dict) -> Workflow:
    """Load workflow from YAML and wire up executors."""
    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    wf = Workflow()

    # Add all nodes
    for node_name, node_config in config.get("nodes", {}).items():
        executor = registry[node_config["executor"]]
        wf.add_node(node_name, executor)

    # Connect nodes
    for node_name, node_config in config.get("nodes", {}).items():
        for target in node_config.get("connects_to", []):
            wf.connect(node_name, target)

    # Set entry and exit
    wf.set_entry_node(config["entry"])
    wf.set_exit_node(config["exit"])

    return wf

# Usage
workflow = load_workflow_from_yaml("workflow.yaml", executor_registry)
result = await workflow.run("Hello world")
```

## Declarative Agent Definition

Agents can also be declaratively defined in YAML alongside workflows.

### Agent YAML Format

```yaml
# agent.yaml
name: CustomerSupport
description: "Handles customer inquiries"
instructions: |
  You are a helpful customer support agent.
  Be empathetic and professional.
  Always try to resolve issues on first contact.
  If unable, escalate to human agent.

tools:
  - name: lookup_account
    description: Look up customer account information
    parameters:
      customer_id:
        type: string
        description: The customer ID

  - name: create_ticket
    description: Create a support ticket
    parameters:
      issue_description:
        type: string
        description: Description of the issue
      priority:
        type: string
        enum: [low, medium, high]
        description: Ticket priority

options:
  temperature: 0.7
  max_tokens: 1000
  top_p: 0.9
```

### Loading Declarative Agents

```python
from agent_framework import Agent

# Define tools
@tool
def lookup_account(customer_id: str) -> dict:
    """Look up customer account."""
    return {"customer_id": customer_id, "name": "John Doe", "status": "active"}

@tool
def create_ticket(issue_description: str, priority: str) -> str:
    """Create support ticket."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    return f"Ticket created: {ticket_id}"

# Load agent from YAML
agent = Agent.from_yaml(
    "agent.yaml",
    client=client,
    tools=[lookup_account, create_ticket]
)

# Use like any other agent
result = await agent.run("I have an account issue")
```

## Combining Declarative and Code-Based Tools

Mix declarative workflow definition with programmatic tool binding:

```python
# workflow.yaml
nodes:
  input:
    executor: input_processor
    connects_to: [agent_node]

  agent_node:
    executor: support_agent
    connects_to: [response_formatter]

  response_formatter:
    executor: formatter

---

# Python code
from agent_framework import Agent
from agent_framework.workflows import Workflow, WorkflowExecutor

# Load workflow structure from YAML
yaml_config = yaml.safe_load(open("workflow.yaml"))

# Create executors with specific tools
agent = Agent.from_yaml("agent.yaml", client=client, tools=[...])
agent_executor = agent.as_executor()

registry = {
    "input_processor": InputProcessor(),
    "support_agent": agent_executor,
    "formatter": OutputFormatter(),
}

# Combine declarative structure with programmatic setup
workflow = load_workflow_from_yaml("workflow.yaml", registry)
```

## YAML Workflow with Agents

Embed agent executors in a workflow configuration:

```yaml
# workflow_with_agents.yaml
name: research_workflow
entry: query_input
exit: report_formatter

nodes:
  query_input:
    executor: query_parser
    connects_to: [research_agent]

  research_agent:
    # This executor is an agent (created in Python)
    executor: researcher_agent
    connects_to: [critic_agent]

  critic_agent:
    executor: critic
    connects_to: [report_formatter]

  report_formatter:
    executor: report_writer
```

Python setup:

```python
# Create agents
researcher = Agent.from_yaml("researcher-agent.yaml", client=client, tools=[search, summarize])
critic = Agent.from_yaml("critic-agent.yaml", client=client, tools=[evaluate])

# Wrap as executors
researcher_executor = researcher.as_executor()
critic_executor = critic.as_executor()

# Register and load workflow
registry = {
    "query_parser": QueryParser(),
    "researcher_agent": researcher_executor,
    "critic": critic_executor,
    "report_writer": ReportWriter(),
}

workflow = load_workflow_from_yaml("workflow_with_agents.yaml", registry)
```

## Declarative Workflow Samples

Reference YAML structures for common patterns:

### Simple Sequential Pipeline

```yaml
# simple_workflow.yaml
name: text_pipeline
entry: step1
exit: step3

nodes:
  step1:
    executor: step1_executor
    connects_to: [step2]
  step2:
    executor: step2_executor
    connects_to: [step3]
  step3:
    executor: step3_executor
```

### Conditional Routing

```yaml
# conditional_workflow.yaml
name: request_router
entry: classify
exit: response_formatter

nodes:
  classify:
    executor: classifier
    routes:
      - condition: "type == 'bug'"
        target: bug_handler
      - condition: "type == 'feature'"
        target: feature_handler
      - default: general_handler

  bug_handler:
    executor: bug_processor
    connects_to: [response_formatter]

  feature_handler:
    executor: feature_processor
    connects_to: [response_formatter]

  general_handler:
    executor: general_processor
    connects_to: [response_formatter]

  response_formatter:
    executor: formatter
```

### Parallel Processing (Fan-Out/Fan-In)

```yaml
# parallel_workflow.yaml
name: content_analysis
entry: input
exit: merger

nodes:
  input:
    executor: input_processor
    connects_to: [sentiment_analyzer, entity_extractor, summarizer]

  sentiment_analyzer:
    executor: sentiment_exec
    connects_to: [merger]

  entity_extractor:
    executor: entity_exec
    connects_to: [merger]

  summarizer:
    executor: summarize_exec
    connects_to: [merger]

  merger:
    executor: results_merger
```

### Human-in-Loop Approval

```yaml
# human_in_loop.yaml
name: approval_workflow
entry: request_processor
exit: finalizer

nodes:
  request_processor:
    executor: request_handler
    connects_to: [approval_gate]

  approval_gate:
    executor: approval_requester
    connects_to: [decision_handler]

  decision_handler:
    executor: decision_processor
    routes:
      - condition: "approved == true"
        target: executor_action
      - default: rejection_handler

  executor_action:
    executor: action_executor
    connects_to: [finalizer]

  rejection_handler:
    executor: rejection_handler
    connects_to: [finalizer]

  finalizer:
    executor: final_formatter
```

### Multi-Agent Collaboration

```yaml
# multi_agent_workflow.yaml
name: customer_support
entry: intake
exit: response

nodes:
  intake:
    executor: ticket_parser
    connects_to: [classifier]

  classifier:
    executor: issue_classifier
    routes:
      - condition: "category == 'technical'"
        target: tech_agent
      - condition: "category == 'billing'"
        target: billing_agent
      - default: general_agent

  tech_agent:
    executor: technical_support
    connects_to: [quality_check]

  billing_agent:
    executor: billing_support
    connects_to: [quality_check]

  general_agent:
    executor: general_support
    connects_to: [quality_check]

  quality_check:
    executor: response_quality_checker
    connects_to: [response]

  response:
    executor: response_formatter
```

### Deep Research Workflow

```yaml
# deep_research.yaml
name: research_pipeline
entry: query
exit: report

nodes:
  query:
    executor: query_normalizer
    connects_to: [researcher]

  researcher:
    executor: research_agent
    connects_to: [fact_checker]

  fact_checker:
    executor: fact_check_agent
    connects_to: [synthesizer]

  synthesizer:
    executor: synthesis_agent
    connects_to: [quality_reviewer]

  quality_reviewer:
    executor: quality_agent
    routes:
      - condition: "quality_score >= 0.8"
        target: report
      - default: researcher  # Loop back for revision

  report:
    executor: report_writer
```

### Marketing Campaign Builder

```yaml
# marketing_campaign.yaml
name: campaign_generator
entry: brief
exit: campaign_output

nodes:
  brief:
    executor: brief_parser
    connects_to: [content_gen, audience_gen]

  content_gen:
    executor: content_creator
    connects_to: [merger]

  audience_gen:
    executor: audience_analyzer
    connects_to: [merger]

  merger:
    executor: campaign_assembler
    connects_to: [critic]

  critic:
    executor: campaign_critic
    routes:
      - condition: "approved == true"
        target: campaign_output
      - default: content_gen  # Revise

  campaign_output:
    executor: campaign_formatter
```

### Function Tool Executor Pattern

Use Python functions as declarative executor definitions:

```python
# Register function-based executors
from agent_framework.workflows import executor, WorkflowContext
from typing import Never

@executor(id="email_validator")
async def validate_email(email: str, ctx: WorkflowContext[str]) -> None:
    if "@" in email and "." in email:
        await ctx.send_message({"email": email, "valid": True})
    else:
        await ctx.send_message({"email": email, "valid": False})

@executor(id="email_saver")
async def save_email(data: dict, ctx: WorkflowContext[Never, str]) -> None:
    # Save and yield final output
    await ctx.yield_output(f"Saved: {data['email']}")

registry = {
    "validator": validate_email,
    "saver": save_email,
}
```

## When to Use Declarative vs Code-Based

| Use Case | Declarative | Code-Based |
|---|:-:|:-:|
| Non-developers editing workflows | ✅ | |
| Configuration-driven deployments | ✅ | |
| Simple sequential pipelines | ✅ | |
| Quick prototyping | ✅ | |
| Complex conditional logic | | ✅ |
| Stateful executors | | ✅ |
| Custom error handling | | ✅ |
| Dynamic workflow construction | | ✅ |
| Mixing tools and agents | ✅ | ✅ |
| Sub-workflows and nesting | | ✅ |

## Best Practices

1. **Keep YAML simple** — Use code for complex logic
2. **Version control workflows** — Treat YAML files like code
3. **Use registry pattern** — Centralized executor management
4. **Document executors** — Docstrings and descriptions
5. **Validate YAML** — Use JSON Schema for configuration validation
6. **Test in isolation** — Test executors separately from workflow
7. **Use environment variables** — For environment-specific config (paths, URLs)

Example with env vars:

```python
import os
from pathlib import Path

def load_workflow_from_env() -> Workflow:
    """Load workflow path from environment."""
    workflow_path = os.getenv("WORKFLOW_PATH", "./workflows/default.yaml")
    return load_workflow_from_yaml(workflow_path, executor_registry)
```

## Workflow Validation

Validate YAML before loading:

```python
import jsonschema

WORKFLOW_SCHEMA = {
    "type": "object",
    "required": ["name", "entry", "exit", "nodes"],
    "properties": {
        "name": {"type": "string"},
        "entry": {"type": "string"},
        "exit": {"type": "string"},
        "nodes": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["executor"],
                "properties": {
                    "executor": {"type": "string"},
                    "connects_to": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}

def validate_workflow_config(config: dict) -> bool:
    """Validate workflow YAML against schema."""
    try:
        jsonschema.validate(config, WORKFLOW_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        print(f"Invalid workflow: {e.message}")
        return False
```
