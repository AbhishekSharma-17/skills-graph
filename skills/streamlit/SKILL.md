---
name: streamlit
description: "Streamlit — Python framework for building interactive data apps and ML demos with minimal code. MANDATORY TRIGGERS: streamlit, Streamlit, st.write, st.dataframe, st.chat_input, st.cache_data, data app, streamlit deploy. Also trigger when user wants to build interactive dashboards in Python, create ML model demos, prototype data tools, build chat interfaces for LLMs with Python, or choose between Streamlit vs Gradio vs Dash. When in doubt about whether to use this skill for Python data app tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["streamlit", "python", "data-apps", "dashboards", "ml-demos", "chat-ui", "visualization", "interactive", "rapid-prototyping"]
---

# Streamlit — Skill Router

> A faster way to build and share data apps — turn Python scripts into interactive web apps in minutes.

**Source:** [streamlit.io](https://streamlit.io/) | **Version:** `1.59.x` | **GitHub:** 45K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Architecture** | `references/00-overview.md` | What Streamlit is, execution model, installation, project structure |
| **Text & Data Display** | `references/01-text-data-display.md` | Markdown, titles, dataframes, data_editor, metrics, JSON |
| **Input Widgets** | `references/02-input-widgets.md` | Buttons, selectors, sliders, text inputs, file uploads, feedback |
| **Charts & Visualization** | `references/03-charts-visualization.md` | Built-in charts, Plotly, Altair, Matplotlib, maps |
| **Layout & Containers** | `references/04-layout-containers.md` | Columns, tabs, sidebar, expanders, dialogs, popovers |
| **Session State** | `references/05-session-state.md` | State persistence, callbacks, widget keys, initialization patterns |
| **Caching & Performance** | `references/06-caching-performance.md` | cache_data, cache_resource, TTL, hash_funcs, mutation safety |
| **Forms & Fragments** | `references/07-forms-fragments.md` | Batch input, partial reruns, run_every, parallel fragments |
| **Multipage Apps** | `references/08-multipage-apps.md` | st.navigation, st.Page, routing, dynamic pages, auth gating |
| **Chat & LLM Integration** | `references/09-chat-llm.md` | Chat UI, streaming responses, LLM patterns, conversation history |
| **Media & Status** | `references/10-media-status.md` | Images, audio, video, progress bars, spinners, toasts, alerts |
| **Connections & Config** | `references/11-connections-config.md` | Database connections, secrets.toml, config.toml, page config |
| **Testing & Deployment** | `references/12-testing-deployment.md` | AppTest framework, Community Cloud, Docker, ASGI mounting |

## Installation

```bash
pip install streamlit

# With extras
pip install streamlit[snowflake]

# Run an app
streamlit run app.py

# Quick hello
streamlit hello
```

## Quick Reference

- [Streamlit Docs](https://docs.streamlit.io/)
- [API Reference](https://docs.streamlit.io/develop/api-reference)
- [GitHub](https://github.com/streamlit/streamlit)
- [PyPI](https://pypi.org/project/streamlit/)
- [Community Cloud](https://streamlit.io/cloud)
