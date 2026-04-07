# DSPy — Signatures

> Source: https://dspy.ai/learn/programming/signatures — Written for DSPy v2.5.x

## Overview

A **Signature** in DSPy declares the *I/O contract* of an LM call: what goes in, what comes out, and (optionally) a natural-language instruction describing the task. It is DSPy's replacement for hand-written prompts. You never write "You are a helpful assistant…" — you describe the *shape* of the task and let DSPy materialise the prompt.

There are two forms:

1. **Inline signatures** — short strings like `"question -> answer"` or `"context, question -> answer"`.
2. **Class-based signatures** — subclasses of `dspy.Signature` with typed fields and rich docstrings.

Use inline for quick prototypes; class-based everywhere else.

## Inline signatures

```python
import dspy

# Single input, single output
qa = dspy.Predict("question -> answer")

# Multiple inputs
summarise = dspy.Predict("document, audience -> summary")

# Multiple outputs
classify = dspy.Predict("text -> label, confidence")

# Typed inline (DSPy infers types from annotations)
rate = dspy.Predict("review -> rating: int")
```

Separators: `,` between fields on each side; `->` between inputs and outputs. Types default to `str`; add `: type` for anything else.

Supported inline types include `int`, `float`, `bool`, `list[str]`, `dict`, and Pydantic models.

## Class-based signatures

For non-trivial tasks, use a class. It gives you per-field descriptions, docstrings (which become the task instruction), and full type hints.

```python
import dspy

class ExtractInvoice(dspy.Signature):
    """Extract structured invoice data from free-form text."""

    text: str = dspy.InputField(desc="raw OCR text of the invoice")
    vendor: str = dspy.OutputField(desc="the name of the billing company")
    total_usd: float = dspy.OutputField(desc="the final amount owed in USD")
    due_date: str = dspy.OutputField(desc="ISO 8601 date, e.g. 2026-05-01")
```

Key parts:

- **Docstring** → becomes the module's instruction ("Extract structured invoice data …").
- **`dspy.InputField(...)`** → marks a field as an input. Optional `desc`.
- **`dspy.OutputField(...)`** → marks a field as an output. Optional `desc`.
- **Type annotations** → DSPy uses them for parsing and validation. Pydantic types work too.

## Typed outputs with Pydantic

Any Pydantic `BaseModel` works as a field type. DSPy parses the LM's output into the model and raises if parsing fails (which you can then catch or retry via Assertions).

```python
from pydantic import BaseModel, Field
import dspy

class Address(BaseModel):
    street: str
    city: str
    postal_code: str

class Person(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)
    address: Address

class ExtractPerson(dspy.Signature):
    """Extract a person record from unstructured text."""
    text: str = dspy.InputField()
    person: Person = dspy.OutputField()

predict = dspy.Predict(ExtractPerson)
result = predict(text="Alice Smith, 34, lives at 1 Main St, Springfield, 12345.")
print(result.person.address.city)  # "Springfield"
```

## Lists and enums

```python
from typing import Literal
import dspy

class Classify(dspy.Signature):
    """Assign one or more topics to a news headline."""
    headline: str = dspy.InputField()
    topics: list[str] = dspy.OutputField(desc="zero or more of: politics, sports, tech, finance")
    sentiment: Literal["positive", "neutral", "negative"] = dspy.OutputField()
```

`Literal[...]` is especially useful — DSPy will constrain the output to the listed values during parsing, and optimizers can use it to write more precise prompts.

## The instruction docstring

The docstring of a signature class is the **task instruction** that DSPy sends to the LM. Keep it:

- Short (one to three sentences).
- Action-oriented ("Extract…", "Classify…", "Rewrite…").
- Free of few-shot examples (the optimizer adds those).

```python
class TranslateToFrench(dspy.Signature):
    """Translate English text to idiomatic French. Preserve proper nouns verbatim."""
    english: str = dspy.InputField()
    french: str = dspy.OutputField()
```

Optimizers like `MIPROv2` may rewrite this instruction during compile to improve metric scores. If you want to freeze it, use the `instructions=` argument on `dspy.Signature.with_instructions(...)` at compile time.

## Updating a signature programmatically

You can mutate signatures at runtime. Useful for dynamic tool definitions in agents.

```python
sig = dspy.Signature("question -> answer")
sig = sig.with_instructions("Answer very tersely.")
sig = sig.append("citations", dspy.OutputField(), type_=list[str])
```

`append` returns a new signature with the extra field — signatures are immutable so you must reassign.

## Signature → Module

A signature by itself does nothing. You wrap it in a module to make it callable:

```python
predict = dspy.Predict(ExtractInvoice)
cot     = dspy.ChainOfThought(ExtractInvoice)   # adds a `rationale` field
react   = dspy.ReAct(ExtractInvoice, tools=[...])
```

See `02-modules.md` for the full module catalogue.

## Field order matters (a little)

DSPy renders input fields in the order they appear in the class. For inline signatures it uses the order in the string. Put the most important / canonical input first. For classification tasks, put the label field *last* among outputs so the LM sees the task description before committing to a label.

## Passing complex context

When one of your inputs is a retrieved passage list, pass it as `list[str]`:

```python
class Answer(dspy.Signature):
    """Answer the question using the passages."""
    passages: list[str] = dspy.InputField(desc="retrieved supporting context")
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()
```

DSPy will render each passage with a numbered bullet and wrap them in a context block automatically.

## Common pitfalls

- **Using the docstring to give few-shot examples.** Don't. Let the optimizer choose demos; keep the docstring abstract.
- **Forgetting a type annotation on an output field.** Without one DSPy assumes `str`, and a Pydantic class at the call site won't validate.
- **Naming a field `input` or `output`.** These shadow Python built-ins and DSPy internals. Use domain-specific names (`question`, `claim`, `summary`, `label`).
- **Using the same name twice across input and output.** Illegal — each field name must be unique across the signature.
- **Overloading one signature with many unrelated outputs.** Split into separate modules; each module is easier to optimise.
- **Calling a module with positional args.** Always use keyword arguments that match your input field names — `predict(text=...)` not `predict("...")`.

## Related topics

- **Wrapping signatures in modules:** `02-modules.md`
- **Parsing errors and self-refinement:** `07-assertions.md`
- **Using signatures in a RAG chain:** `06-rag-retrieval.md`
