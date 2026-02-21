# Structured Output — Type-Safe Agent Responses

## Table of Contents
1. [Overview](#overview)
2. [Basic Structured Output](#basic-structured-output)
3. [Complex Models](#complex-models)
4. [Nested Models](#nested-models)
5. [Lists and Collections](#lists-and-collections)
6. [Validation](#validation)
7. [Patterns](#patterns)

---

## Overview

Structured output forces the agent to return data as a Pydantic model instead of free-form text. The framework constrains the LLM to produce valid JSON matching the model's schema.

### When to Use

- API responses that need parsing
- Data extraction from text
- Form filling
- Structured analysis reports
- Any time you need programmatic access to agent output

---

## Basic Structured Output

```python
from pydantic import BaseModel, Field

class WeatherInfo(BaseModel):
    city: str = Field(description="City name")
    temperature: float = Field(description="Temperature in Celsius")
    conditions: str = Field(description="Weather conditions description")
    humidity: int = Field(description="Humidity percentage")

agent = client.as_agent(
    name="WeatherAgent",
    instructions="Provide weather information for requested locations.",
    response_format=WeatherInfo,
)

result: WeatherInfo = await agent.run("What's the weather in Tokyo?")
print(f"Temperature: {result.temperature}°C")
print(f"Conditions: {result.conditions}")
```

---

## Complex Models

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskAnalysis(BaseModel):
    title: str = Field(description="Brief task title")
    description: str = Field(description="Detailed task description")
    priority: Priority = Field(description="Task priority level")
    estimated_hours: float = Field(description="Estimated hours to complete")
    skills_required: list[str] = Field(description="Required skills")
    dependencies: list[str] = Field(default=[], description="Task dependencies")
    risks: Optional[str] = Field(default=None, description="Potential risks")

agent = client.as_agent(
    name="TaskAnalyzer",
    instructions="Analyze tasks and provide structured breakdowns.",
    response_format=TaskAnalysis,
)

task: TaskAnalysis = await agent.run("Build a user authentication system with OAuth2")
print(f"Priority: {task.priority}")
print(f"Hours: {task.estimated_hours}")
print(f"Skills: {', '.join(task.skills_required)}")
```

---

## Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"

class ContactInfo(BaseModel):
    email: str
    phone: Optional[str] = None
    address: Address

class CompanyProfile(BaseModel):
    name: str = Field(description="Company name")
    industry: str = Field(description="Primary industry")
    founded_year: int = Field(description="Year founded")
    employee_count: int = Field(description="Approximate employees")
    contact: ContactInfo
    key_products: list[str] = Field(description="Main products/services")
    competitors: list[str] = Field(description="Main competitors")

agent = client.as_agent(
    name="CompanyResearcher",
    instructions="Research companies and provide structured profiles.",
    response_format=CompanyProfile,
)

profile: CompanyProfile = await agent.run("Profile Microsoft Corporation")
print(f"Founded: {profile.founded_year}")
print(f"HQ: {profile.contact.address.city}, {profile.contact.address.state}")
```

---

## Lists and Collections

### Agent Returning a List

```python
class ExtractedEntity(BaseModel):
    text: str = Field(description="The entity text")
    entity_type: str = Field(description="Type: person, org, location, date")
    confidence: float = Field(description="Confidence score 0-1")

class EntityExtractionResult(BaseModel):
    entities: list[ExtractedEntity]
    summary: str = Field(description="Brief summary of extracted entities")

agent = client.as_agent(
    name="NERAgent",
    instructions="Extract named entities from text.",
    response_format=EntityExtractionResult,
)

result = await agent.run("Apple CEO Tim Cook announced new products in Cupertino on Monday.")
for entity in result.entities:
    print(f"{entity.text} ({entity.entity_type}): {entity.confidence:.2f}")
```

---

## Validation

### Pydantic Validators

```python
from pydantic import BaseModel, Field, field_validator

class BudgetProposal(BaseModel):
    project_name: str
    total_budget: float = Field(gt=0, description="Total budget in USD")
    duration_months: int = Field(ge=1, le=36, description="Project duration")
    line_items: list[dict] = Field(description="Budget line items")

    @field_validator("total_budget")
    @classmethod
    def budget_reasonable(cls, v):
        if v > 10_000_000:
            raise ValueError("Budget exceeds $10M limit")
        return v

    @field_validator("line_items")
    @classmethod
    def items_sum_to_total(cls, v, info):
        total = sum(item.get("amount", 0) for item in v)
        budget = info.data.get("total_budget", 0)
        if abs(total - budget) > 1:  # Allow $1 rounding
            raise ValueError(f"Line items ({total}) don't match budget ({budget})")
        return v
```

---

## Patterns

### Pattern: Structured Analysis with Recommendations

```python
class Recommendation(BaseModel):
    action: str = Field(description="Recommended action")
    rationale: str = Field(description="Why this is recommended")
    impact: str = Field(description="Expected impact")
    effort: str = Field(description="Implementation effort: low, medium, high")

class AnalysisReport(BaseModel):
    executive_summary: str
    key_findings: list[str]
    recommendations: list[Recommendation]
    risks: list[str]
    conclusion: str

agent = client.as_agent(
    name="Analyst",
    instructions="Provide thorough business analysis with actionable recommendations.",
    response_format=AnalysisReport,
)
```

### Pattern: Structured Decision

```python
class Decision(BaseModel):
    question: str = Field(description="The decision question")
    answer: bool = Field(description="Yes/No decision")
    confidence: float = Field(ge=0, le=1, description="Confidence 0-1")
    reasoning: str = Field(description="Reasoning behind the decision")
    caveats: list[str] = Field(default=[], description="Important caveats")

agent = client.as_agent(
    name="DecisionMaker",
    instructions="Make clear yes/no decisions with reasoning.",
    response_format=Decision,
)

decision = await agent.run("Should we migrate from PostgreSQL to MongoDB for our e-commerce app?")
print(f"Decision: {'Yes' if decision.answer else 'No'} (confidence: {decision.confidence})")
```

### Pattern: Multi-Step Extraction

```python
class MeetingNotes(BaseModel):
    title: str
    date: str
    attendees: list[str]
    agenda_items: list[str]
    action_items: list[dict]  # {assignee, task, deadline}
    decisions_made: list[str]
    next_meeting: Optional[str] = None

agent = client.as_agent(
    name="MeetingParser",
    instructions="Extract structured meeting notes from transcripts.",
    response_format=MeetingNotes,
)
```
