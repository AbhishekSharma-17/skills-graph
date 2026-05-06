# CrewAI Structured Output

> Source: https://docs.crewai.com/en/concepts/tasks

## Overview

CrewAI supports structured outputs via Pydantic models (`output_pydantic`) and JSON schemas (`output_json`). This ensures agent outputs conform to expected formats with validation, making outputs reliable for downstream processing.

## Output Types

| Method | Class | Access | Validation |
|--------|-------|--------|-----------|
| `output_pydantic` | Pydantic BaseModel | `result.pydantic` | Full Pydantic validation |
| `output_json` | Pydantic BaseModel | `result.json_dict` | JSON structure validation |
| Raw (default) | None | `result.raw` | No validation |

## Pydantic Output

```python
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process

class CompetitorReport(BaseModel):
    company_name: str = Field(description="Name of the competitor")
    market_position: str = Field(description="Current market position")
    strengths: list[str] = Field(description="Key strengths")
    weaknesses: list[str] = Field(description="Key weaknesses")
    threat_level: float = Field(ge=1.0, le=10.0, description="Threat level 1-10")
    recommended_actions: list[str] = Field(description="Recommended strategic actions")

analyst = Agent(
    role="Competitive Intelligence Analyst",
    goal="Analyze competitors and produce structured reports",
    backstory="Expert in market analysis with Fortune 500 experience.",
)

task = Task(
    description="Analyze {competitor} as a competitive threat in the AI market.",
    expected_output="Structured competitor analysis report.",
    agent=analyst,
    output_pydantic=CompetitorReport,
)

crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential)
result = crew.kickoff(inputs={"competitor": "OpenAI"})

# Access structured output
report = result.pydantic
print(f"Company: {report.company_name}")
print(f"Threat Level: {report.threat_level}")
print(f"Strengths: {report.strengths}")
```

## JSON Output

```python
from pydantic import BaseModel, Field
from crewai import Task

class APIEndpoint(BaseModel):
    method: str = Field(description="HTTP method (GET, POST, etc.)")
    path: str = Field(description="URL path")
    description: str = Field(description="What this endpoint does")
    parameters: list[str] = Field(default=[], description="Query/body parameters")
    response_code: int = Field(default=200, description="Expected response code")

task = Task(
    description="Design the API endpoints for user management.",
    expected_output="JSON specification of all endpoints.",
    agent=api_designer,
    output_json=APIEndpoint,
)

result = crew.kickoff()
data = result.json_dict  # dict
print(data["method"])
print(data["path"])
```

## Nested Pydantic Models

```python
from pydantic import BaseModel, Field

class TechStack(BaseModel):
    frontend: list[str] = Field(description="Frontend technologies")
    backend: list[str] = Field(description="Backend technologies")
    database: list[str] = Field(description="Database technologies")
    infrastructure: list[str] = Field(description="Infrastructure/cloud")

class TeamMember(BaseModel):
    name: str = Field(description="Team member name")
    role: str = Field(description="Role in the project")
    responsibilities: list[str] = Field(description="Key responsibilities")

class ProjectPlan(BaseModel):
    project_name: str = Field(description="Name of the project")
    description: str = Field(description="Brief project description")
    tech_stack: TechStack = Field(description="Technology stack")
    team: list[TeamMember] = Field(description="Team composition")
    milestones: list[str] = Field(description="Key milestones")
    estimated_weeks: int = Field(ge=1, description="Estimated duration in weeks")
    risks: list[str] = Field(description="Identified risks")

task = Task(
    description="Create a project plan for building an AI-powered chatbot.",
    expected_output="Comprehensive project plan.",
    agent=project_manager,
    output_pydantic=ProjectPlan,
)
```

## Output File

Save task output directly to a file:

```python
task = Task(
    description="Generate a comprehensive market report.",
    expected_output="Detailed market analysis in markdown.",
    agent=analyst,
    output_file="reports/market_analysis.md",
)
```

Combined with structured output:

