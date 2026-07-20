# Instructor — Classification Patterns

> Source: https://python.useinstructor.com/concepts/enums | v1.15.4

## Overview

Instructor supports multiple approaches for text classification: Python `Enum` classes, `Literal` types, and `Union` types. Each restricts LLM outputs to predefined categories with type safety.

## Enum-Based Classification

Use `Enum` for robust, reusable category sets:

```python
from enum import Enum
from pydantic import BaseModel, Field
import instructor

class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class SentimentAnalysis(BaseModel):
    text: str
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)

client = instructor.from_provider("openai/gpt-4o-mini")

result = client.create(
    response_model=SentimentAnalysis,
    messages=[{
        "role": "user",
        "content": "Classify: 'The product is great but shipping was terrible'",
    }],
)
print(result.sentiment)    # Sentiment.MIXED
print(result.confidence)   # 0.85
```

### Multi-Level Classification

```python
class Department(Enum):
    ENGINEERING = "engineering"
    SALES = "sales"
    SUPPORT = "support"
    HR = "hr"
    OTHER = "other"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketClassification(BaseModel):
    """Classify a support ticket into department and priority."""
    subject: str
    department: Department
    priority: Priority
    reasoning: str = Field(description="Brief explanation of classification")
```

## Literal-Based Classification

For simpler cases, `Literal` offers a lightweight alternative without defining a separate class:

```python
from typing import Literal

class ContentLabel(BaseModel):
    text: str
    category: Literal["news", "opinion", "tutorial", "review", "other"]
    language: Literal["en", "es", "fr", "de", "ja"]
```

### When to Use Literal vs Enum

| Feature | Enum | Literal |
|---------|------|---------|
| Reusability | Yes — define once, use anywhere | Inline only |
| Methods | Can add custom methods | No |
| Iteration | `list(Sentiment)` | No |
| Separate file | Natural | Awkward |
| Quick prototype | Verbose | Concise |

**Rule of thumb:** Use `Enum` for domain models shared across the codebase. Use `Literal` for one-off classifications.

## The "Other" Escape Hatch

Always include a fallback option for inputs that don't fit categories:

```python
class Role(Enum):
    ENGINEER = "engineer"
    DESIGNER = "designer"
    MANAGER = "manager"
    OTHER = "other"  # Lets the model signal uncertainty

class UserRole(BaseModel):
    name: str
    role: Role = Field(
        description="Assign the most appropriate role. Use OTHER if unsure."
    )
```

Without `OTHER`, the model is forced to pick an incorrect category for ambiguous inputs.

## Multi-Label Classification

Use `list[Enum]` or `list[Literal]` for multiple labels:

```python
class Tag(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    DEVOPS = "devops"
    AI_ML = "ai-ml"
    SECURITY = "security"
    DATABASE = "database"

class ArticleTags(BaseModel):
    title: str
    tags: list[Tag] = Field(
        min_length=1,
        max_length=5,
        description="Assign 1-5 relevant tags",
    )
    primary_tag: Tag = Field(description="Single most relevant tag")
```

## Union Types for Heterogeneous Classification

When different categories require different fields, use `Union`:

```python
from typing import Union

class BugReport(BaseModel):
    type: Literal["bug"] = "bug"
    severity: Literal["low", "medium", "high", "critical"]
    steps_to_reproduce: str
    expected_behavior: str

class FeatureRequest(BaseModel):
    type: Literal["feature"] = "feature"
    priority: Literal["nice-to-have", "important", "essential"]
    use_case: str
    proposed_solution: str | None = None

class Question(BaseModel):
    type: Literal["question"] = "question"
    topic: str
    context: str

class TicketRouter(BaseModel):
    """Route an incoming support message to the correct ticket type."""
    ticket: Union[BugReport, FeatureRequest, Question]
```

## Boolean Classification

For binary decisions:

```python
class SpamCheck(BaseModel):
    is_spam: bool = Field(description="True if the message is spam")
    reason: str = Field(description="Brief explanation")

class ModerationResult(BaseModel):
    is_appropriate: bool
    flagged_content: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
```

## Confidence Scores

Pair classifications with confidence for downstream filtering:

```python
class ClassificationResult(BaseModel):
    category: Literal["positive", "negative", "neutral"]
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident the classification is (0=guess, 1=certain)",
    )

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.8

# Usage
result = client.create(response_model=ClassificationResult, messages=[...])
if result.is_confident:
    process(result.category)
else:
    queue_for_review(result)
```

## Batch Classification

Classify multiple items in one call:

```python
from typing import Iterable

class EmailLabel(BaseModel):
    subject: str
    category: Literal["inbox", "spam", "newsletter", "transactional"]
    priority: Literal["low", "medium", "high"]

emails_text = """
1. "Your order has shipped" from amazon.com
2. "WIN A FREE iPHONE" from promo@deals.xyz
3. "Weekly Python Digest" from newsletter@python.org
"""

labels = client.create(
    response_model=Iterable[EmailLabel],
    messages=[{
        "role": "user",
        "content": f"Classify each email:\n{emails_text}",
    }],
)
for label in labels:
    print(f"{label.subject}: {label.category} ({label.priority})")
```
