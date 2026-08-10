---
name: gradio
description: "Gradio — Python library for building interactive ML demos and web apps with minimal code. MANDATORY TRIGGERS: gradio, Gradio, gr.Interface, gr.Blocks, gr.ChatInterface, gr.Audio, gr.Image, Hugging Face demo, gradio deploy. Also trigger when user wants to build ML model demos, create AI chatbot UIs, prototype data tools with Python, share models via web links, or choose between Gradio vs Streamlit vs Dash. When in doubt about whether to use this skill for Python ML demo tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["gradio", "python", "ml-demos", "hugging-face", "chatbot-ui", "web-apps", "interactive", "model-serving", "rapid-prototyping"]
---

# Gradio — Skill Router

> Build and share delightful machine learning apps, all in Python.

**Source:** [gradio.app](https://gradio.app/) | **Version:** `6.22.x` | **GitHub:** 37K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Installation** | `references/00-overview.md` | What Gradio is, architecture, installation, quick start |
| **Interface API** | `references/01-interface.md` | gr.Interface, string shortcuts, examples, caching, launch |
| **Blocks API** | `references/02-blocks.md` | gr.Blocks, Row/Column/Tab layout, flexible UIs |
| **ChatInterface** | `references/03-chatinterface.md` | Chatbot UIs, multimodal chat, LLM integration |
| **Components** | `references/04-components.md` | Textbox, Image, Audio, Video, Slider, Dropdown, Gallery |
| **Events & Interactivity** | `references/05-events-interactivity.md` | Event listeners, click/change/submit, chaining, gr.on |
| **State Management** | `references/06-state-management.md` | gr.State, session state, global state, BrowserState |
| **Streaming & Reactive** | `references/07-streaming-reactive.md` | Generator functions, live mode, streaming audio/video |
| **Theming & Styling** | `references/08-theming-styling.md` | Themes, custom CSS/JS, elem_id, head injection |
| **Queuing & Performance** | `references/09-queuing-performance.md` | Queue system, concurrency, batching, progress bars |
| **Sharing & Deployment** | `references/10-sharing-deployment.md` | Share links, HF Spaces, Docker, embedding, auth |
| **Clients & API** | `references/11-clients-api.md` | Python/JS clients, API endpoints, MCP server |
| **Custom Components** | `references/12-custom-components.md` | Creating, building, publishing custom components |

## Installation

```bash
pip install gradio

# Run a simple demo
python app.py

# Deploy to Hugging Face Spaces
gradio deploy
```

## Quick Reference

- [Gradio Docs](https://gradio.app/docs)
- [Guides](https://gradio.app/guides)
- [GitHub](https://github.com/gradio-app/gradio)
- [PyPI](https://pypi.org/project/gradio/)
- [Hugging Face Spaces](https://huggingface.co/spaces)
