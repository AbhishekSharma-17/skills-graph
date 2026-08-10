# Gradio — Streaming & Reactive Interfaces

> Source: [gradio.app/guides/streaming-outputs](https://gradio.app/guides/streaming-outputs) · [gradio.app/guides/reactive-interfaces](https://gradio.app/guides/reactive-interfaces)

## Table of Contents

- [Overview](#overview)
- [Generator Functions](#generator-functions)
- [Streaming Text Output](#streaming-text-output)
- [Streaming Audio](#streaming-audio)
- [Streaming Video](#streaming-video)
- [Streaming Inputs](#streaming-inputs)
- [Live Mode](#live-mode)
- [Timer Component](#timer-component)
- [Progress Bars](#progress-bars)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Gradio supports two forms of real-time interaction:

1. **Streaming outputs** — Generator functions that yield progressive results (text tokens, audio chunks, image steps)
2. **Reactive/live mode** — Auto-update outputs when inputs change, no submit button

## Generator Functions

Use `yield` instead of `return` to stream values progressively:

```python
import gradio as gr
import time

def generate_slowly(prompt):
    output = ""
    for word in prompt.split():
        output += word + " "
        time.sleep(0.3)
        yield output

demo = gr.Interface(fn=generate_slowly, inputs="textbox", outputs="textbox")
demo.launch()
```

Each `yield` replaces the output with the new value — yield the accumulated result, not just the delta.

## Streaming Text Output

### Token-by-Token (LLM Pattern)

```python
def stream_llm(prompt, history):
    response = ""
    for chunk in llm.stream(prompt):
        response += chunk.text
        yield response  # Yield accumulated text

demo = gr.ChatInterface(fn=stream_llm)
demo.launch()
```

### With Blocks

```python
def stream_text(prompt):
    result = ""
    for token in generate_tokens(prompt):
        result += token
        yield result

with gr.Blocks() as demo:
    prompt = gr.Textbox(label="Prompt")
    output = gr.Textbox(label="Response", lines=10)
    btn = gr.Button("Generate")

    btn.click(fn=stream_text, inputs=prompt, outputs=output)
```

### Image Generation Steps

```python
def generate_image_steps(prompt, steps):
    for i in range(steps):
        image = model.step(prompt, step=i)
        yield image  # Show each intermediate step

demo = gr.Interface(
    fn=generate_image_steps,
    inputs=[gr.Textbox(), gr.Slider(1, 50, value=20)],
    outputs=gr.Image(),
)
```

## Streaming Audio

Set `streaming=True` on the output Audio component:

```python
def generate_audio(text):
    for chunk in tts_model.stream(text):
        yield (24000, chunk)  # (sample_rate, numpy_array)

with gr.Blocks() as demo:
    text = gr.Textbox(label="Text")
    audio = gr.Audio(streaming=True, autoplay=True, label="Output")
    btn = gr.Button("Speak")

    btn.click(fn=generate_audio, inputs=text, outputs=audio)
```

### Audio Chunk Requirements

- Yield tuples of `(sample_rate, numpy_array)` or file paths
- Chunks should be ≥1 second for smooth playback
- Consistent sample rate across chunks
- Supported formats: `.mp3`, `.wav`, or raw bytes

## Streaming Video

```python
def generate_video(prompt):
    for frame_path in render_frames(prompt):
        yield frame_path  # .ts files with h.264 encoding

with gr.Blocks() as demo:
    prompt = gr.Textbox(label="Prompt")
    video = gr.Video(streaming=True, autoplay=True)
    btn = gr.Button("Generate")

    btn.click(fn=generate_video, inputs=prompt, outputs=video)
```

### Video Chunk Format

- Yield `.ts` (MPEG Transport Stream) files with h.264 encoding
- Or yield `.mp4` file paths
- Chunks are concatenated into a single streaming video output

## Streaming Inputs

Continuously stream from camera or microphone:

### Webcam Stream

```python
def process_frame(frame):
    # frame is a numpy array (H, W, 3)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return gray

demo = gr.Interface(
    fn=process_frame,
    inputs=gr.Image(sources=["webcam"], streaming=True),
    outputs=gr.Image(),
    live=True,
)
```

### Microphone Stream

```python
def transcribe_chunk(audio):
    sr, data = audio
    text = asr_model.transcribe(data, sample_rate=sr)
    return text

demo = gr.Interface(
    fn=transcribe_chunk,
    inputs=gr.Audio(sources=["microphone"], streaming=True),
    outputs="textbox",
    live=True,
)
```

### Streaming Input Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `time_limit` | `30` | Max seconds per streaming session |
| `stream_every` | `0.5` | How often to send chunks (seconds) |

```python
demo = gr.Interface(
    fn=process_frame,
    inputs=gr.Image(sources=["webcam"], streaming=True),
    outputs=gr.Image(),
    live=True,
    time_limit=60,
    stream_every=0.1,  # 10 FPS
)
```

## Live Mode

Auto-update outputs when any input changes — no submit button:

```python
def calculate(a, op, b):
    ops = {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else 0}
    return ops.get(op, 0)

demo = gr.Interface(
    fn=calculate,
    inputs=[
        gr.Number(label="A"),
        gr.Radio(["+", "-", "*", "/"], value="+"),
        gr.Number(label="B"),
    ],
    outputs="number",
    live=True,
)
```

### Live with Blocks

```python
with gr.Blocks() as demo:
    inp = gr.Textbox(label="Input")
    out = gr.Textbox(label="Output")

    # .input() fires only on user typing (not programmatic changes)
    inp.input(fn=str.upper, inputs=inp, outputs=out)
```

## Timer Component

Periodic updates without user interaction:

```python
import datetime

def get_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

with gr.Blocks() as demo:
    clock = gr.Textbox(label="Current Time")
    timer = gr.Timer(value=1)  # Every 1 second

    timer.tick(fn=get_time, outputs=clock)
```

### Dashboard Auto-Refresh

```python
with gr.Blocks() as demo:
    chart = gr.Plot(label="Live Metrics")
    timer = gr.Timer(value=30)  # Refresh every 30 seconds

    timer.tick(fn=fetch_metrics, outputs=chart)
    demo.load(fn=fetch_metrics, outputs=chart)  # Initial load
```

## Progress Bars

Show progress for long-running tasks:

```python
def train_model(data, epochs, progress=gr.Progress()):
    progress(0, desc="Starting training...")

    for epoch in range(epochs):
        for i, batch in enumerate(data):
            train_step(batch)
            progress(
                (epoch * len(data) + i) / (epochs * len(data)),
                desc=f"Epoch {epoch+1}/{epochs}",
            )

    progress(1.0, desc="Training complete!")
    return "Model trained successfully"
```

### Progress with Track Tqdm

```python
def process_files(files, progress=gr.Progress(track_tqdm=True)):
    from tqdm import tqdm
    results = []
    for f in tqdm(files, desc="Processing"):
        results.append(process(f))
    return results
```

## Common Patterns

### Streaming + Progress

```python
def generate_with_progress(prompt, progress=gr.Progress()):
    progress(0, desc="Initializing...")
    model = load_model()
    progress(0.1, desc="Generating...")

    result = ""
    tokens = model.generate(prompt, stream=True)
    for i, token in enumerate(tokens):
        result += token
        progress(0.1 + 0.9 * (i / 100), desc="Generating...")
        yield result

    progress(1.0, desc="Done!")
```

### Cancellable Streaming

```python
with gr.Blocks() as demo:
    prompt = gr.Textbox()
    output = gr.Textbox()
    start = gr.Button("Start")
    stop = gr.Button("Stop", variant="stop")

    event = start.click(fn=stream_text, inputs=prompt, outputs=output)
    stop.click(fn=None, cancels=[event])
```

### Real-Time Object Detection

```python
import cv2

def detect_objects(frame):
    results = yolo_model(frame)
    annotated = results[0].plot()
    return annotated

demo = gr.Interface(
    fn=detect_objects,
    inputs=gr.Image(sources=["webcam"], streaming=True),
    outputs=gr.Image(),
    live=True,
    stream_every=0.1,
)
```

## Common Pitfalls

1. **Yielding deltas instead of accumulated**: Each `yield` replaces the entire output — yield the full result so far, not just the new token
2. **Missing `streaming=True`**: Audio and video components need `streaming=True` to play chunks as they arrive
3. **Small audio chunks**: Chunks shorter than 1 second cause choppy playback — buffer before yielding
4. **`live=True` with expensive functions**: Every keystroke triggers the function — add debouncing or use `.submit()` instead
5. **Progress bar type hint**: `progress=gr.Progress()` must be a parameter with the `gr.Progress()` default — it's detected by type, not position
6. **Stream cancellation**: Without a stop button, long-running generators can't be interrupted — always provide cancel capability
