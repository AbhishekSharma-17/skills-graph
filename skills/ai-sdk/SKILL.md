---
name: ai-sdk
description: "Vercel AI SDK for building AI-powered applications with streaming, tool calling, agents, and multi-provider support. MANDATORY TRIGGERS: ai-sdk, vercel ai, useChat, streamText, generateText, AI SDK. Also trigger when building chatbots, AI streaming interfaces, LLM tool calling in TypeScript/JavaScript, or multi-provider AI apps. When in doubt about whether to use this skill for AI app development tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ai", "llm", "streaming", "tools", "agents", "vercel", "typescript", "react", "nextjs"]
---

# AI SDK (Vercel)

> Version tracked: 6.x (v6.0.158) | Source: https://ai-sdk.dev

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview](references/00-overview.md) | Starting with AI SDK, installation, core concepts |
| [01-providers-and-models](references/01-providers-and-models.md) | Configuring providers, switching models, custom providers |
| [02-generating-text](references/02-generating-text.md) | Using generateText/streamText, callbacks, options |
| [03-structured-output](references/03-structured-output.md) | Generating typed objects/arrays, schema validation |
| [04-tool-calling](references/04-tool-calling.md) | Defining tools, execution, approval, multi-step |
| [05-agents](references/05-agents.md) | Building agents, ToolLoopAgent, subagents, memory |
| [06-streaming-patterns](references/06-streaming-patterns.md) | Stream protocols, transforms, backpressure |
| [07-useChat-hook](references/07-useChat-hook.md) | Chat UI with React, transports, status management |
| [08-mcp-integration](references/08-mcp-integration.md) | Model Context Protocol clients, tools from MCP servers |
| [09-embeddings-and-rag](references/09-embeddings-and-rag.md) | Embeddings, similarity, RAG patterns |
| [10-middleware-and-telemetry](references/10-middleware-and-telemetry.md) | Middleware, DevTools, observability, testing |
| [11-multimodal-generation](references/11-multimodal-generation.md) | Images, speech, transcription, video |
| [12-deployment-patterns](references/12-deployment-patterns.md) | Next.js, Node.js, edge, serverless deployment |

## Installation

```bash
npm install ai @ai-sdk/openai @ai-sdk/anthropic @ai-sdk/google
# or
pnpm add ai @ai-sdk/openai @ai-sdk/anthropic @ai-sdk/google
```

## Quick Reference

- Docs: https://ai-sdk.dev
- GitHub: https://github.com/vercel/ai
- npm: https://www.npmjs.com/package/ai
- DevTools: `npx @ai-sdk/devtools`
- Migration: `npx @ai-sdk/codemod upgrade v6`
