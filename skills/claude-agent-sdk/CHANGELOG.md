# Changelog

## [1.4.0] — 2026-03-29

**Source version tracked**: Python `claude-agent-sdk` v0.1.51 / TypeScript `@anthropic-ai/claude-agent-sdk` v0.2.86

### Added

- **18-claude-agent-options.md** — Dedicated `ClaudeAgentOptions` deep reference:
  - "The 3 you always need" (`model`, `env`, `permission_mode`) with minimal boilerplate
  - All 38 parameters across 15 groups, each with: type, default, when-to-use, when-not-to-use, code examples
  - `env` — all 4 provider patterns: Anthropic direct, AWS Bedrock, Google Vertex AI, Azure AI Foundry
  - `permission_mode` — table with reads/edits/bash columns per mode
  - `allowed_tools` — all 17 built-in names listed, wildcard syntax
  - `can_use_tool` — callback signature with path-restriction and command-blocking examples
  - `hooks` — all 10 events with "Can modify?" column, audit + block example
  - `agents` / `AgentDefinition` — all 9 fields, `description` importance explained
  - `output_format` — json_schema example + gotcha on schema complexity
  - `setting_sources` — critical gotcha: default is `[]` (loads nothing)
  - `enable_file_checkpointing` — full setup with partner `extra_args`
  - TypeScript name mapping table (Python snake_case → TypeScript camelCase)
  - TypeScript-only parameters: `persistSession`, `abortController`, `spawnClaudeCodeProcess`, `debug`, `debugFile`, `sessionId`, `strictMcpConfig`, `resumeSessionAt`
  - Decision matrix — 7 complete use cases with recommended parameter sets: CI/CD, read-only analysis, interactive chat, production untrusted input, code generation with undo, structured extraction, multi-specialist sub-agents
  - All 38 parameters quick reference table with group column
  - Deprecated parameters migration guide

### Changed

- **SKILL.md** — Added routing entry for `18-claude-agent-options.md`, bumped to v1.4.0

### Stats

- Routing entries: 19
- Reference files: 19
- Total lines: ~9,090 (+600 from v1.3.0)

---

## [1.3.0] — 2026-03-29

**Source version tracked**: Python `claude-agent-sdk` v0.1.51 / TypeScript `@anthropic-ai/claude-agent-sdk` v0.2.86

### Added

- **16-query-and-messages.md** — Complete `query()` function reference from QUERY.md:
  - `query()` function signature (Python + TypeScript), keyword-only params
  - `query()` vs `ClaudeSDKClient` comparison table (10 features)
  - `AssistantMessage` full `@dataclass` fields with all types
  - Content blocks: `TextBlock`, `ToolUseBlock` (with `AskUserQuestion` special case), `ThinkingBlock` — all fields
  - `ResultMessage` full `@dataclass` fields + all `subtype` values with meanings
  - All other message types: `UserMessage`, `SystemMessage`, `TaskStartedMessage`, `TaskProgressMessage`, `TaskNotificationMessage`, `StreamEvent`, `RateLimitEvent`
  - Minimum Viable Options (3 levels: minimal, with tools, production)
  - Permission priority diagram with worked example
  - 7 complete patterns: simple question, file analysis, code generation, structured output, session resume, custom tools, streaming partial messages

- **17-client.md** — Complete `ClaudeSDKClient` reference from CLIENT.md:
  - What is ClaudeSDKClient + under-the-hood subprocess model
  - Constructor parameters with examples
  - Lifecycle: `async with` vs manual connect/disconnect, same-async-context warning
  - All 14 methods with: parameter table, description, when-to-use, code examples
  - `receive_messages()` vs `receive_response()` distinction (critical difference)
  - `rewind_files()` with full setup (enable_file_checkpointing, replay-user-messages)
  - `get_mcp_status()` with `McpStatusResponse` field table
  - `stop_task()` with `TaskStartedMessage`/`TaskNotificationMessage` handling
  - ClaudeSDKClient-only features table (8 capabilities not in query())
  - Message types specific to client (UserMessage UUID, Task messages, RateLimitEvent)
  - 8 complete patterns: multi-turn, human-in-loop, plan-then-execute, model switching, interrupt, file checkpointing, MCP health check, interactive chat loop
  - All 14 methods quick reference table
  - Typical usage flow (10-step)
  - Minimum viable client example

### Changed

- **01-configuration.md** — Added 4 missing deep-dive sections:
  - `can_use_tool` — custom permission callback with `PermissionResultAllow`/`PermissionResultDeny` example
  - `hooks` — all 10 hook events table + `HookMatcher` usage example
  - `agents` / `AgentDefinition` — all 9 fields table with typed example
  - `sandbox` / `SandboxSettings` — all 6 fields table with network config example
  - Extended Related Topics to link new files

- **SKILL.md** — Added 2 new routing entries for `16-query-and-messages.md` and `17-client.md`

### Stats

- Routing entries: 18
- Reference files: 18
- Total lines: ~8,490 (+1,820 from v1.2.0)

---

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
