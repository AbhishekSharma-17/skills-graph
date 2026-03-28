# Changelog

## [1.0.0] — 2026-03-28

**Source version tracked**: Python `claude-agent-sdk` v0.1.51 / TypeScript `@anthropic-ai/claude-agent-sdk` v0.2.86

### Added

- **00-overview.md** — Architecture, installation, authentication, quickstart (Python + TypeScript), message types
- **01-configuration.md** — ClaudeAgentOptions / Options, all fields, model selection, thinking, effort, env vars
- **02-built-in-tools.md** — All built-in tools, categories, controlling availability, tool search
- **03-custom-tools.md** — @tool decorator, tool() function, input schemas, return types, annotations, error handling
- **04-mcp-integration.md** — MCP server types (stdio/HTTP/SSE/SDK), configuration, .mcp.json, tool naming
- **05-hooks.md** — Hook events, matchers, callbacks, permission decisions, async hooks, Python vs TS differences
- **06-permissions.md** — Permission modes, evaluation order, canUseTool, dynamic changes, security
- **07-sessions.md** — One-shot, multi-turn, ClaudeSDKClient, resume, fork, session management functions
- **08-subagents.md** — AgentDefinition, spawning, model selection, tool scoping, limitations, patterns
- **09-structured-outputs.md** — output_format, JSON Schema, Pydantic, Zod, validation, error handling
- **10-deployment.md** — System requirements, deployment patterns, sandboxes, cost tracking, security, checkpointing

### Stats

- Routing entries: 11
- Reference files: 11
- Total lines: ~3,500
