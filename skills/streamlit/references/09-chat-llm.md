# Streamlit — Chat & LLM Integration

> Source: [docs.streamlit.io/develop/tutorials/llms](https://docs.streamlit.io/develop/tutorials/llms) | Version: 1.59.x

## Table of Contents

- [Chat Elements](#chat-elements)
- [Building a Chatbot](#building-a-chatbot)
- [Streaming Responses](#streaming-responses)
- [OpenAI Integration](#openai-integration)
- [Anthropic Integration](#anthropic-integration)
- [LangChain Integration](#langchain-integration)
- [Advanced Chat Patterns](#advanced-chat-patterns)
- [Common Pitfalls](#common-pitfalls)

## Chat Elements

### st.chat_message

Display a message in a chat-style container:

```python
with st.chat_message("user"):
    st.write("Hello! Can you help me?")

with st.chat_message("assistant"):
    st.write("Of course! What do you need?")
```

Parameters:

```python
with st.chat_message(
    name="user",          # "user", "assistant", "ai", "human", or custom string
    avatar=None,          # URL, file path, emoji, or None (uses default)
):
    st.write("Message content")
    st.image("chart.png")   # Can contain any Streamlit element
    st.code("print('hi')")
```

Custom avatars:

```python
with st.chat_message("assistant", avatar="🤖"):
    st.write("I'm a robot!")

with st.chat_message("user", avatar="https://example.com/avatar.png"):
    st.write("Custom avatar image")
```

### st.chat_input

Text input pinned to the bottom of the app:

```python
prompt = st.chat_input("Say something")
if prompt:
    st.write(f"User said: {prompt}")
```

Parameters:

```python
prompt = st.chat_input(
    placeholder="Type a message...",
    key="chat_input",
    max_chars=500,
    disabled=False,
    on_submit=my_callback,
)
```

## Building a Chatbot

### Echo Bot (Minimal)

```python
import streamlit as st

st.title("Echo Bot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What's up?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    response = f"Echo: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
```

### Chat Pattern Anatomy

1. **Initialize** message history in session state
2. **Replay** all previous messages on each rerun
3. **Accept** new input via `st.chat_input`
4. **Display** user message immediately
5. **Generate** assistant response
6. **Store** both messages in session state

## Streaming Responses

### st.write_stream

Display streamed text with a typewriter effect:

```python
import time

def response_generator(prompt):
    response = f"You said: {prompt}. Here is a detailed response."
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(prompt))

    st.session_state.messages.append({"role": "assistant", "content": response})
```

`st.write_stream` accepts:
- Generator functions that `yield` strings
- OpenAI-style streaming response objects
- Any iterable of strings

## OpenAI Integration

```python
import streamlit as st
from openai import OpenAI

st.title("ChatGPT Clone")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask ChatGPT"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
```

### Secrets Setup

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."
```

## Anthropic Integration

```python
import streamlit as st
import anthropic

st.title("Claude Chat")

client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Claude"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with client.messages.stream(
            model="claude-sonnet-5-20261015",
            max_tokens=1024,
            messages=st.session_state.messages,
        ) as stream:
            response = st.write_stream(stream.text_stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
```

## LangChain Integration

```python
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

st.title("LangChain Chat")

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=st.secrets["OPENAI_API_KEY"],
    streaming=True,
)

if "lc_messages" not in st.session_state:
    st.session_state.lc_messages = []

for msg in st.session_state.lc_messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

if prompt := st.chat_input("Ask"):
    human_msg = HumanMessage(content=prompt)
    st.session_state.lc_messages.append(human_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(
            llm.stream(st.session_state.lc_messages)
        )

    st.session_state.lc_messages.append(AIMessage(content=response))
```

## Advanced Chat Patterns

### System Prompt Configuration

```python
with st.sidebar:
    system_prompt = st.text_area(
        "System Prompt",
        value="You are a helpful data analysis assistant.",
        height=150,
    )
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

if prompt := st.chat_input("Ask"):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages)
    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature,
        stream=True,
    )
```

### Chat with File Upload

```python
uploaded_file = st.sidebar.file_uploader("Upload a document", type=["pdf", "txt"])

if uploaded_file:
    content = uploaded_file.read().decode()
    st.session_state.context = content
    st.sidebar.success(f"Loaded: {uploaded_file.name}")

if prompt := st.chat_input("Ask about the document"):
    full_prompt = prompt
    if "context" in st.session_state:
        full_prompt = f"Context:\n{st.session_state.context}\n\nQuestion: {prompt}"
    # ... send to LLM
```

### Clear Chat History

```python
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
```

### Chat with Tool Calls / Function Calling

```python
import json

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]

def get_weather(city: str) -> str:
    return f"72°F and sunny in {city}"

# In the chat loop after getting a response with tool_calls:
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "get_weather":
            args = json.loads(tool_call.function.arguments)
            result = get_weather(**args)
            # Append tool result and continue conversation
```

### Multi-Model Chat

```python
with st.sidebar:
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "claude-sonnet"])

if "gpt" in model:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    # ... OpenAI streaming
else:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    # ... Anthropic streaming
```

## Common Pitfalls

### 1. Not Storing Messages

```python
# Wrong — messages disappear on rerun
if prompt := st.chat_input():
    st.write(prompt)  # Gone after next interaction

# Correct — persist in session state
st.session_state.messages.append({"role": "user", "content": prompt})
```

### 2. Not Replaying History

Each rerun clears the UI. Always replay stored messages:

```python
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
```

### 3. Infinite Message Accumulation

Long conversations consume tokens. Implement a sliding window:

```python
MAX_MESSAGES = 20
if len(st.session_state.messages) > MAX_MESSAGES:
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]
```

### 4. API Key Exposure

Never hardcode API keys. Use `.streamlit/secrets.toml` and add it to `.gitignore`.

## Related Topics

- `05-session-state.md` — State for chat history
- `10-media-status.md` — Spinners and progress during generation
- `11-connections-config.md` — Secrets management
