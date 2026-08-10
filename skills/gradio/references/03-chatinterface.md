# Gradio — ChatInterface

> Source: [gradio.app/docs/gradio/chatinterface](https://gradio.app/docs/gradio/chatinterface)

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Function Signature](#function-signature)
- [Constructor Parameters](#constructor-parameters)
- [Streaming Responses](#streaming-responses)
- [Multimodal Chat](#multimodal-chat)
- [LLM Integration](#llm-integration)
- [Customization](#customization)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

`gr.ChatInterface` is a high-level wrapper purpose-built for chatbot UIs. It manages conversation history, message rendering, and user input — you just provide a response function.

## Basic Usage

```python
import gradio as gr

def echo(message, history):
    return f"You said: {message}"

demo = gr.ChatInterface(fn=echo)
demo.launch()
```

## Function Signature

The `fn` must accept exactly two positional arguments:

```python
def respond(message: str, history: list[dict]) -> str:
    """
    Args:
        message: The user's latest message (string).
        history: List of OpenAI-format dicts:
            [{"role": "user", "content": "Hi"},
             {"role": "assistant", "content": "Hello!"}]

    Returns:
        String, dict, Component, or list of messages.
    """
    return "Response text"
```

### Return Types

```python
# Simple string
def respond(message, history):
    return "Hello!"

# Dict (OpenAI format)
def respond(message, history):
    return {"role": "assistant", "content": "Hello!"}

# Multiple messages
def respond(message, history):
    return [
        {"role": "assistant", "content": "Let me think..."},
        {"role": "assistant", "content": "Here's my answer."},
    ]

# With metadata (e.g., thinking)
def respond(message, history):
    return {
        "role": "assistant",
        "content": "Final answer",
        "metadata": {"title": "Thinking", "log": "reasoning steps..."}
    }
```

## Constructor Parameters

### Core

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fn` | `Callable` | Required | Chat response function |
| `multimodal` | `bool` | `False` | Enable file uploads |
| `type` | `'messages' \| 'tuples'` | `'messages'` | History format |

### UI Elements

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str \| None` | `None` | Title above chatbot |
| `description` | `str \| None` | `None` | Description below title |
| `chatbot` | `gr.Chatbot \| None` | `None` | Custom Chatbot instance |
| `textbox` | `gr.Textbox \| gr.MultimodalTextbox \| None` | `None` | Custom input component |
| `submit_btn` | `str \| bool \| Button` | `True` | Submit button config |
| `stop_btn` | `str \| bool \| Button` | `True` | Stop button config |

### Behavior

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `editable` | `bool` | `False` | Allow editing past messages |
| `autofocus` | `bool` | `True` | Focus textbox on load |
| `autoscroll` | `bool` | `True` | Auto-scroll to bottom |
| `save_history` | `bool` | `False` | Persist in browser storage |
| `run_examples_on_click` | `bool` | `False` | Execute examples through fn |
| `fill_height` | `bool` | `True` | Expand to fill vertical space |

### Examples

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `examples` | `list[str] \| None` | `None` | Sample prompts |
| `example_labels` | `list[str] \| None` | `None` | Labels for examples |
| `example_icons` | `list[str] \| None` | `None` | Icons for examples |
| `cache_examples` | `bool \| None` | `None` | Cache example outputs |

### Additional Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `additional_inputs` | `str \| Component \| list \| None` | `None` | Extra inputs in accordion |
| `additional_outputs` | `Component \| list \| None` | `None` | Extra output components |
| `concurrency_limit` | `int \| None \| 'default'` | `'default'` | Max concurrent executions |

## Streaming Responses

Use a generator to stream token-by-token:

```python
import time

def stream_response(message, history):
    response = ""
    for word in message.split():
        response += word + " "
        time.sleep(0.1)
        yield response

demo = gr.ChatInterface(fn=stream_response)
demo.launch()
```

### Streaming with OpenAI

```python
from openai import OpenAI

client = OpenAI()

def predict(message, history):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        stream=True,
    )

    partial = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            partial += chunk.choices[0].delta.content
            yield partial

demo = gr.ChatInterface(fn=predict)
demo.launch()
```

## Multimodal Chat

Enable file uploads alongside text:

```python
def respond(message, history):
    text = message.get("text", "")
    files = message.get("files", [])

    if files:
        return f"Received {len(files)} file(s) with message: {text}"
    return f"You said: {text}"

demo = gr.ChatInterface(
    fn=respond,
    multimodal=True,
    textbox=gr.MultimodalTextbox(
        file_types=["image", ".pdf"],
        placeholder="Type a message or upload files...",
    ),
)
demo.launch()
```

## LLM Integration

### With Anthropic (Claude)

```python
import anthropic

client = anthropic.Anthropic()

def predict(message, history):
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=messages,
        stream=True,
    )

    partial = ""
    for event in response:
        if event.type == "content_block_delta":
            partial += event.delta.text
            yield partial

demo = gr.ChatInterface(fn=predict, title="Claude Chat")
demo.launch()
```

### With Additional Inputs

```python
def predict(message, history, system_prompt, temperature):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    # ... call LLM with temperature
    return response

demo = gr.ChatInterface(
    fn=predict,
    additional_inputs=[
        gr.Textbox("You are a helpful assistant.", label="System Prompt"),
        gr.Slider(0, 2, value=0.7, label="Temperature"),
    ],
)
demo.launch()
```

## Customization

### Custom Chatbot Component

```python
demo = gr.ChatInterface(
    fn=respond,
    chatbot=gr.Chatbot(
        height=600,
        bubble_full_width=False,
        avatar_images=("user.png", "bot.png"),
        show_copy_button=True,
        render_markdown=True,
        likeable=True,
    ),
)
```

### Inside Blocks

```python
with gr.Blocks() as demo:
    gr.Markdown("# My Custom Chat App")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            model = gr.Dropdown(["gpt-4", "gpt-3.5"], label="Model")

        with gr.Column(scale=3):
            chat = gr.ChatInterface(
                fn=predict,
                additional_inputs=[model],
            )
```

## Common Patterns

### System Prompt Template

```python
PROMPTS = {
    "Tutor": "You are a patient tutor...",
    "Coder": "You are a senior developer...",
    "Writer": "You are a creative writer...",
}

def predict(message, history, persona):
    system = PROMPTS[persona]
    # ... use system prompt with LLM

demo = gr.ChatInterface(
    fn=predict,
    additional_inputs=[
        gr.Dropdown(list(PROMPTS.keys()), value="Tutor", label="Persona"),
    ],
    examples=["Explain recursion", "Write a haiku", "Debug this code"],
)
```

### Conversation with Memory

```python
def predict(message, history):
    context = "\n".join(
        f"{m['role']}: {m['content']}" for m in history[-10:]
    )
    # Pass truncated history to LLM
    return llm_call(message, context)
```

## Common Pitfalls

1. **Wrong history format**: History uses OpenAI-style dicts (`{"role": ..., "content": ...}`), not tuples — unless you set `type="tuples"` (deprecated)
2. **Forgetting to yield**: For streaming, you must `yield` the accumulated response, not just the new token
3. **Blocking function**: Long-running sync functions block the event loop — use generators or async
4. **Multimodal message format**: When `multimodal=True`, `message` is a dict (`{"text": ..., "files": [...]}`) not a string
5. **Additional inputs order**: Additional inputs are appended as extra positional args after `message` and `history`
