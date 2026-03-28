# Claude Agent SDK — Structured Outputs

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What Are Structured Outputs](#what-are-structured-outputs)
- [Configuration](#configuration)
- [JSON Schema Format](#json-schema-format)
- [Python: Pydantic Models](#python-pydantic-models)
- [TypeScript: Zod Schemas](#typescript-zod-schemas)
- [Accessing Results](#accessing-results)
- [Validation and Retries](#validation-and-retries)
- [Practical Examples](#practical-examples)
- [Common Pitfalls](#common-pitfalls)

## What Are Structured Outputs

Structured outputs instruct the agent to return its final result as typed JSON conforming to a schema. Instead of parsing free-text responses, you get validated, predictable data structures.

Use structured outputs when:
- Building pipelines that consume agent results programmatically
- Extracting structured data from codebases (lists of functions, dependency graphs)
- Generating reports with consistent formats
- Integrating agent results into APIs or databases

## Configuration

Set `output_format` in options:

### Python

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string"},
                            "line": {"type": "integer"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "description": {"type": "string"},
                        },
                        "required": ["file", "line", "severity", "description"],
                    },
                },
                "total_issues": {"type": "integer"},
            },
            "required": ["summary", "issues", "total_issues"],
        },
    },
)
```

### TypeScript

```typescript
const q = query({
  prompt: "Review auth.py for security issues",
  options: {
    outputFormat: {
      type: "json_schema",
      schema: {
        type: "object",
        properties: {
          summary: { type: "string" },
          issues: {
            type: "array",
            items: {
              type: "object",
              properties: {
                file: { type: "string" },
                line: { type: "integer" },
                severity: { type: "string", enum: ["low", "medium", "high"] },
                description: { type: "string" },
              },
              required: ["file", "line", "severity", "description"],
            },
          },
          total_issues: { type: "integer" },
        },
        required: ["summary", "issues", "total_issues"],
      },
    },
  },
});
```

## JSON Schema Format

The `output_format` object structure:

```json
{
  "type": "json_schema",
  "schema": {
    "type": "object",
    "properties": { ... },
    "required": [ ... ]
  }
}
```

### Supported Schema Types

| Type | JSON Schema | Example |
|------|------------|---------|
| String | `{"type": "string"}` | `"hello"` |
| Integer | `{"type": "integer"}` | `42` |
| Number | `{"type": "number"}` | `3.14` |
| Boolean | `{"type": "boolean"}` | `true` |
| Array | `{"type": "array", "items": {...}}` | `[1, 2, 3]` |
| Object | `{"type": "object", "properties": {...}}` | `{"key": "value"}` |
| Enum | `{"type": "string", "enum": [...]}` | `"high"` |
| Nullable | `{"type": ["string", "null"]}` | `null` |

## Python: Pydantic Models

Convert Pydantic models to JSON Schema for `output_format`:

```python
from pydantic import BaseModel

class SecurityIssue(BaseModel):
    file: str
    line: int
    severity: str  # "low", "medium", "high"
    description: str

class SecurityReport(BaseModel):
    summary: str
    issues: list[SecurityIssue]
    total_issues: int

# Convert Pydantic model to JSON Schema
options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": SecurityReport.model_json_schema(),
    },
)

# Parse the result
async for msg in query(prompt="Review for security issues", options=options):
    if msg.type == "result" and msg.structured_output:
        report = SecurityReport.model_validate(msg.structured_output)
        print(f"Found {report.total_issues} issues")
        for issue in report.issues:
            print(f"  [{issue.severity}] {issue.file}:{issue.line} — {issue.description}")
```

## TypeScript: Zod Schemas

Use Zod to define schemas and convert to JSON Schema:

```typescript
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

const SecurityIssue = z.object({
  file: z.string(),
  line: z.number().int(),
  severity: z.enum(["low", "medium", "high"]),
  description: z.string(),
});

const SecurityReport = z.object({
  summary: z.string(),
  issues: z.array(SecurityIssue),
  total_issues: z.number().int(),
});

const q = query({
  prompt: "Review for security issues",
  options: {
    outputFormat: {
      type: "json_schema",
      schema: zodToJsonSchema(SecurityReport),
    },
  },
});

for await (const msg of q) {
  if (msg.type === "result" && msg.structured_output) {
    const report = SecurityReport.parse(msg.structured_output);
    console.log(`Found ${report.total_issues} issues`);
  }
}
```

## Accessing Results

Structured output is available on the `ResultMessage`:

### Python

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "result":
        if msg.subtype == "success" and msg.structured_output:
            data = msg.structured_output  # Already a dict
            print(json.dumps(data, indent=2))
        elif msg.subtype == "error_max_structured_output_retries":
            print("Failed to produce valid structured output")
```

### TypeScript

```typescript
for await (const msg of q) {
  if (msg.type === "result") {
    if (msg.subtype === "success" && msg.structured_output) {
      const data = msg.structured_output;
      console.log(JSON.stringify(data, null, 2));
    }
  }
}
```

### ResultMessage Fields

| Field | Type | Description |
|-------|------|-------------|
| `structured_output` | `dict \| None` | The structured output (if valid) |
| `result` | `str \| None` | Free-text result (always available) |
| `subtype` | `str` | `"success"` or `"error_max_structured_output_retries"` |

## Validation and Retries

When structured output doesn't match the schema, the SDK automatically retries:

1. Claude generates a response
2. SDK validates against the JSON Schema
3. If invalid, SDK sends the validation error back to Claude
4. Claude tries again with the error context
5. After max retries, yields `ResultMessage` with `subtype: "error_max_structured_output_retries"`

> The free-text `result` field is always populated regardless of structured output success.

## Practical Examples

### Code Analysis Report

```python
class FunctionInfo(BaseModel):
    name: str
    file: str
    line_number: int
    parameters: list[str]
    return_type: str | None
    docstring: str | None
    complexity: str  # "low", "medium", "high"

class CodeAnalysis(BaseModel):
    total_functions: int
    functions: list[FunctionInfo]
    languages_detected: list[str]

options = ClaudeAgentOptions(
    output_format={"type": "json_schema", "schema": CodeAnalysis.model_json_schema()},
    tools=["Read", "Glob", "Grep"],
    max_turns=30,
)
```

### Dependency Graph

```python
class Dependency(BaseModel):
    source: str
    target: str
    relationship: str  # "imports", "extends", "implements"

class DependencyGraph(BaseModel):
    nodes: list[str]
    edges: list[Dependency]
    circular_dependencies: list[list[str]]

options = ClaudeAgentOptions(
    output_format={"type": "json_schema", "schema": DependencyGraph.model_json_schema()},
)
```

### Test Results

```python
class TestResult(BaseModel):
    test_name: str
    status: str  # "passed", "failed", "skipped"
    duration_ms: int | None
    error_message: str | None

class TestSuite(BaseModel):
    total: int
    passed: int
    failed: int
    skipped: int
    results: list[TestResult]

options = ClaudeAgentOptions(
    output_format={"type": "json_schema", "schema": TestSuite.model_json_schema()},
)
```

## Common Pitfalls

1. **Schema must be valid JSON Schema** — the SDK validates the schema itself before sending to Claude
2. **`required` field matters** — omitting `required` means all properties are optional; Claude may skip them
3. **Complex schemas reduce reliability** — deeply nested schemas with many required fields increase retry likelihood
4. **`structured_output` can be None** — always check for `None` even on success (the agent might complete without producing structured output)
5. **Pydantic `model_json_schema()` produces valid JSON Schema** — but some Pydantic features (validators, custom types) don't translate to JSON Schema
6. **Cost of retries** — each retry consumes additional tokens; set `max_budget_usd` to cap costs
7. **Free-text result is always available** — even when structured output fails, `message.result` contains Claude's text response

## Related Topics

- [Configuration](01-configuration.md) — output_format in options
- [Overview](00-overview.md) — Result message types
- [Deployment](10-deployment.md) — Structured outputs in production pipelines
