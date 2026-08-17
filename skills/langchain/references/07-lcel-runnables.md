# LCEL & Runnables

> Source: https://docs.langchain.com/oss/python/langchain/lcel

## Table of Contents

- [Overview](#overview)
- [The Runnable Interface](#the-runnable-interface)
- [Pipe Operator](#pipe-operator)
- [RunnableSequence](#runnablesequence)
- [RunnableParallel](#runnableparallel)
- [RunnableLambda](#runnablelambda)
- [RunnablePassthrough](#runnablepassthrough)
- [RunnableBranch](#runnablebranch)
- [Chain Patterns](#chain-patterns)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
- [Common Patterns](#common-patterns)

## Overview

LangChain Expression Language (LCEL) is the declarative composition syntax for building chains. It uses the pipe operator (`|`) to connect components into pipelines. Every LangChain component — prompts, models, parsers, retrievers — implements the **Runnable** interface, making them composable.

## The Runnable Interface

Every Runnable exposes three core methods and their async counterparts:

| Method | Description | Async |
|--------|-------------|-------|
| `.invoke(input)` | Single input → single output | `.ainvoke(input)` |
| `.stream(input)` | Single input → streamed output | `.astream(input)` |
| `.batch(inputs)` | Multiple inputs → multiple outputs | `.abatch(inputs)` |

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

# All three work on any Runnable
result = model.invoke("Hello")
for chunk in model.stream("Hello"):
    print(chunk.content, end="")
results = model.batch(["Hello", "World"])
```

## Pipe Operator

The `|` operator creates a `RunnableSequence` where each step's output feeds the next:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Explain {topic} simply.")
model = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

chain = prompt | model | parser

result = chain.invoke({"topic": "quantum computing"})
print(result)  # Plain string output
```

Data flow: `dict → prompt → messages → model → AIMessage → parser → str`

## RunnableSequence

Created automatically by `|`. Steps execute in order.

```python
from langchain_core.runnables import RunnableSequence

chain = RunnableSequence(first=prompt, middle=[model], last=parser)
result = chain.invoke({"topic": "machine learning"})
```

### Inspect Chain

```python
chain = prompt | model | parser

print(chain.input_schema.model_json_schema())
print(chain.output_schema.model_json_schema())
print(chain.get_graph().draw_ascii())
```

## RunnableParallel

Run multiple runnables on the same input simultaneously. Output is a dict.

```python
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel(
    summary=prompt_summary | model | parser,
    keywords=prompt_keywords | model | parser,
    sentiment=prompt_sentiment | model | parser,
)

result = parallel.invoke({"text": "LangChain is amazing for building AI apps"})
print(result["summary"])
print(result["keywords"])
print(result["sentiment"])
```

### Dict Shorthand

A plain dict in a chain is automatically interpreted as RunnableParallel:

```python
from langchain_core.runnables import RunnablePassthrough

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | parser
)
```

## RunnableLambda

Wrap any Python function as a Runnable:

```python
from langchain_core.runnables import RunnableLambda

def format_output(text: str) -> str:
    return text.upper().strip()

chain = prompt | model | StrOutputParser() | RunnableLambda(format_output)
result = chain.invoke({"topic": "AI"})
```

### With Async Support

```python
async def async_process(text: str) -> str:
    await asyncio.sleep(0.1)
    return text.lower()

chain = prompt | model | StrOutputParser() | RunnableLambda(async_process)
result = await chain.ainvoke({"topic": "AI"})
```

### Decorator Syntax

```python
from langchain_core.runnables import chain as runnable_chain

@runnable_chain
def process_and_format(input_dict: dict) -> str:
    text = input_dict["text"]
    return f"Processed: {text.upper()}"
```

## RunnablePassthrough

Pass input through unchanged, optionally adding fields:

```python
from langchain_core.runnables import RunnablePassthrough

# Pass through unchanged
chain = RunnablePassthrough() | model

# Assign additional fields
chain = RunnablePassthrough.assign(
    word_count=lambda x: len(x["text"].split()),
    char_count=lambda x: len(x["text"])
)

result = chain.invoke({"text": "Hello world"})
# {"text": "Hello world", "word_count": 2, "char_count": 11}
```

### In RAG Chains

```python
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | parser
)

answer = chain.invoke("What is LangChain?")
```

## RunnableBranch

Conditional routing based on input:

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: x["type"] == "math", math_chain),
    (lambda x: x["type"] == "code", code_chain),
    general_chain  # Default
)

result = branch.invoke({"type": "math", "question": "What is 2+2?"})
```

### With Router Function

```python
from langchain_core.runnables import RunnableLambda

def route(input_dict):
    topic = input_dict.get("topic", "")
    if "python" in topic.lower():
        return python_chain
    elif "javascript" in topic.lower():
        return javascript_chain
    return general_chain

chain = RunnableLambda(route)
result = chain.invoke({"topic": "Python decorators"})
```

## Chain Patterns

### Simple Q&A Chain

```python
chain = (
    ChatPromptTemplate.from_template("Answer concisely: {question}")
    | ChatOpenAI(model="gpt-4o")
    | StrOutputParser()
)

answer = chain.invoke({"question": "What is LCEL?"})
```

### RAG Chain

```python
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_messages([
        ("system", "Answer based on context:\n{context}"),
        ("human", "{question}")
    ])
    | model
    | StrOutputParser()
)

answer = rag_chain.invoke("How does LangChain work?")
```

### Multi-Step Processing

```python
chain = (
    RunnablePassthrough.assign(
        summary=lambda x: summarize(x["text"]),
        language=lambda x: detect_language(x["text"]),
    )
    | ChatPromptTemplate.from_template(
        "The {language} text summary: {summary}\n\nTranslate to English."
    )
    | model
    | StrOutputParser()
)
```

### Map-Reduce

```python
from langchain_core.runnables import RunnableLambda

map_chain = ChatPromptTemplate.from_template("Summarize: {text}") | model | parser

def split_and_map(doc: str) -> list[str]:
    chunks = doc.split("\n\n")
    return map_chain.batch([{"text": c} for c in chunks])

reduce_chain = (
    RunnableLambda(lambda summaries: "\n".join(summaries))
    | ChatPromptTemplate.from_template("Combine summaries:\n{text}")
    | model
    | parser
)

full_chain = RunnableLambda(split_and_map) | reduce_chain
```

## Error Handling

### Fallbacks

```python
primary = ChatOpenAI(model="gpt-4o")
fallback = ChatAnthropic(model="claude-sonnet-4-6")

chain = prompt | primary.with_fallbacks([fallback]) | parser
```

### Retry

```python
chain = prompt | model.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True
) | parser
```

## Configuration

### Configurable Fields

```python
model = ChatOpenAI(model="gpt-4o").configurable_fields(
    model_name=ConfigurableField(id="model"),
    temperature=ConfigurableField(id="temp"),
)

chain = prompt | model | parser
result = chain.invoke(
    {"topic": "AI"},
    config={"configurable": {"model": "gpt-4o-mini", "temp": 0.0}}
)
```

### Configurable Alternatives

```python
model = ChatOpenAI(model="gpt-4o").configurable_alternatives(
    ConfigurableField(id="provider"),
    anthropic=ChatAnthropic(model="claude-sonnet-4-6"),
    google=ChatGoogleGenerativeAI(model="gemini-2.0-flash"),
)

chain = prompt | model | parser
result = chain.invoke(
    {"topic": "AI"},
    config={"configurable": {"provider": "anthropic"}}
)
```

## Common Patterns

### Add Callbacks

```python
chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [my_handler]}
)
```

### Add Tags and Metadata

```python
chain.invoke(
    {"topic": "AI"},
    config={
        "tags": ["production", "v2"],
        "metadata": {"user_id": "u123"}
    }
)
```

### Bind Stop Sequences

```python
chain = prompt | model.bind(stop=["\n"]) | parser
```
