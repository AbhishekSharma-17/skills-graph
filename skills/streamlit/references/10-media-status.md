# Streamlit — Media & Status Elements

> Source: [docs.streamlit.io/develop/api-reference](https://docs.streamlit.io/develop/api-reference) | Version: 1.59.x

## Table of Contents

- [Images](#images)
- [Audio](#audio)
- [Video](#video)
- [PDF Display](#pdf-display)
- [Progress Indicators](#progress-indicators)
- [Status Messages](#status-messages)
- [Celebratory Effects](#celebratory-effects)
- [Common Patterns](#common-patterns)

## Images

### st.image

```python
import streamlit as st

# From file path
st.image("photo.jpg", caption="My photo")

# From URL
st.image("https://example.com/image.png", width=300)

# From NumPy array
import numpy as np
img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
st.image(img_array, caption="Random noise")

# From PIL
from PIL import Image
img = Image.open("photo.jpg")
st.image(img, use_container_width=True)
```

Parameters:

```python
st.image(
    image,                          # Path, URL, ndarray, PIL.Image, bytes
    caption="Optional caption",
    width=None,                     # Width in pixels
    use_container_width=False,      # Scale to container
    clamp=False,                    # Clamp pixel values to [0, 255]
    channels="RGB",                 # "RGB" or "BGR"
    output_format="auto",          # "JPEG", "PNG", "auto"
)
```

### Clickable Image (v1.55+)

```python
event = st.image("photo.jpg", on_click="rerun", key="my_image")
if event and event.click:
    st.write(f"Clicked at ({event.click.x}, {event.click.y})")
```

### st.logo

Place a logo in the sidebar:

```python
st.logo(
    image="logo_full.png",          # Shown when sidebar expanded
    icon_image="logo_icon.png",     # Shown when sidebar collapsed
    link="https://myapp.com",       # Click destination
)
```

## Audio

### st.audio

```python
# From file
st.audio("song.mp3")

# From bytes
audio_bytes = open("audio.wav", "rb").read()
st.audio(audio_bytes, format="audio/wav")

# From URL
st.audio("https://example.com/audio.mp3")

# With parameters
st.audio(
    audio_bytes,
    format="audio/mp3",
    start_time=30,           # Start at 30 seconds
    sample_rate=44100,       # For raw audio data
    autoplay=False,
    loop=False,
)
```

### Audio from NumPy

```python
import numpy as np

sample_rate = 44100
duration = 2
freq = 440  # A4 note

t = np.linspace(0, duration, int(sample_rate * duration))
audio = np.sin(2 * np.pi * freq * t)

st.audio(audio, sample_rate=sample_rate)
```

## Video

### st.video

```python
# From file
st.video("video.mp4")

# From URL
st.video("https://youtu.be/example")

# With parameters
st.video(
    video_bytes,
    format="video/mp4",
    start_time=10,
    subtitles={"English": "subs_en.vtt", "Spanish": "subs_es.vtt"},
    autoplay=False,
    loop=False,
    muted=False,
)
```

### Subtitles

```python
# Single subtitle track
st.video("video.mp4", subtitles="captions.vtt")

# Multiple tracks
st.video("video.mp4", subtitles={
    "English": "en.vtt",
    "French": "fr.vtt",
})
```

## PDF Display

### st.pdf (v1.55+)

```python
st.pdf("document.pdf")

# From bytes
with open("report.pdf", "rb") as f:
    st.pdf(f.read())

# Specific page
st.pdf("document.pdf", page=3)
```

## Progress Indicators

### st.progress

```python
import time

progress = st.progress(0, text="Processing...")
for i in range(100):
    time.sleep(0.01)
    progress.progress(i + 1, text=f"Processing... {i+1}%")
progress.empty()  # Remove after completion
```

### st.spinner

```python
with st.spinner("Loading data..."):
    data = load_data()  # Spinner shows while this runs

st.success("Data loaded!")
```

### st.status — Multi-Step Progress

```python
with st.status("Running analysis...", expanded=True) as status:
    st.write("Loading data...")
    data = load_data()

    st.write("Training model...")
    model = train_model(data)

    st.write("Generating report...")
    report = generate_report(model)

    status.update(label="Analysis complete!", state="complete", expanded=False)
```

States: `"running"` (default), `"complete"`, `"error"`

### st.skeleton — Loading Placeholder (v1.55+)

```python
with st.skeleton(height=200):
    # Shows a skeleton/shimmer placeholder while loading
    st.line_chart(load_chart_data())
```

## Status Messages

### Alert Messages

```python
st.success("Operation completed successfully!")
st.info("This is an informational message.")
st.warning("Proceed with caution.")
st.error("An error occurred!")

# With icon
st.success("Done!", icon="✅")
st.error("Failed!", icon="🚨")
```

### st.exception

Display a formatted exception:

```python
try:
    result = 1 / 0
except Exception as e:
    st.exception(e)
```

### st.toast — Brief Notification

```python
st.toast("File saved!", icon="💾")

# Toast disappears after a few seconds
if st.button("Save"):
    save_data()
    st.toast("Saved successfully!")
```

Multiple toasts stack:

```python
for i in range(3):
    st.toast(f"Step {i+1} complete")
    time.sleep(1)
```

## Celebratory Effects

```python
st.balloons()  # Floating balloon animation
st.snow()      # Falling snowflake animation
```

Use sparingly — triggered on every rerun if not guarded:

```python
if st.button("Celebrate"):
    st.balloons()
```

## Common Patterns

### Image Gallery

```python
images = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"]
cols = st.columns(4)

for i, img in enumerate(images):
    with cols[i % 4]:
        st.image(img, use_container_width=True)
```

### Upload and Preview Image

```python
uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
if uploaded:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(uploaded, use_container_width=True)
    with col2:
        st.subheader("Processed")
        img = Image.open(uploaded).convert("L")  # Grayscale
        st.image(img, use_container_width=True)
```

### Progress with Caching

```python
@st.cache_data(show_spinner="Loading dataset...")
def load_large_dataset():
    return pd.read_parquet("large_file.parquet")

df = load_large_dataset()  # Spinner shows only on first load
```

### Multi-Step Pipeline

```python
steps = ["Load data", "Clean data", "Train model", "Evaluate"]

with st.status("Running pipeline...") as status:
    for i, step in enumerate(steps):
        st.write(f"Step {i+1}: {step}")
        time.sleep(1)  # Simulate work
    status.update(label="Pipeline complete!", state="complete")
```

### Error Handling with Status

```python
try:
    with st.spinner("Processing..."):
        result = process_data()
    st.success(f"Result: {result}")
except ValueError as e:
    st.error(f"Validation error: {e}")
except Exception as e:
    st.exception(e)
```

## Related Topics

- `01-text-data-display.md` — Text and data elements
- `04-layout-containers.md` — Image and media layout
- `06-caching-performance.md` — Caching with spinners
