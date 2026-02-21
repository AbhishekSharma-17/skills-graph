# Sessions — Multi-Turn Conversations & State

## What is AgentSession

`AgentSession` manages conversation context across multiple `agent.run()` calls. Without a session, each call is independent — the agent forgets everything.

### Session Properties

| Property | Type | Description |
|---|---|---|
| `id` | `str` | Local unique identifier |
| `service_session_id` | `str` | Remote service conversation ID (when service manages history) |
| `state` | `dict` | Mutable key-value store for custom data |

## Creating Sessions

```python
# Create new session
session = agent.create_session()

# Create from existing service conversation
session = agent.get_session(service_session_id="<conversation-id>")
```

## Multi-Turn Conversation

```python
session = agent.create_session()

# Turn 1
r1 = await agent.run("My name is Alice.", session=session)
print(r1.text)  # "Nice to meet you, Alice!"

# Turn 2 — agent remembers previous context
r2 = await agent.run("What is my name?", session=session)
print(r2.text)  # "Your name is Alice!"

# Turn 3 — full conversation history available
r3 = await agent.run("What was the first thing I told you?", session=session)
print(r3.text)  # "You told me your name is Alice."
```

## Streaming with Sessions

```python
session = agent.create_session()

await agent.run("My name is Bob", session=session)

async for chunk in agent.run("Remind me of my name", stream=True, session=session):
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

## Session State — Custom Data

Store arbitrary data in `session.state`:

```python
session = agent.create_session()

# Store custom data
session.state["user_id"] = "user-123"
session.state["preferences"] = {
    "language": "en",
    "timezone": "US/Pacific",
}
session.state["cart_items"] = []

# Access in context providers or middleware
```

## Session Serialization — Persistence

```python
# Serialize to dict
serialized = session.to_dict()

# Store anywhere (JSON, Redis, database, file)
import json
with open("session.json", "w") as f:
    json.dump(serialized, f)

# Later: restore session
with open("session.json") as f:
    data = json.load(f)
restored = AgentSession.from_dict(data)

# Continue conversation
r = await agent.run("Where were we?", session=restored)
```

## Service-Managed vs Local Sessions

| Storage Mode | Where History Lives | Use Case |
|---|---|---|
| **Service-managed** | Server-side (Azure OpenAI Responses, Foundry) | Cloud agents, server handles persistence |
| **Local** | In `AgentSession.state` via history provider | Custom storage, any provider |

### Service-Managed History Providers

| Provider | Service Chat History | Custom History |
|---|:-:|:-:|
| Azure AI Foundry Agent | ✅ | ❌ |
| Azure OpenAI Responses | ✅ | ✅ |
| OpenAI Responses | ✅ | ✅ |
| Azure OpenAI Chat Completion | ❌ | ✅ |
| OpenAI Chat Completion | ❌ | ✅ |
| Anthropic Claude | ❌ | ❌ |
| Ollama | ❌ | ❌ |

### Rehydrate Service-Managed Session

```python
# Resume a service-managed conversation
session = agent.get_session(service_session_id="conv-abc-123")
response = await agent.run("Continue where we left off.", session=session)
```

## Important Rules

1. **Sessions are agent-specific** — don't reuse a session across different agent configurations
2. **Always pass `session=session`** — without it, no memory between turns
3. **Serialize for persistence** — sessions are in-memory by default, use `to_dict()`/`from_dict()` to persist
4. **Only one `load_messages=True`** — if using history providers, only one should load messages into context
5. **Treat session as opaque** — don't manually modify internal message arrays, use the API

## Complete Example — Persistent Chat

```python
import asyncio, json, os
from pathlib import Path
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity.aio import AzureCliCredential

SESSION_FILE = "chat_session.json"

async def main():
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )
    agent = client.as_agent(
        name="PersistentChat",
        instructions="You are a helpful assistant with memory.",
    )

    # Load or create session
    if Path(SESSION_FILE).exists():
        with open(SESSION_FILE) as f:
            session = AgentSession.from_dict(json.load(f))
        print("Resumed previous session.")
    else:
        session = agent.create_session()
        print("Started new session.")

    # Chat loop
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break

        response = await agent.run(user_input, session=session)
        print(f"Agent: {response.text}\n")

        # Save session after each turn
        with open(SESSION_FILE, "w") as f:
            json.dump(session.to_dict(), f)

if __name__ == "__main__":
    asyncio.run(main())
```
