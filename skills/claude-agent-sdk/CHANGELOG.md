# Changelog

## [1.1.0] — 2026-03-28

**Source version tracked**: Python `claude-agent-sdk` v0.1.51 / TypeScript `@anthropic-ai/claude-agent-sdk` v0.2.86

### Added

- **11-streaming.md** — StreamEvent, event types, partial messages, streaming vs single mode input, building streaming UIs
- **12-user-input.md** — AskUserQuestion structure, approval flows, canUseTool deep dive, option previews, free text
- **13-agent-loop.md** — Agent loop internals, turns, compaction, stop reasons, error types, rate limits, cost tracking
- **14-system-prompts-features.md** — 4 system prompt methods, CLAUDE.md, skills, slash commands, plugins, output styles
- **15-secure-deployment.md** — Docker hardening, credential management, proxy patterns, isolation technologies

### Changed

- **01-configuration.md** — Added SystemPromptPreset with append, deprecated fields, migration notes
- **05-hooks.md** — Added missing output fields (suppressOutput, stopReason, decision, updatedMCPToolOutput)
- **08-subagents.md** — Added filesystem agent definitions, resume subagents, 3 creation methods

### Stats

- Routing entries: 16
- Reference files: 16
- Total lines: ~5,817

---

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
- Total lines: ~3,809
