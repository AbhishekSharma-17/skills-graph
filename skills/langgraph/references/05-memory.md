# LangGraph — Memory

> Source: [docs.langchain.com/oss/python/langgraph/memory](https://docs.langchain.com/oss/python/langgraph/memory)

## Table of Contents

- [Memory Architecture](#memory-architecture)
- [Short-Term Memory](#short-term-memory)
- [Long-Term Memory](#long-term-memory)
- [BaseStore API](#basestore-api)
- [InMemoryStore](#inmemorystore)
- [Memory Types Framework](#memory-types-framework)
- [Writing Strategies](#writing-strategies)
- [Accessing Store in Nodes](#accessing-store-in-nodes)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Memory Architecture

LangGraph provides two complementary memory systems:

| Type | Scope | Backed By | Use Case |
|------|-------|-----------|----------|
| **Short-term** | Within a thread | Checkpointer | Conversation history, turn-by-turn state |
| **Long-term** | Across threads | BaseStore | User preferences, learned facts, episodic memory |

```
Thread 1: [msg1, msg2, msg3]  ←  Short-term (checkpointer)
Thread 2: [msg1, msg2]        ←  Short-term (checkpointer)
                  ↓ ↑
        User Profile Store     ←  Long-term (BaseStore)
        {"name": "Alice", "prefs": {...}}
```

## Short-Term Memory

Short-term memory is the graph's state persisted via checkpointers. It remembers previous interactions within a single thread.

```python
from langgraph.checkpoint.memory import InMemorySaver

graph = StateGraph(MessagesState)
# ... add nodes and edges ...
app = graph.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "conv-1"}}

# Turn 1
app.invoke({"messages": [{"role": "user", "content": "My name is Alice"}]}, config)

# Turn 2 — agent remembers the name from Turn 1
app.invoke({"messages": [{"role": "user", "content": "What's my name?"}]}, config)
```

### Managing Conversation Length

Long conversations exceed LLM context windows. Strategies:

```python
from langchain_core.messages import RemoveMessage

def trim_messages_node(state: MessagesState) -> dict:
    if len(state["messages"]) > 20:
        to_remove = state["messages"][:-10]
        return {"messages": [RemoveMessage(id=m.id) for m in to_remove]}
    return {}

def summarize_and_trim(state: MessagesState) -> dict:
    if len(state["messages"]) > 20:
        summary = llm.invoke(
            f"Summarize this conversation:\n{format_messages(state['messages'][:-5])}"
        )
        keep = state["messages"][-5:]
        remove = [RemoveMessage(id=m.id) for m in state["messages"][:-5]]
        return {
            "messages": remove + [
                {"role": "system", "content": f"Previous summary: {summary.content}"}
            ] + keep
        }
    return {}
```

## Long-Term Memory

Long-term memory stores data across threads using the `BaseStore` API. It survives thread boundaries and process restarts.

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
app = graph.compile(checkpointer=checkpointer, store=store)
```

**Scoping with namespaces:**
```
("users", "alice")           → Alice's preferences
("users", "alice", "facts")  → Facts learned about Alice
("system", "rules")          → Application-level rules
```

## BaseStore API

The `BaseStore` abstract class defines four operations:

### put() — Write a Memory

```python
store.put(
    namespace=("users", "alice"),
    key="profile",
    value={"name": "Alice", "timezone": "UTC", "language": "en"},
)
```

### get() — Retrieve by Key

```python
item = store.get(namespace=("users", "alice"), key="profile")
print(item.value)  # {"name": "Alice", "timezone": "UTC", ...}
print(item.key)    # "profile"
print(item.namespace)  # ("users", "alice")
print(item.created_at)
print(item.updated_at)
```

### search() — Query a Namespace

```python
# List all items in namespace
items = store.search(namespace=("users", "alice"))

# With content filter
items = store.search(
    namespace=("users",),
    filter={"language": "en"},
)

# Semantic search (requires embedding config)
items = store.search(
    namespace=("knowledge",),
    query="How to deploy to production?",
    limit=5,
)
```

### delete() — Remove a Memory

```python
store.delete(namespace=("users", "alice"), key="profile")
```

## InMemoryStore

The built-in in-memory implementation supporting optional semantic search:

```python
from langgraph.store.memory import InMemoryStore

# Basic (no semantic search)
store = InMemoryStore()

# With embeddings for semantic search
from langchain_openai import OpenAIEmbeddings

store = InMemoryStore(
    index={
        "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
        "dims": 1536,
    }
)
```

**Production backends:**
- `PostgresStore` — durable, scalable, supports semantic search
- Community backends via `langgraph-checkpoint-*` packages

## Memory Types Framework

### Semantic Memory (Facts)

User-specific knowledge the agent learns over time:

```python
def update_user_profile(state: State, *, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"]["user_id"]
    
    # Extract facts from conversation
    facts = extract_facts(state["messages"])
    
    # Store each fact
    for fact in facts:
        store.put(
            namespace=("users", user_id, "facts"),
            key=fact["id"],
            value={"content": fact["text"], "confidence": fact["score"]},
        )
    return {}
```

**Approaches:**
- **Profile** — single continuously-updated document per user. Simpler but error-prone for large profiles.
- **Collection** — multiple narrow documents. Better recall, needs delete/update logic.

### Episodic Memory (Experiences)

Past successful interactions as few-shot examples:

```python
def retrieve_examples(state: State, *, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"]["user_id"]
    
    # Find similar past interactions
    examples = store.search(
        namespace=("users", user_id, "episodes"),
        query=state["messages"][-1].content,
        limit=3,
    )
    
    few_shot = "\n".join([e.value["interaction"] for e in examples])
    return {"context": f"Relevant past interactions:\n{few_shot}"}
```

### Procedural Memory (Instructions)

Dynamic system prompts that evolve based on feedback:

```python
def get_system_prompt(state: State, *, store: BaseStore):
    rules = store.search(namespace=("system", "rules"))
    prompt = "You are a helpful assistant.\n\nRules:\n"
    prompt += "\n".join([f"- {r.value['rule']}" for r in rules])
    return {"system_prompt": prompt}
```

## Writing Strategies

### Hot Path (Real-time)

Write memories during the conversation. Immediate availability but adds latency:

```python
def agent_with_memory(state: State, *, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"]["user_id"]
    
    # Read existing memories
    memories = store.search(namespace=("users", user_id, "facts"))
    
    # Generate response with memory context
    response = llm.invoke(state["messages"] + format_memories(memories))
    
    # Extract and save new facts (adds latency)
    new_facts = extract_facts_from_response(response)
    for fact in new_facts:
        store.put(("users", user_id, "facts"), fact["id"], fact)
    
    return {"messages": [response]}
```

### Background (Asynchronous)

Write memories after the conversation completes. No latency impact but delayed availability:

```python
# Use a separate background graph to process memories
memory_graph = StateGraph(...)
# Triggered post-conversation via cron, webhook, or event
```

## Accessing Store in Nodes

### In Graph API Nodes

```python
from langgraph.store.base import BaseStore

def my_node(state: State, config: RunnableConfig, *, store: BaseStore):
    user_id = config["configurable"]["user_id"]
    items = store.search(("users", user_id))
    return {"context": format_items(items)}

app = graph.compile(checkpointer=checkpointer, store=store)
app.invoke(inputs, {"configurable": {"thread_id": "t1", "user_id": "u1"}})
```

### In Functional API

```python
@entrypoint(checkpointer=checkpointer)
def workflow(query: str, *, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"]["user_id"]
    context = store.search(("users", user_id), query=query)
    return process_with_context(query, context)

workflow.invoke("question", config={"configurable": {"thread_id": "t1", "user_id": "u1"}})
```

## Common Patterns

### User-Scoped Memory

```python
namespace = ("users", user_id)
store.put(namespace, "preferences", {"theme": "dark", "language": "en"})
prefs = store.get(namespace, "preferences")
```

### Application-Level Knowledge Base

```python
namespace = ("knowledge", "faq")
store.put(namespace, "refund-policy", {"content": "Refunds within 30 days..."})

results = store.search(("knowledge", "faq"), query="How do I get a refund?")
```

## Common Pitfalls

1. **Confusing checkpointer and store** — Checkpointer = thread-scoped state. Store = cross-thread long-term memory.
2. **Missing `store` parameter in compile** — `graph.compile(checkpointer=cp, store=store)` to make store available in nodes.
3. **Namespace design** — Use hierarchical tuples: `("users", user_id, "type")`. Flat namespaces don't scale.
4. **Memory bloat** — Implement TTL or cleanup strategies for growing memory stores.
5. **InMemoryStore in production** — Data lost on restart. Use PostgresStore.

---

> **Related:** [04-persistence-checkpointing.md](04-persistence-checkpointing.md) for thread-scoped persistence, [06-streaming.md](06-streaming.md) for real-time output
