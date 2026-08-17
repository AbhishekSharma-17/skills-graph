# Prompt Templates

> Source: https://docs.langchain.com/oss/python/langchain/prompts

## Table of Contents

- [Overview](#overview)
- [ChatPromptTemplate](#chatprompttemplate)
- [PromptTemplate](#prompttemplate)
- [Message Placeholders](#message-placeholders)
- [Few-Shot Prompting](#few-shot-prompting)
- [Prompt Composition](#prompt-composition)
- [Partial Variables](#partial-variables)
- [Multimodal Prompts](#multimodal-prompts)
- [Best Practices](#best-practices)

## Overview

Prompt templates transform user input into structured prompts for LLMs. They support variable substitution, message composition, few-shot examples, and multimodal content. Templates are Runnables and integrate with LCEL chains via the pipe operator.

## ChatPromptTemplate

The primary template for chat models. Produces a list of messages.

### From Messages

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role} expert."),
    ("human", "{question}")
])

messages = prompt.invoke({"role": "Python", "question": "Explain decorators"})
```

### Supported Message Tuples

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),          # SystemMessage
    ("human", "Hello {name}"),               # HumanMessage
    ("ai", "Hi! How can I help?"),           # AIMessage
    ("human", "What is {topic}?"),           # Another HumanMessage
])
```

### From Template String

```python
prompt = ChatPromptTemplate.from_template(
    "Tell me a joke about {topic}"
)
result = prompt.invoke({"topic": "programming"})
```

## PromptTemplate

For simple string prompts (non-chat models or single-message use).

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    "Summarize the following text:\n\n{text}\n\nSummary:"
)
result = prompt.invoke({"text": "LangChain is a framework..."})
```

### With Input Validation

```python
prompt = PromptTemplate(
    template="Translate '{text}' to {language}.",
    input_variables=["text", "language"]
)
```

## Message Placeholders

Insert dynamic message lists (conversation history, examples) into templates.

### MessagesPlaceholder

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("history"),
    ("human", "{question}")
])

from langchain_core.messages import HumanMessage, AIMessage

messages = prompt.invoke({
    "history": [
        HumanMessage("What is Python?"),
        AIMessage("Python is a programming language."),
    ],
    "question": "What are its key features?"
})
```

### Optional History

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder("history", optional=True),
    ("human", "{question}")
])

result = prompt.invoke({"question": "Hello"})
```

### Placeholder Shorthand

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    ("placeholder", "{history}"),
    ("human", "{question}")
])
```

## Few-Shot Prompting

### Static Examples

```python
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

examples = [
    {"input": "2+2", "output": "4"},
    {"input": "3*5", "output": "15"},
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}"),
])

few_shot = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a calculator."),
    few_shot,
    ("human", "{input}"),
])

result = prompt.invoke({"input": "7+8"})
```

### Dynamic Example Selection

```python
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(),
    FAISS,
    k=2,
)

few_shot = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    example_selector=selector,
    input_variables=["input"],
)
```

## Prompt Composition

### Combining Templates with Pipe

```python
system = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}.")
])
human = ChatPromptTemplate.from_messages([
    ("human", "{question}")
])

combined = system + human
result = combined.invoke({"role": "teacher", "question": "What is AI?"})
```

### In LCEL Chains

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise assistant."),
    ("human", "{question}")
])

chain = prompt | ChatOpenAI(model="gpt-4o") | StrOutputParser()
answer = chain.invoke({"question": "What is Python?"})
```

## Partial Variables

Pre-fill template variables so they don't need to be provided at invoke time.

### With Values

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Today is {date}. You are a {role}."),
    ("human", "{question}")
])

partial = prompt.partial(date="2026-08-18")
result = partial.invoke({"role": "teacher", "question": "What is ML?"})
```

### With Functions

```python
from datetime import datetime

prompt = ChatPromptTemplate.from_messages([
    ("system", "Today is {date}. Be helpful."),
    ("human", "{question}")
])

partial = prompt.partial(date=lambda: datetime.now().strftime("%Y-%m-%d"))
```

## Multimodal Prompts

### Image in Prompt

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a vision assistant."),
    ("human", [
        {"type": "text", "text": "{question}"},
        {"type": "image_url", "image_url": {"url": "{image_url}"}}
    ])
])

result = prompt.invoke({
    "question": "What is in this image?",
    "image_url": "https://example.com/photo.jpg"
})
```

## Best Practices

1. **Use ChatPromptTemplate** for chat models — `PromptTemplate` is for legacy string-in/string-out models
2. **Describe roles in system messages** — They set model behavior and persona
3. **Use MessagesPlaceholder for history** — Enables multi-turn conversations without manual list building
4. **Keep descriptions in field annotations** — For tools and structured output, field descriptions guide the model
5. **Prefer f-string style** — `{variable}` syntax is the default and most intuitive
6. **Use partial for shared context** — Dates, user info, and other common values can be pre-filled
7. **Test templates independently** — Call `.invoke()` on templates before wiring into chains