```python
task = Task(
    description="Analyze the data and produce a report.",
    expected_output="JSON report.",
    agent=analyst,
    output_json=ReportModel,
    output_file="reports/analysis.json",  # Saves JSON to file too
)
```

## Accessing Task Outputs

```python
result = crew.kickoff()

# Last task's output
print(result.raw)           # Always available
print(result.pydantic)      # If output_pydantic was set on last task
print(result.json_dict)     # If output_json was set on last task

# Dictionary-style access (if structured)
print(result["field_name"])

# All task outputs
for task_output in result.tasks_output:
    print(f"Agent: {task_output.agent}")
    print(f"Raw: {task_output.raw[:100]}")
    print(f"Pydantic: {task_output.pydantic}")

# Token usage
print(result.token_usage)
```

## Validation and Retries

CrewAI validates structured outputs automatically:

1. Agent produces output
2. CrewAI attempts to parse into the specified model
3. If parsing fails, agent is re-prompted with format instructions
4. Retries up to the configured limit

```python
task = Task(
    description="Produce a structured analysis.",
    expected_output="Must conform to the specified schema.",
    agent=analyst,
    output_pydantic=AnalysisModel,
    max_retries=3,  # Retry parsing up to 3 times
)
```

## Combining with Guardrails

```python
from crewai import Task
from crewai.tasks.task_output import TaskOutput
from typing import Union

class SentimentResult(BaseModel):
    text: str
    sentiment: str = Field(pattern="^(positive|negative|neutral)$")
    confidence: float = Field(ge=0.0, le=1.0)

def validate_sentiment(output: TaskOutput) -> Union[bool, str]:
    if output.pydantic:
        if output.pydantic.confidence < 0.5:
            return "Confidence too low. Re-analyze with more context."
    return True

task = Task(
    description="Analyze the sentiment of this customer review: {review}",
    expected_output="Structured sentiment analysis.",
    agent=analyst,
    output_pydantic=SentimentResult,
    guardrail=validate_sentiment,
    max_retries=2,
)
```

## Lists and Enums in Output

```python
from enum import Enum
from pydantic import BaseModel, Field

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ActionItem(BaseModel):
    title: str = Field(description="Action item title")
    assignee: str = Field(description="Person responsible")
    priority: Priority = Field(description="Priority level")
    due_date: str = Field(description="Due date (YYYY-MM-DD)")

class MeetingNotes(BaseModel):
    date: str = Field(description="Meeting date")
    attendees: list[str] = Field(description="List of attendees")
    summary: str = Field(description="Brief meeting summary")
    action_items: list[ActionItem] = Field(description="Action items from meeting")
    next_meeting: str | None = Field(default=None, description="Next meeting date")
```

## Best Practices

### Field Descriptions Are Critical

```python
# BAD: No descriptions — agent doesn't know what to put where
class Report(BaseModel):
    a: str
    b: list[str]
    c: float

# GOOD: Clear descriptions guide the agent
class Report(BaseModel):
    title: str = Field(description="Concise report title (max 10 words)")
    findings: list[str] = Field(description="Key findings (3-5 bullet points)")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0.0-1.0")
```

### Keep Models Focused

```python
# BAD: Too many fields — agent struggles
class EverythingReport(BaseModel):
    # 20+ fields...

# GOOD: Focused model for the specific task
class ExecutiveSummary(BaseModel):
    headline: str = Field(description="One-line headline")
    key_metrics: list[str] = Field(max_length=5)
    recommendation: str = Field(description="Single recommendation")
```

## Common Pitfalls

1. **Missing Field descriptions** — Without them, agents guess at content
2. **Overly complex models** — Keep to <10 fields per model; nest for complexity
3. **Strict validation on creative tasks** — Allow flexibility in creative outputs
4. **Not checking result.pydantic is None** — Parsing can fail; always handle None
5. **Forgetting output_pydantic vs output_json** — pydantic gives model instance, json gives dict
6. **No expected_output alignment** — expected_output should describe the model's structure
