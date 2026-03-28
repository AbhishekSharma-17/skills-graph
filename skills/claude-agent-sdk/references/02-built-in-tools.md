# Claude Agent SDK — Built-in Tools

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Tool Categories](#tool-categories)
- [File Operations](#file-operations)
- [Search Tools](#search-tools)
- [Execution Tools](#execution-tools)
- [Web Tools](#web-tools)
- [Orchestration Tools](#orchestration-tools)
- [MCP Tools](#mcp-tools)
- [Controlling Tool Availability](#controlling-tool-availability)
- [Tool Search](#tool-search)
- [Common Patterns](#common-patterns)

## Tool Categories

Built-in tools are the core capabilities that come with the Claude Agent SDK. They are the same tools available in Claude Code.

| Category | Tools | Description |
|----------|-------|-------------|
| **File Operations** | Read, Write, Edit, NotebookEdit | Read, create, and modify files |
| **Search** | Glob, Grep | Find files and search content |
| **Execution** | Bash, BashOutput, KillBash | Run terminal commands |
| **Web** | WebSearch, WebFetch | Search and fetch web content |
| **Orchestration** | Agent, AskUserQuestion, TodoWrite, Skill | Multi-agent and user interaction |
| **MCP** | ListMcpResources, ReadMcpResource, ToolSearch | MCP resource access |
| **Planning** | ExitPlanMode | Plan mode control |

## File Operations

### Read

Reads file contents. Supports text files, images (rendered visually), PDFs, and Jupyter notebooks.

```
Parameters:
  file_path  (required)  Absolute path to file
  offset     (optional)  Start line number
  limit      (optional)  Number of lines to read
  pages      (optional)  PDF page range (e.g., "1-5")
```

### Write

Creates a new file or completely rewrites an existing one. Prefer Edit for modifications.

```
Parameters:
  file_path  (required)  Absolute path
  content    (required)  Full file content
```

### Edit

Performs exact string replacements in existing files. More efficient than Write for modifications.

```
Parameters:
  file_path    (required)  Absolute path
  old_string   (required)  Text to find (must be unique in file)
  new_string   (required)  Replacement text
  replace_all  (optional)  Replace all occurrences (default: false)
```

### NotebookEdit

Edits Jupyter notebook cells by index.

```
Parameters:
  notebook_path  (required)  Absolute path to .ipynb file
  new_source     (required)  New cell content
  cell_type      (optional)  "code" or "markdown"
  edit_mode      (optional)  "replace", "insert", or "delete"
```

## Search Tools

### Glob

Fast file pattern matching. Returns paths sorted by modification time.

```
Parameters:
  pattern  (required)  Glob pattern (e.g., "**/*.py", "src/**/*.ts")
  path     (optional)  Directory to search in
```

### Grep

Content search using ripgrep. Supports regex and multiple output modes.

```
Parameters:
  pattern      (required)  Regex pattern
  path         (optional)  File or directory to search
  glob         (optional)  File filter (e.g., "*.py")
  type         (optional)  File type (e.g., "py", "js")
  output_mode  (optional)  "files_with_matches" (default), "content", "count"
  -A, -B, -C  (optional)  Context lines (after, before, both)
  multiline    (optional)  Enable multiline matching
```

## Execution Tools

### Bash

Executes shell commands in a persistent working directory.

```
Parameters:
  command          (required)  Shell command to execute
  description      (required)  What the command does
  timeout          (optional)  Timeout in ms (default: 120000, max: 600000)
  run_in_background (optional)  Run async, get notified on completion
```

> **Security note:** Bash is the most powerful and potentially dangerous tool. Consider restricting it in production via `disallowed_tools` or permission hooks.

### BashOutput / KillBash

`BashOutput` retrieves output from background Bash commands. `KillBash` terminates running commands.

## Web Tools

### WebSearch

Searches the web and returns results with links.

```
Parameters:
  query            (required)  Search query
  allowed_domains  (optional)  Only these domains
  blocked_domains  (optional)  Exclude these domains
```

### WebFetch

Fetches and processes web content using an AI model.

```
Parameters:
  url     (required)  URL to fetch
  prompt  (required)  What to extract from the page
```

## Orchestration Tools

### Agent

Spawns subagents for focused subtasks. Each runs in its own context window.

```
Parameters:
  prompt          (required)  Task description
  description     (required)  Short summary (3-5 words)
  subagent_type   (optional)  Named agent type from agents config
  model           (optional)  Model override
  run_in_background (optional)  Run async
```

### AskUserQuestion

Asks the user a question with multiple-choice options.

```
Parameters:
  questions  (required)  Array of questions with options
```

### TodoWrite

Tracks task progress with a structured todo list.

```
Parameters:
  todos  (required)  Array of {content, status, activeForm}
```

## MCP Tools

### ToolSearch

Dynamically discovers and loads tools from MCP servers. Enabled by default to save context window space — tool definitions are only loaded when needed.

### ListMcpResources / ReadMcpResource

Access MCP server resources (files, data, configurations) exposed by connected MCP servers.

## Controlling Tool Availability

Three mechanisms control which tools the agent can use:

### 1. `tools` — Restrict Built-in Tools

Limits which built-in tools are available. Does NOT affect MCP tools.

```python
# Only file reading and search
options = ClaudeAgentOptions(tools=["Read", "Glob", "Grep"])

# Remove ALL built-ins (only MCP tools available)
options = ClaudeAgentOptions(tools=[])
```

```typescript
const q = query({
  prompt: "...",
  options: { tools: ["Read", "Glob", "Grep"] },
});
```

### 2. `allowed_tools` — Pre-approve Tools

Pre-approves tools so they don't trigger permission prompts. Does NOT restrict — just auto-approves.

```python
options = ClaudeAgentOptions(
    allowed_tools=[
        "Read", "Glob", "Grep",        # Built-in tools
        "mcp__myserver__*",             # All tools from myserver
        "mcp__github__get_issue",       # Specific MCP tool
    ]
)
```

Supports wildcards: `mcp__server__*` matches all tools from that server.

### 3. `disallowed_tools` — Always Deny Tools

Blocks tools regardless of permission mode. Takes priority over `allowed_tools`.

```python
# Block dangerous tools even in bypassPermissions mode
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    disallowed_tools=["Bash", "Write", "Edit"],
)
```

### Evaluation Order

```
1. disallowed_tools  →  DENY (highest priority)
2. Permission mode check
3. allowed_tools     →  ALLOW (auto-approve)
4. can_use_tool      →  ALLOW or DENY (callback)
5. Default           →  Prompt user or deny
```

## Tool Search

Tool search is enabled by default. When many MCP tools are available, the SDK withholds their definitions from the context window and uses a search mechanism to load only relevant tools per turn.

```python
# Disable tool search (load all tool definitions into context)
options = ClaudeAgentOptions(extra_args={"--no-tool-search": None})
```

> **When to disable:** If you have few MCP tools (<20) and want Claude to always see them all.

## Common Patterns

### Read-Only Agent (No Write/Execute)

```python
options = ClaudeAgentOptions(
    tools=["Read", "Glob", "Grep", "WebSearch", "WebFetch"],
    disallowed_tools=["Write", "Edit", "Bash", "NotebookEdit"],
)
```

### Code-Writing Agent (No Web, No Bash)

```python
options = ClaudeAgentOptions(
    tools=["Read", "Write", "Edit", "Glob", "Grep"],
    disallowed_tools=["Bash", "WebSearch", "WebFetch"],
)
```

### MCP-Only Agent

```python
options = ClaudeAgentOptions(
    tools=[],  # No built-in tools
    mcp_servers={"myserver": server_config},
    allowed_tools=["mcp__myserver__*"],
)
```

### Selective Tool Approval

```python
options = ClaudeAgentOptions(
    permission_mode="default",
    allowed_tools=[
        "Read", "Glob", "Grep",             # Auto-approve read ops
        "mcp__github__get_issue",            # Auto-approve specific MCP tools
    ],
    # Write, Edit, Bash still require permission
)
```

## Related Topics

- [Custom Tools](03-custom-tools.md) — Define your own tools
- [MCP Integration](04-mcp-integration.md) — Connect external MCP servers
- [Permissions](06-permissions.md) — Permission modes and evaluation
