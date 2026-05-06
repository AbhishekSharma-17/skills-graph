# CrewAI Tasks

> Source: https://docs.crewai.com/en/concepts/tasks

## Table of Contents

- [Overview](#overview) | [Task Definition](#task-definition) | [Core Parameters](#core-parameters)
- [Context Chaining](#task-with-context-chaining) | [Structured Output](#structured-output-with-pydantic) | [JSON Output](#json-output)
- [Async Tasks](#async-tasks) | [Guardrails](#task-guardrails) | [Human Input](#human-input-task)
- [Callbacks](#task-callbacks) | [YAML Config](#yaml-based-task-configuration) | [Common Pitfalls](#common-pitfalls)

## Overview

A Task in CrewAI is a specific assignment completed by an Agent. Tasks define what needs to be done, who does it, and what the expected output looks like. They are the driving force behind agent actions.

## Task Definition

```python
from crewai import Task, Agent

task = Task(
    description="Analyze the Q4 2025 sales data and identify the top 3 growth opportunities.",
    expected_output="A bullet-point list of 3 growth opportunities with supporting data.",
    agent=research_agent,
)
```

## Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | str | required | What the task is about (supports {variables}) |
| `expected_output` | str | required | Clear description of desired output format |
| `agent` | Agent | None | Agent assigned (required for sequential) |
| `tools` | list[Tool] | [] | Task-specific tools (override agent tools) |
| `context` | list[Task] | [] | Other tasks whose output feeds into this one |
| `output_json` | type | None | Pydantic model for JSON output |
| `output_pydantic` | type | None | Pydantic model for validated output |
| `output_file` | str | None | File path to save output |
| `callback` | callable | None | Called when task completes |
| `human_input` | bool | False | Require human approval before finishing |
| `async_execution` | bool | False | Execute asynchronously |
| `guardrail` | callable | None | Validation function for output |
| `max_retries` | int | None | Max retries on guardrail failure |
| `markdown` | bool | False | Format output as markdown |

## Task with Context (Chaining)

```python
research_task = Task(
    description="Research the latest AI agent frameworks.",
    expected_output="A comprehensive report on top 5 frameworks.",
    agent=researcher,
)

analysis_task = Task(
    description="Compare the frameworks and recommend the best one for our use case.",
    expected_output="A recommendation with pros/cons table.",
    agent=analyst,
    context=[research_task],  # Gets output from research_task
)

writing_task = Task(
    description="Write a technical blog post about the recommended framework.",
    expected_output="A 1000-word blog post in markdown.",
    agent=writer,
    context=[research_task, analysis_task],  # Gets both outputs
)
```

## Structured Output with Pydantic

```python
from pydantic import BaseModel, Field
from crewai import Task

class MarketReport(BaseModel):
    title: str = Field(description="Report title")
    summary: str = Field(description="Executive summary")
    opportunities: list[str] = Field(description="List of opportunities")
    risk_score: float = Field(ge=0, le=10, description="Overall risk score")

task = Task(
    description="Analyze the market for AI tools in 2026.",
    expected_output="Structured market analysis report.",
    agent=analyst,
    output_pydantic=MarketReport,
)

# After execution
result = crew.kickoff()
report = result.pydantic  # MarketReport instance
print(report.title)
print(report.risk_score)
```

## JSON Output

```python
class CompetitorAnalysis(BaseModel):
    company: str
    strengths: list[str]
    weaknesses: list[str]
    market_share: float

task = Task(
    description="Analyze our top competitor.",
    expected_output="JSON analysis of the competitor.",
    agent=analyst,
    output_json=CompetitorAnalysis,
)

# Access via result
result = crew.kickoff()
data = result.json_dict  # dict
```

## Task with File Output

```python
task = Task(
    description="Generate a CSV report of all findings.",
    expected_output="CSV file with columns: metric, value, trend",
    agent=data_agent,
    output_file="reports/analysis.csv",
)
```

## Async Tasks

```python
# Tasks execute in parallel when marked async
research_web = Task(
    description="Search the web for recent news about {topic}.",
    expected_output="Summary of recent news.",
    agent=web_researcher,
    async_execution=True,
)

research_papers = Task(
    description="Search academic papers about {topic}.",
    expected_output="Summary of academic findings.",
    agent=paper_researcher,
    async_execution=True,
)

# This task waits for both async tasks
synthesis = Task(
    description="Synthesize findings from web and academic research.",
    expected_output="Unified report combining both sources.",
    agent=analyst,
    context=[research_web, research_papers],  # Waits for both
)
```

## Task Guardrails

```python
from crewai import Task
from crewai.tasks.task_output import TaskOutput
from typing import Union

def validate_json_output(output: TaskOutput) -> Union[bool, str]:
    """Validate task output meets requirements."""
    try:
        import json
        data = json.loads(output.raw)
        if "recommendations" not in data:
            return "Output must contain 'recommendations' key"
        if len(data["recommendations"]) < 3:
            return "Must include at least 3 recommendations"
        return True
    except json.JSONDecodeError:
        return "Output must be valid JSON"

task = Task(
    description="Generate recommendations for improving the product.",
    expected_output="JSON with 'recommendations' array (minimum 3 items).",
    agent=analyst,
    guardrail=validate_json_output,
    max_retries=3,  # Retry up to 3 times on guardrail failure
)
```

## Human Input Task

```python
task = Task(
    description="Draft the quarterly investor letter.",
    expected_output="A professional investor letter in formal tone.",
    agent=writer,
    human_input=True,  # Pauses for human review before completing
)
```

## Task Callbacks

```python
def on_task_complete(output):
    print(f"Task completed! Output length: {len(output.raw)}")
    # Log to external system, send notification, etc.

task = Task(
    description="Analyze customer feedback data.",
    expected_output="Sentiment analysis summary.",
    agent=analyst,
    callback=on_task_complete,
)
```

## YAML-Based Task Configuration

```yaml
# config/tasks.yaml
research_task:
  description: >
    Research the latest developments in {topic}.
    Focus on practical applications and recent breakthroughs.
  expected_output: >
    A comprehensive research report with:
    - Key findings (minimum 5)
    - Supporting evidence
    - Relevance to our project
  agent: researcher
  tools:
    - SerperDevTool

writing_task:
  description: >
    Based on the research findings, write a blog post about {topic}.
    Target audience: senior developers.
  expected_output: >
    A 800-word blog post in markdown format with:
    - Engaging introduction
    - 3-4 main sections
    - Code examples where relevant
    - Conclusion with call to action
  agent: writer
  context:
    - research_task
  output_file: "output/blog_post.md"
```

## Task with Custom Tools

```python
from crewai_tools import FileReadTool

task = Task(
    description="Read the configuration file and validate all settings.",
    expected_output="Validation report with any issues found.",
    agent=validator,
    tools=[FileReadTool(file_path="config.yaml")],  # Task-specific tool
)
```

## Task Output Access

```python
result = crew.kickoff()

# Access overall result
print(result.raw)           # Raw string output
print(result.json_dict)     # If output_json was set
print(result.pydantic)      # If output_pydantic was set
print(result.token_usage)   # Token consumption stats

# Access individual task outputs
for task_output in result.tasks_output:
    print(f"Task: {task_output.description[:50]}")
    print(f"Output: {task_output.raw[:100]}")
```

## Common Patterns

### Conditional Task Execution

```python
def should_run_deep_analysis(context):
    return "high risk" in context[0].output.raw.lower()

deep_task = Task(
    description="Perform deep-dive risk analysis.",
    expected_output="Detailed risk assessment.",
    agent=risk_analyst,
    context=[initial_assessment],
    condition=should_run_deep_analysis,
)
```

### Template Variables

```python
task = Task(
    description="Research {company} and their {product} in the {market} market.",
    expected_output="Company profile and market position analysis.",
    agent=researcher,
)

# Variables are passed at kickoff
result = crew.kickoff(inputs={
    "company": "Anthropic",
    "product": "Claude",
    "market": "enterprise AI",
})
```

## Common Pitfalls

1. **Vague expected_output** — Be specific about format, length, and structure
2. **Missing context for dependent tasks** — Always chain tasks that need prior output
3. **Too many async tasks** — Can overwhelm rate limits; batch judiciously
4. **No guardrails on critical tasks** — Add validation for production workflows
5. **Ignoring token_usage** — Monitor costs especially with large context chains
