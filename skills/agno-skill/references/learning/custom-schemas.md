# Custom Schemas for Learning Stores

Extend the default store schemas with domain-specific fields using Python dataclasses. The `metadata={"description": ...}` on each field tells the model what the field captures, so it can extract values correctly.

## Extending User Profile

```python
from dataclasses import dataclass, field
from typing import Optional
from agno.learn.schemas import UserProfile

@dataclass
class CustomerProfile(UserProfile):
    company: Optional[str] = field(
        default=None,
        metadata={"description": "Company or organization"}
    )
    plan_tier: Optional[str] = field(
        default=None,
        metadata={"description": "Subscription tier: free | pro | enterprise"}
    )
    role: Optional[str] = field(
        default=None,
        metadata={"description": "Job title or role"}
    )
    timezone: Optional[str] = field(
        default=None,
        metadata={"description": "User's timezone"}
    )
```

Use it:
```python
from agno.learn import LearningMachine, UserProfileConfig

agent = Agent(
    learning=LearningMachine(
        user_profile=UserProfileConfig(schema=CustomerProfile),
    ),
    db=db,
)
```

## Extending Entity Memory

```python
from dataclasses import dataclass, field
from typing import Optional
from agno.learn.schemas import EntityMemory

@dataclass
class CompanyEntity(EntityMemory):
    industry: Optional[str] = field(
        default=None,
        metadata={"description": "Industry: fintech | healthcare | saas"}
    )
    funding_stage: Optional[str] = field(
        default=None,
        metadata={"description": "Stage: seed | series_a | series_b | public"}
    )
    employee_count: Optional[int] = field(
        default=None,
        metadata={"description": "Number of employees"}
    )
```

## Extending Learned Knowledge

```python
from dataclasses import dataclass, field
from typing import Optional, List
from agno.learn.schemas import LearnedKnowledge

@dataclass
class TechnicalInsight(LearnedKnowledge):
    applicable_languages: Optional[List[str]] = field(
        default=None,
        metadata={"description": "Languages this applies to"}
    )
    performance_impact: Optional[str] = field(
        default=None,
        metadata={"description": "Performance impact: high | medium | low"}
    )
    complexity: Optional[str] = field(
        default=None,
        metadata={"description": "Complexity: simple | moderate | complex"}
    )
```

## Developer Profile Example

```python
@dataclass
class DeveloperProfile(UserProfile):
    primary_language: Optional[str] = field(
        default=None,
        metadata={"description": "Primary language: python | javascript | go | rust"}
    )
    framework: Optional[str] = field(
        default=None,
        metadata={"description": "Primary framework: react | django | fastapi"}
    )
    experience_years: Optional[int] = field(
        default=None,
        metadata={"description": "Years of programming experience"}
    )
    editor: Optional[str] = field(
        default=None,
        metadata={"description": "Editor: vscode | neovim | intellij"}
    )
```

## Schema Design Tips

- Use `Optional[str]` with `default=None` for all fields so they start empty and fill over time
- The `metadata={"description": ...}` is critical — the model reads it to know what to extract
- Use constrained values in the description (e.g. `"free | pro | enterprise"`) to guide extraction
- Keep field names short and descriptive
- Inherit from the correct base: `UserProfile`, `EntityMemory`, or `LearnedKnowledge`
