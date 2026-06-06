# Structured Data Extraction

> Source: [developers.llamaindex.ai — Extraction](https://developers.llamaindex.ai/python/framework/understanding/extraction/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Pydantic Models for Extraction](#pydantic-models-for-extraction)
- [LLM-Based Extraction](#llm-based-extraction)
- [Document-Level Extraction](#document-level-extraction)
- [Structured LLM Output](#structured-llm-output)
- [Query Engine Structured Output](#query-engine-structured-output)
- [Common Patterns](#common-patterns)

## Overview

LlamaIndex uses Pydantic models to extract structured data from unstructured text. The LLM interprets field names, types, and descriptions to produce validated, typed output — turning free-form text into machine-readable data.

Key use cases:
- Extracting entities from documents (names, dates, amounts)
- Converting reports into structured records
- Parsing invoices, receipts, and forms
- Building knowledge bases from unstructured text

## Pydantic Models for Extraction

Define the target schema using Pydantic `BaseModel`:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Invoice(BaseModel):
    """A representation of information from an invoice."""
    
    invoice_id: str = Field(description="The unique invoice identifier")
    vendor_name: str = Field(description="Name of the vendor or company")
    date: datetime = Field(description="Invoice date")
    total_amount: float = Field(description="Total amount due")
    currency: str = Field(default="USD", description="Currency code")
    line_items: list[str] = Field(description="List of items on the invoice")
    is_paid: bool = Field(default=False, description="Whether the invoice has been paid")
```

Guidelines for effective schemas:
- Use descriptive `Field(description=...)` — the LLM reads these
- Add docstrings to the class — used as extraction instructions
- Use precise types (`datetime`, not `str` for dates)
- Provide `default` values for optional fields
- Use `Optional[T]` for truly optional fields

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"

class Contact(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[Address] = None

class Company(BaseModel):
    """Information about a company extracted from text."""
    name: str = Field(description="Official company name")
    industry: str = Field(description="Primary industry sector")
    founded_year: Optional[int] = Field(description="Year the company was founded")
    headquarters: Address = Field(description="Company headquarters location")
    key_contacts: list[Contact] = Field(description="Key personnel")
    annual_revenue: Optional[float] = Field(description="Annual revenue in USD")
```

## LLM-Based Extraction

### Using Structured LLM

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4o")
structured_llm = llm.as_structured_llm(output_cls=Invoice)

response = structured_llm.complete(
    "Invoice #INV-2024-001 from Acme Corp dated March 15, 2024. "
    "Items: Widget A ($50), Widget B ($75). Total: $125.00. Status: unpaid."
)

invoice = response.raw  # Pydantic Invoice object
print(invoice.invoice_id)     # "INV-2024-001"
print(invoice.vendor_name)    # "Acme Corp"
print(invoice.total_amount)   # 125.0
print(invoice.line_items)     # ["Widget A ($50)", "Widget B ($75)"]
```

### Using Chat Interface

```python
from llama_index.core.llms import ChatMessage

structured_llm = llm.as_structured_llm(output_cls=Company)

messages = [
    ChatMessage(role="system", content="Extract company information."),
    ChatMessage(
        role="user",
        content="Apple Inc. was founded in 1976 in Cupertino, CA. "
                "They are in the technology sector with $394B annual revenue."
    ),
]

response = structured_llm.chat(messages)
company = response.raw
```

### Streaming Structured Output

```python
structured_llm = llm.as_structured_llm(output_cls=Invoice)

for chunk in structured_llm.stream_complete(text):
    if chunk.raw:
        partial = chunk.raw  # Partial Pydantic object during streaming
```

## Document-Level Extraction

Extract structured data from indexed documents:

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./contracts").load_data()
index = VectorStoreIndex.from_documents(documents)

class ContractInfo(BaseModel):
    """Key information extracted from a contract."""
    parties: list[str] = Field(description="Parties involved in the contract")
    effective_date: str = Field(description="Contract effective date")
    termination_date: Optional[str] = Field(description="Contract end date")
    contract_value: Optional[float] = Field(description="Total contract value")
    key_terms: list[str] = Field(description="Important terms and conditions")

query_engine = index.as_query_engine(output_cls=ContractInfo)
response = query_engine.query("Extract the key information from this contract.")
contract = response.response  # ContractInfo object
```

## Structured LLM Output

### In Query Engines

```python
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    sentiment: str
    confidence: float
    key_topics: list[str]

query_engine = index.as_query_engine(
    response_mode="compact",
    output_cls=AnalysisResult,
)

response = query_engine.query("Analyze the customer feedback.")
result = response.response  # AnalysisResult object
print(result.sentiment)
print(result.confidence)
```

### In Agents

```python
from llama_index.core.agent.workflow import FunctionAgent

class TaskResult(BaseModel):
    completed: bool
    findings: list[str]
    next_steps: list[str]

agent = FunctionAgent(
    tools=[search_tool],
    llm=llm,
    output_cls=TaskResult,
)

response = await agent.run(user_msg="Research the topic")
result = response  # TaskResult object
```

## Query Engine Structured Output

### With Custom Response Schema

```python
class QuestionAnswer(BaseModel):
    answer: str = Field(description="The answer to the question")
    sources: list[str] = Field(description="Source documents used")
    confidence: float = Field(
        description="Confidence score between 0 and 1"
    )
    reasoning: str = Field(description="Step-by-step reasoning")

query_engine = index.as_query_engine(output_cls=QuestionAnswer)
response = query_engine.query("What caused the revenue decline?")

qa = response.response
print(f"Answer: {qa.answer}")
print(f"Confidence: {qa.confidence}")
print(f"Reasoning: {qa.reasoning}")
```

### Batch Extraction

```python
from llama_index.core import Document

class ArticleMeta(BaseModel):
    title: str
    author: Optional[str] = None
    date: Optional[str] = None
    topics: list[str]
    summary: str

structured_llm = llm.as_structured_llm(output_cls=ArticleMeta)

articles = []
for doc in documents:
    response = structured_llm.complete(
        f"Extract metadata from this article:\n\n{doc.text[:2000]}"
    )
    articles.append(response.raw)
```

## Common Patterns

### Multi-Entity Extraction

```python
class Person(BaseModel):
    name: str
    role: Optional[str] = None
    organization: Optional[str] = None

class ExtractedEntities(BaseModel):
    """All entities found in the text."""
    people: list[Person] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)

structured_llm = llm.as_structured_llm(output_cls=ExtractedEntities)
response = structured_llm.complete(text)
entities = response.raw
```

### Classification + Extraction

```python
from enum import Enum

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    EMAIL = "email"

class ClassifiedDocument(BaseModel):
    doc_type: DocumentType
    confidence: float
    key_info: dict[str, str] = Field(
        description="Key information extracted based on document type"
    )
    summary: str

structured_llm = llm.as_structured_llm(output_cls=ClassifiedDocument)
```

### Extraction with Validation

```python
from pydantic import field_validator

class FinancialRecord(BaseModel):
    amount: float
    currency: str
    date: str
    category: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        valid = {"USD", "EUR", "GBP", "JPY"}
        if v.upper() not in valid:
            raise ValueError(f"Currency must be one of {valid}")
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount must be non-negative")
        return v
```

Pydantic validators run after LLM extraction, catching and rejecting invalid outputs automatically.
