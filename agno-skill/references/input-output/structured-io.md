# Agno Structured Input / Output

## Contents
- [Input Formats](#input-formats)
- [Structured Input](#structured-input)
- [Structured Output](#structured-output)
- [Output Model (Refinement)](#output-model-refinement)
- [Parser Model (Structured Parsing)](#parser-model-structured-parsing)
- [Expected Output](#expected-output)

Agno agents accept multiple input formats (strings, dicts, Pydantic models, message lists) and can produce text or structured Pydantic objects.

---

## Input Formats

Agents accept any of these as the `input` parameter to `run()` / `arun()`:

| Format | Example |
|--------|---------|
| **String** | `"What is machine learning?"` |
| **Dict** | `{"topic": "AI", "depth": 5}` (validated if `input_schema` set) |
| **Pydantic model** | `ResearchRequest(topic="AI")` |
| **Message list** | `[{"role": "user", "content": "Hello"}]` |
| **Multimodal** | String + `images=`, `audio=`, `videos=`, `files=` kwargs |

### String input (basic)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(model=OpenAIResponses(id="gpt-4o"))
response = agent.run("What's the capital of France?")
print(response.content)  # "The capital of France is Paris."
```

### Message list input

```python
agent.run([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"},
])
```

---

## Structured Input

Validate and type-check input using Pydantic models. Two approaches:

### 1. Pass a Pydantic instance directly

```python
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    topic: str
    max_sources: int = Field(ge=1, le=20, default=5)
    focus_areas: list[str] = Field(default_factory=list)

agent = Agent(model=OpenAIResponses(id="gpt-4o"))

request = ResearchRequest(
    topic="AI Agents",
    max_sources=10,
    focus_areas=["multi-agent systems", "tool use"],
)
response = agent.run(input=request)
```

Validation happens when the model instance is created. Invalid data raises `ValidationError` before the agent runs.

### 2. Set `input_schema` on the agent

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    input_schema=ResearchRequest,
)

# Now dicts are auto-validated against the schema
response = agent.run(input={
    "topic": "AI Agents",
    "max_sources": 10,
    "focus_areas": ["multi-agent systems", "tool use"],
})
```

This is useful when input comes from external sources (APIs, files, user forms) — the agent validates the dict for you.

### Validation error handling

```python
from pydantic import ValidationError

class OrderRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    input_schema=OrderRequest,
)

try:
    agent.run(input={"product_id": "SKU-123", "quantity": -5})
except ValidationError as e:
    print(e)  # quantity: Input should be greater than 0
```

### Nested models

```python
class Author(BaseModel):
    name: str
    email: str

class ArticleRequest(BaseModel):
    title: str
    author: Author
    tags: list[str]

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    input_schema=ArticleRequest,
)

response = agent.run(input={
    "title": "Getting Started with Agno",
    "author": {"name": "Jane Doe", "email": "jane@example.com"},
    "tags": ["tutorial", "agents"],
})
```

---

## Structured Output

Use Pydantic models to get validated, typed responses instead of raw text.

### Basic structured output

```python
from pydantic import BaseModel, Field
from typing import List

class MovieScript(BaseModel):
    setting: str = Field(description="Where the movie takes place")
    genre: str = Field(description="Movie genre")
    storyline: str = Field(description="Brief plot summary")

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    output_schema=MovieScript,
)

response = agent.run("Write a movie script about a heist in Tokyo")

# response.content is a MovieScript instance, not a string
print(response.content.setting)    # "Tokyo, Japan"
print(response.content.genre)      # "Action/Thriller"
print(response.content.storyline)  # "A retired thief is pulled back..."
```

**How it works:**
1. Pydantic model → JSON schema
2. Schema passed to model's structured output API (if supported natively)
3. Response validated against schema
4. Typed Pydantic object returned in `response.content`

### With tools

```python
from agno.tools.yfinance import YFinanceTools

class StockAnalysis(BaseModel):
    symbol: str
    current_price: float
    change_percent: float
    recommendation: str = Field(description="buy, hold, or sell")
    reasoning: str

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True)],
    output_schema=StockAnalysis,
)

response = agent.run("Analyze NVDA stock")
analysis: StockAnalysis = response.content
print(f"{analysis.symbol}: ${analysis.current_price} → {analysis.recommendation}")
```

### Per-run schema override

Override the default schema for a specific call:

```python
agent = Agent(model=OpenAIResponses(id="gpt-4o"))

# Different schemas for different calls — no need to set one on the agent
sentiment = agent.run("Analyze: 'Great product!'", output_schema=SentimentResult)
entities = agent.run("Extract entities from this text...", output_schema=EntityList)
```

### Classification pattern

```python
from typing import Literal

class Classification(BaseModel):
    category: Literal["spam", "not_spam"]
    confidence: float = Field(ge=0, le=1)
    reasoning: str

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    output_schema=Classification,
)
```

### Data extraction pattern

```python
class ExtractedData(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    output_schema=ExtractedData,
)

response = agent.run(f"Extract contact info from: {document_text}")
```

### Multi-item generation pattern

```python
class BlogPost(BaseModel):
    title: str
    summary: str
    sections: list[str]

class BlogPostList(BaseModel):
    posts: list[BlogPost]

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    output_schema=BlogPostList,
)

response = agent.run("Generate 3 blog post ideas about AI trends")
for post in response.content.posts:
    print(f"- {post.title}")
```

### JSON mode fallback

For models without native structured output support:

```python
agent = Agent(
    model=SomeModel(),
    output_schema=MySchema,
    use_json_mode=True,  # Instructs model to respond in JSON
)
```

JSON mode doesn't guarantee schema compliance — prefer native structured output when available.

### Schema design tips

Use `Field(description=...)` to guide the model:

```python
class Review(BaseModel):
    sentiment: str = Field(description="Must be 'positive', 'negative', or 'neutral'")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0.0 to 1.0")
    score: int = Field(ge=1, le=5, description="Rating from 1 to 5")
```

Use `Optional` for fields the model may not always have data for:

```python
class CompanyInfo(BaseModel):
    name: str
    ticker: str
    market_cap: float | None = Field(None, description="Market cap if publicly traded")
    founded_year: int | None = None
```

---

## Output Model (Refinement)

Use a separate (often more capable) model to refine the main model's response. Useful for cost optimization — cheap model for reasoning/tool use, expensive model for polished output.

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-4o-mini"),       # Cheap: does the work
    output_model=OpenAIResponses(id="gpt-4o"),      # Expensive: polishes the result
    output_model_prompt="Rewrite as a professional, well-formatted response.",
)

response = agent.run("Give me a recipe for pad thai")
```

---

## Parser Model (Structured Parsing)

Use a separate model to parse the main model's text response into a structured schema. Useful when the main model produces good content but struggles with strict JSON formatting.

```python
from typing import List
from pydantic import BaseModel, Field

class ParkAdventure(BaseModel):
    park_name: str
    best_season: str
    signature_attractions: List[str]
    recommended_trails: List[str]
    wildlife_encounters: List[str]
    difficulty_rating: int = Field(ge=1, le=5)
    estimated_days: int = Field(ge=1, le=14)

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    output_schema=ParkAdventure,
    parser_model=OpenAIResponses(id="gpt-4o"),  # Parses main response into schema
)

response = agent.run("Tell me about Yellowstone National Park")
adventure: ParkAdventure = response.content
```

---

## Expected Output

Guide the agent's response format with a natural language description:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    expected_output="A numbered list of exactly 5 items, each with a title and one-sentence description.",
    markdown=True,
)

agent.print_response("What are the most important principles of clean code?", stream=True)
```

---

