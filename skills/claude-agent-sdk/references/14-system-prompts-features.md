# Claude Agent SDK — System Prompts, Skills, Plugins & Features

> Source: [platform.claude.com/docs/en/agent-sdk/modifying-system-prompts](https://platform.claude.com/docs/en/agent-sdk/modifying-system-prompts), [skills](https://platform.claude.com/docs/en/agent-sdk/skills), [plugins](https://platform.claude.com/docs/en/agent-sdk/plugins), [slash-commands](https://platform.claude.com/docs/en/agent-sdk/slash-commands), [claude-code-features](https://platform.claude.com/docs/en/agent-sdk/claude-code-features) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [System Prompt Methods](#system-prompt-methods)
- [Default System Prompt Behavior](#default-system-prompt-behavior)
- [Method 1: CLAUDE.md Files](#method-1-claudemd-files)
- [Method 2: Output Styles](#method-2-output-styles)
- [Method 3: SystemPromptPreset with Append](#method-3-systempromptpreset-with-append)
- [Method 4: Custom System Prompt](#method-4-custom-system-prompt)
- [Setting Sources](#setting-sources)
- [Skills in the SDK](#skills-in-the-sdk)
- [Slash Commands](#slash-commands)
- [Plugins](#plugins)
- [Feature Comparison](#feature-comparison)
- [Common Patterns](#common-patterns)

## System Prompt Methods

There are four ways to configure the system prompt, each with different trade-offs:

| Method | Persistence | Shared via Git | Replaces Default |
|--------|------------|----------------|-----------------|
| CLAUDE.md files | Filesystem | Yes | No (appends) |
| Output styles | Filesystem | Yes | No (appends) |
| SystemPromptPreset + append | Session only | No | No (appends) |
| Custom string | Session only | No | Yes (replaces) |

## Default System Prompt Behavior

> **Critical:** The SDK uses a **minimal** system prompt by default — NOT Claude Code's full prompt. This is different from using Claude Code directly.

To get Claude Code's full prompt (with tool instructions, safety rules, etc.):

```python
options = ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code"},
)
```

Without this, the agent gets only basic instructions and may not use tools as effectively.

## Method 1: CLAUDE.md Files

Project instructions that persist on the filesystem and are loaded automatically when `setting_sources` includes `"project"`:

```python
options = ClaudeAgentOptions(
    setting_sources=["user", "project", "local"],
    # CLAUDE.md files are now loaded from:
    # - Project root: ./CLAUDE.md
    # - Project rules: .claude/rules/*.md
    # - Parent directories: ../CLAUDE.md, ../../CLAUDE.md, etc.
    # - User level: ~/.claude/CLAUDE.md
    # - User rules: ~/.claude/rules/*.md
    # - Local (gitignored): .claude/CLAUDE.local.md
)
```

### CLAUDE.md Loading Locations

| Location | Loaded When | Shared |
|----------|-------------|--------|
| `./CLAUDE.md` | `"project"` in setting_sources | Yes (via git) |
| `.claude/rules/*.md` | `"project"` in setting_sources | Yes (via git) |
| Parent dir CLAUDE.md | `"project"` in setting_sources | Yes |
| `~/.claude/CLAUDE.md` | `"user"` in setting_sources | No (user-only) |
| `~/.claude/rules/*.md` | `"user"` in setting_sources | No (user-only) |
| `.claude/CLAUDE.local.md` | `"local"` in setting_sources | No (gitignored) |
| Child dir CLAUDE.md | On demand (when agent enters dir) | Yes |

> **Important:** Auto memory (`~/.claude/projects/memory/`) is CLI-only and never loaded by the SDK.

## Method 2: Output Styles

Persistent style files that modify how Claude formats responses:

```
# Location: .claude/output-styles/concise.md or ~/.claude/output-styles/concise.md

---
name: concise
description: Short, direct responses without filler
---

Respond concisely. Use bullet points. No preamble or closing remarks.
Maximum 3 sentences per explanation.
```

Output styles are loaded when the appropriate `setting_sources` are configured.

## Method 3: SystemPromptPreset with Append

Use Claude Code's default prompt and append additional instructions:

```python
# Python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Additional rule: Always write tests for new code.",
    },
)
```

```typescript
// TypeScript
const q = query({
  prompt: "...",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: "Additional rule: Always write tests for new code.",
    },
  },
});
```

This gives you Claude Code's full capabilities plus your custom rules. Best when you want the default behavior with additions.

## Method 4: Custom System Prompt

Replace the system prompt entirely with a custom string:

```python
options = ClaudeAgentOptions(
    system_prompt="You are a Python security auditor. Only analyze code for vulnerabilities. Never modify files.",
)
```

> **Warning:** This replaces the entire default system prompt. Claude may not know how to use tools effectively without the default instructions. Use Method 3 (preset + append) when possible.

## Setting Sources

`setting_sources` controls which filesystem settings are loaded:

```python
# Default: no filesystem settings loaded
options = ClaudeAgentOptions(setting_sources=[])

# Load user-level settings (~/.claude/)
options = ClaudeAgentOptions(setting_sources=["user"])

# Load everything
options = ClaudeAgentOptions(setting_sources=["user", "project", "local"])
```

| Source | Loads From | Includes |
|--------|-----------|----------|
| `"user"` | `~/.claude/` | User CLAUDE.md, rules, output styles, settings.json |
| `"project"` | `.claude/` | Project CLAUDE.md, rules, skills, hooks, settings.json |
| `"local"` | `.claude/` (gitignored) | CLAUDE.local.md, local settings |

> **Critical gotcha:** Even `system_prompt={"preset": "claude_code"}` does NOT load CLAUDE.md files. You must also set `setting_sources` for filesystem settings.

### Filesystem Hooks

When `setting_sources` includes `"project"`, hooks from `settings.json` files are loaded:

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "echo 'Bash tool used'"}]
      }
    ]
  }
}
```

Filesystem hook types: `"command"` (shell), `"http"` (webhook), `"prompt"` (Claude prompt), `"agent"` (spawn agent).

## Skills in the SDK

Skills are SKILL.md files that provide Claude with specialized knowledge and capabilities.

### Requirements

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],     # Must load project settings
    allowed_tools=["Skill"],          # Must allow the Skill tool
)
```

### Skill Discovery

Skills are discovered from:
- `.claude/skills/` (project-level)
- `~/.claude/skills/` (user-level, requires `"user"` in setting_sources)
- Plugin skills (via `plugins` option)

### Important Notes

1. Skills are filesystem-only — no programmatic API for registering skills
2. The `allowed-tools` frontmatter in SKILL.md does NOT apply via SDK
3. Skills are auto-discovered at startup and listed in the `system:init` message
4. Claude invokes skills via the `Skill` tool — not directly called by your code

## Slash Commands

Slash commands are quick shortcuts for common tasks.

### Built-in Commands

| Command | Description |
|---------|-------------|
| `/compact` | Manually trigger context compaction |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |

### Custom Commands

Create custom commands as SKILL.md files with frontmatter:

```markdown
---
description: Run all tests
allowed-tools: Bash
model: haiku
argument-hint: test file pattern
---

Run tests matching $ARGUMENTS. If no argument, run all tests.

!`pytest $ARGUMENTS -v`
```

### Placeholders

| Placeholder | Description |
|-------------|-------------|
| `$1`, `$2` | Positional arguments |
| `$ARGUMENTS` | All arguments as a single string |
| `@filename` | Reference a file |

### Discovery

Available commands are reported in the `system:init` message:

```python
async for msg in query(prompt="/test auth", options=options):
    if msg.type == "system" and msg.subtype == "init":
        commands = msg.slash_commands  # List of available commands
```

### Compact Metadata

Custom commands can control compaction:

```yaml
---
description: My command
pre_tokens: 1000    # Tokens to preserve before command
trigger: always     # When to compact
---
```

## Plugins

Plugins extend the SDK with additional skills, commands, agents, hooks, and MCP servers.

### Configuration

```python
options = ClaudeAgentOptions(
    plugins=[{"type": "local", "path": "/path/to/plugin"}],
    setting_sources=["project"],  # Required for plugin discovery
)
```

### Plugin Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Required: plugin metadata
├── skills/                   # Plugin skills
│   └── my-skill/
│       └── SKILL.md
├── commands/                 # Legacy: slash commands
│   └── my-command.md
├── agents/                   # Plugin agents
│   └── my-agent.md
├── hooks/                    # Plugin hooks
└── .mcp.json                # Plugin MCP servers
```

### plugin.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My custom plugin"
}
```

### Namespacing

Plugin skills use namespaced names: `plugin-name:skill-name`

### Verification

Check loaded plugins in the init message:

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "system" and msg.subtype == "init":
        # Check for loaded plugins
        pass
```

## Feature Comparison

| Feature | Mechanism | Persistence | Scope |
|---------|-----------|------------|-------|
| **CLAUDE.md** | Filesystem | Persistent | Project/User |
| **Skills** | SKILL.md files | Persistent | Project/User/Plugin |
| **Subagents** | `agents` option | Session | Programmatic |
| **Hooks** | Callbacks or settings.json | Session or Persistent | Programmatic or Filesystem |
| **MCP Servers** | `mcp_servers` option or .mcp.json | Session or Persistent | Programmatic or Filesystem |
| **Slash Commands** | SKILL.md with frontmatter | Persistent | Project/User/Plugin |
| **Plugins** | Plugin directories | Persistent | Plugin scope |
| **Output Styles** | Markdown files | Persistent | User/Project |
| **System Prompt** | `system_prompt` option | Session | Programmatic |

## Common Patterns

### Full Claude Code Experience

```python
# Replicate the Claude Code CLI experience in the SDK
options = ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code"},
    setting_sources=["user", "project", "local"],
    allowed_tools=["Skill"],
    plugins=[{"type": "local", "path": "./my-plugin"}],
)
```

### Minimal Programmatic Agent

```python
# Clean, programmatic agent — no filesystem dependencies
options = ClaudeAgentOptions(
    system_prompt="You are a code reviewer. Find bugs and suggest fixes.",
    setting_sources=[],
    tools=["Read", "Glob", "Grep"],
)
```

### Project-Aware Agent

```python
# Load project settings but not user preferences
options = ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code"},
    setting_sources=["project"],
)
```

## Related Topics

- [Configuration](01-configuration.md) — system_prompt and setting_sources options
- [Hooks](05-hooks.md) — Programmatic hooks
- [Subagents](08-subagents.md) — Agent definitions
- [MCP Integration](04-mcp-integration.md) — MCP server configuration
