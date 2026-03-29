# Changelog

## [1.2.0] — 2026-03-29

**Source version tracked**: Python `claude-agent-sdk` v0.1.51 / TypeScript `@anthropic-ai/claude-agent-sdk` v0.2.86

### Changed

- **02-built-in-tools.md** — Major enrichment from `calude_agent_sdk_tools.md` reference:
  - Added Quick Reference Table covering all 18 tools (added `ToolSearch`) with `allowed_tools` strings and best-use summaries
  - Added detailed parameter tables for every tool (all 17 built-ins)
  - Added "When to use / When NOT to use" guidance for every tool
  - Added Claude call JSON examples (`tool_use` format) for each tool
  - Added Permission Modes table (`default`, `acceptEdits`, `plan`, `bypassPermissions`, `dontAsk`)
  - Added Decision Tree: Which Tool? (full flowchart)
  - Added Cost and Performance Reference table (all tools, cost/speed/notes)
  - Expanded Common Patterns from 3 to 9 (added per-phase restriction, subagent divide-and-conquer, read-only, code-writing, MCP-only, selective approval agents)
  - Added Best Practices section (10 rules)

- **03-custom-tools.md** — Targeted enrichment:
  - Added Tool Naming Convention section with `mcp__{server}__{name}` pattern and wildcard examples
  - Added Claude Tool Call Format block showing exact JSON Claude emits for custom tools
  - Added Complete End-to-End Example (`validate_email` + `calculate_hash` tools, MCP server packaging, agent usage)

- **SKILL.md** — Updated routing table descriptions for `02-built-in-tools.md` and `03-custom-tools.md` to reflect enriched content

### Stats

- Routing entries: 16
- Reference files: 16
- Total lines: ~6,670 (+853 from v1.1.0)

---

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
