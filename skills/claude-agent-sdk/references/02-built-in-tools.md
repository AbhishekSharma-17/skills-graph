# Claude Agent SDK — Built-in Tools

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Quick Reference Table](#quick-reference-table)
- [Tool Categories](#tool-categories)
- [File Operations](#file-operations)
- [Search Tools](#search-tools)
- [Execution Tools](#execution-tools)
- [Web Tools](#web-tools)
- [Orchestration Tools](#orchestration-tools)
- [MCP Tools](#mcp-tools)
- [Controlling Tool Availability](#controlling-tool-availability)
- [Tool Search](#tool-search)
- [Decision Tree: Which Tool?](#decision-tree-which-tool)
- [Cost and Performance Reference](#cost-and-performance-reference)
- [Common Patterns](#common-patterns)

---

## Quick Reference Table

| # | Tool | Purpose | `allowed_tools` String | Best For |
|---|------|---------|----------------------|----------|
| 1 | **Read** | Read file/image contents | `"Read"` | Exploring files, reading docs |
| 2 | **Glob** | Find files by glob pattern | `"Glob"` | Discovering files, mass file discovery |
| 3 | **Grep** | Search file contents (regex) | `"Grep"` | Finding patterns, code search |
| 4 | **Write** | Create or overwrite files | `"Write"` | Generating new files, complete replacements |
| 5 | **Edit** | Replace specific text in files | `"Edit"` | Surgical fixes, targeted changes |
| 6 | **Bash** | Execute shell commands | `"Bash"` | Running scripts, system operations |
| 7 | **NotebookEdit** | Edit Jupyter notebook cells | `"NotebookEdit"` | Modifying notebooks in-place |
| 8 | **WebSearch** | Search the web for info | `"WebSearch"` | Research, finding URLs, latest info |
| 9 | **WebFetch** | Fetch and parse web content | `"WebFetch"` | Reading full articles, page content |
| 10 | **TodoWrite** | Manage task lists | `"TodoWrite"` | Multi-step work tracking, progress |
| 11 | **BashOutput** | Read output from background processes | `"BashOutput"` | Long-running tasks, monitoring |
| 12 | **KillBash** | Stop background shell processes | `"KillBash"` | Process cleanup, interrupts |
| 13 | **Agent** | Spawn subagents for parallel work | `"Agent"` | Parallel multi-specialist tasks |
| 14 | **AskUserQuestion** | Prompt user for input | `"AskUserQuestion"` | Interactive workflows, human-in-loop |
| 15 | **ExitPlanMode** | Request approval to execute | `"ExitPlanMode"` | Plan-before-execute workflows |
| 16 | **ListMcpResources** | List MCP server resources | `"ListMcpResources"` | Resource discovery from MCP servers |
| 17 | **ReadMcpResource** | Read MCP resource content | `"ReadMcpResource"` | Accessing MCP resource data |
| 18 | **ToolSearch** | Dynamically load MCP tool definitions | `"ToolSearch"` | Large MCP tool sets, context management |
| — | **Custom Tools** | User-defined via `@tool()` | `"mcp__<server>__<tool>"` | Domain-specific logic |

---

## Tool Categories

Built-in tools are the core capabilities that come with the Claude Agent SDK. They are the same tools available in Claude Code.

| Category | Tools | Description |
|----------|-------|-------------|
| **File Operations** | Read, Write, Edit, NotebookEdit | Read, create, and modify files |
| **Search** | Glob, Grep | Find files and search content |
| **Execution** | Bash, BashOutput, KillBash | Run terminal commands |
| **Web** | WebSearch, WebFetch | Search and fetch web content |
| **Orchestration** | Agent, AskUserQuestion, TodoWrite | Multi-agent and user interaction |
| **MCP** | ListMcpResources, ReadMcpResource, ToolSearch | MCP resource access |
| **Planning** | ExitPlanMode | Plan mode control |

---

## File Operations

### Read

Reads file contents. Supports text files, code, logs, images (PNG/JPG), PDFs, and Jupyter notebooks.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | `str` | Yes | Absolute or relative path to file |
| `offset` | `int` | No | Start reading from line number (0-indexed) |
| `limit` | `int` | No | Number of lines to read (default: all) |
| `pages` | `str` | No | PDF page range (e.g., `"1-5"`) |

**When to use:**
- Load files to analyze before editing
- Read knowledge base or config documents
- Examine image files (passed visually to Claude)
- Read large files incrementally using `offset`/`limit`

**When NOT to use:**
- Don't use for files >100MB without `offset`/`limit`
- Don't use to write files (use Write)
- Don't use for binary files (only text/images/PDFs supported)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "Read",
  "input": {
    "file_path": "/path/to/file.py",
    "offset": 10,
    "limit": 50
  }
}
```

**Cost/Performance:** Minimal cost (input tokens = file size). ~1-2ms per MB.

---

### Write

Creates a new file OR completely overwrites an existing one. No merging, no appending.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | `str` | Yes | Path where file will be created |
| `content` | `str` | Yes | Entire file content (replaces existing) |

**When to use:**
- Generating new Python/config/report files from scratch
- Complete file regeneration
- Initializing files that don't exist yet

**When NOT to use:**
- Don't use to modify just one part of a file (use Edit)
- Don't use if file might have user edits (use Edit for safety)
- Don't use for appending to logs (use `Bash echo >>` instead)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "Write",
  "input": {
    "file_path": "/output/generated_code.py",
    "content": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello')\n"
  }
}
```

**Cost/Performance:** Token cost = output tokens for file content. ~1-2ms to write.

---

### Edit

Performs exact string replacements in an existing file. Everything else stays unchanged.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | `str` | Yes | Path to existing file |
| `old_string` | `str` | Yes | Exact text to find and replace (must be unique in file) |
| `new_string` | `str` | Yes | Replacement text |
| `replace_all` | `bool` | No | If `True`, replace ALL occurrences (default: first only) |

**Critical:** `old_string` must be an EXACT match including indentation, spacing, newlines. Always read the file first.

**When to use:**
- Fixing a bug in one function
- Adding a single line to a config
- Updating documentation in code
- Renaming variables in targeted locations

**When NOT to use:**
- Don't use for complete file rewrites (use Write instead)
- Don't use without reading the file first
- Don't use if `old_string` appears many times and you only want some (add surrounding context)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "Edit",
  "input": {
    "file_path": "/src/auth.py",
    "old_string": "if not password:\n    return False",
    "new_string": "if not password:\n    logger.warning(\"Empty password\")\n    return False"
  }
}
```

**Best practice — add context when `old_string` appears multiple times:**

```json
{
  "old_string": "def login(user, password):\n    if not password:\n        return False",
  "new_string": "def login(user, password):\n    if not password:\n        logger.warning(\"Empty password\")\n        return False"
}
```

**Cost/Performance:** Proportional to file size. ~1-5ms for typical edits.

---

### NotebookEdit

Edits Jupyter notebook cells directly without raw JSON manipulation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notebook_path` | `str` | Yes | Path to `.ipynb` file |
| `new_source` | `str` | Yes | New cell content |
| `cell_type` | `str` | No | `"code"` or `"markdown"` (inferred if omitted) |
| `edit_mode` | `str` | No | `"replace"`, `"insert"`, or `"delete"` |
| `cell_number` | `int` | No | Cell index (0-based) to edit or insert after |

**When to use:**
- Fixing bugs in notebook code cells
- Updating markdown explanations
- Adding new cells with results
- Automating notebook generation

**When NOT to use:**
- Don't use for massive notebook rewrites (too fragile)
- Avoid modifying notebooks with complex cell references

**Claude call example (edit existing cell):**

```json
{
  "type": "tool_use",
  "name": "NotebookEdit",
  "input": {
    "notebook_path": "/analysis.ipynb",
    "cell_number": 3,
    "new_source": "result = df.groupby('category').sum()\nprint(result)",
    "cell_type": "code"
  }
}
```

**Claude call example (insert new cell after cell 5):**

```json
{
  "type": "tool_use",
  "name": "NotebookEdit",
  "input": {
    "notebook_path": "/analysis.ipynb",
    "edit_mode": "insert",
    "cell_number": 5,
    "new_source": "## Analysis Complete\nAll data validated.",
    "cell_type": "markdown"
  }
}
```

**Cost/Performance:** ~5-10ms per edit. Minimal token cost.

---

## Search Tools

### Glob

Fast file pattern matching. Returns paths sorted by modification time.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pattern` | `str` | Yes | Glob pattern (e.g., `**/*.py`, `src/**/*.test.*`) |
| `path` | `str` | No | Directory to search (default: current directory) |

**Pattern examples:**

```
*.py              → all .py files in current dir only
**/*.py           → all .py files recursively (most common)
src/**/*.test.*   → all test files under src/
data/*            → all files in data/ (non-recursive)
**/*config*       → any file with "config" in name anywhere
```

**When to use:**
- Find all files of a specific type
- Discover project structure
- Build file lists for analysis
- Mass file discovery before processing

**When NOT to use:**
- Don't use to search file CONTENTS (use Grep)
- Don't use for exact filename matching if you already know the path
- Avoid on very large directories (millions of files)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "Glob",
  "input": {
    "pattern": "**/*.sql",
    "path": "/data/sql_files"
  }
}
```

**Cost/Performance:** Minimal. ~10-50ms depending on filesystem size. No token cost.

---

### Grep

Content search using ripgrep. Supports full regex and multiple output modes.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pattern` | `str` | Yes | Regex pattern (e.g., `"TODO\|FIXME"`, `"def \w+"`) |
| `path` | `str` | No | Directory to search (default: current) |
| `glob` | `str` | No | File filter (e.g., `"*.py"`) |
| `type` | `str` | No | File type (e.g., `"py"`, `"js"`) |
| `output_mode` | `str` | No | `"files_with_matches"` (default), `"content"`, `"count"` |
| `-A` / `-B` / `-C` | `int` | No | Lines after/before/context |
| `-i` | `bool` | No | Case-insensitive search |
| `multiline` | `bool` | No | Enable multiline matching |

**When to use:**
- Find all TODO/FIXME comments
- Search for function definitions across a codebase
- Find imports or dependencies
- Pattern-based code analysis
- Locate configuration keys

**When NOT to use:**
- Don't use for simple file name matching (use Glob)
- Don't use for binary file search

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "Grep",
  "input": {
    "pattern": "ERROR|WARN|TODO",
    "path": "/var/log",
    "output_mode": "content"
  }
}
```

**Regex syntax (ripgrep):**
- `"def \w+"` → function definitions
- `"^\s*#"` → comments
- `"\d{4}-\d{2}-\d{2}"` → ISO dates
- `"(?:foo|bar)"` → non-capturing groups

**Cost/Performance:** Proportional to file count. ~50-500ms depending on dataset size. Token cost = matched lines.

---

## Execution Tools

### Bash

Executes arbitrary shell commands on the system.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | `str` | Yes | Shell command(s) to execute |
| `description` | `str` | Yes | What the command does (shown in permission prompts) |
| `timeout` | `int` | No | Timeout in ms (default: 120000, max: 600000) |
| `run_in_background` | `bool` | No | If `True`, returns PID immediately — use BashOutput to poll |

**POWERFUL AND RISKY** — Claude can run anything: pip install, git, Python, etc.

**When to use:**
- Running test suites
- Building/compiling code
- Starting development servers
- Git operations
- Package management
- System operations

**When NOT to use:**
- Don't give Bash access for untrusted prompts
- Don't use for simple file operations (Read/Write/Edit are safer)
- Avoid on servers with sensitive data without `disallowed_tools`

**Configuration options:**

```python
# Allow Bash
allowed_tools=["Bash"]

# Block Bash entirely
disallowed_tools=["Bash"]
```

**Claude call example (foreground):**

```json
{
  "type": "tool_use",
  "name": "Bash",
  "input": {
    "command": "python3 -m pytest tests/ -v --tb=short",
    "description": "Run test suite",
    "run_in_background": false
  }
}
```

**Claude call example (background — returns PID):**

```json
{
  "type": "tool_use",
  "name": "Bash",
  "input": {
    "command": "python3 long_task.py",
    "description": "Start long-running task",
    "run_in_background": true
  }
}
```

Returns: `{"pid": 12345, "status": "started"}` — then use BashOutput and KillBash.

**Cost/Performance:** Varies widely. Execution time = token cost. 10s command ≈ 30 output tokens.

---

### BashOutput

Read output from a background Bash process using its PID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pid` | `int` | Yes | Process ID from previous `Bash` call with `run_in_background=true` |

**When to use:**
- Polling long-running background tasks
- Checking progress of background scripts
- Reading partial output before process completes
- Tailing logs from running services

**When NOT to use:**
- Don't use without first starting a background process
- Don't use on PIDs you don't own

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "BashOutput",
  "input": {
    "pid": 12345
  }
}
```

**Returns:** Accumulated stdout/stderr since last check.

**Cost/Performance:** Minimal. ~10-50ms. No token cost (just reads buffer).

---

### KillBash

Terminate a background shell process by PID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pid` | `int` | Yes | Process ID to kill |

**When to use:**
- Stopping long-running background tasks
- Interrupting stuck processes
- Cleanup after BashOutput polling

**When NOT to use:**
- Don't use without a valid PID
- Don't use on system processes
- Avoid if process cleanup is critical (may not gracefully flush state)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "KillBash",
  "input": {
    "pid": 12345
  }
}
```

**Returns:** `{"status": "killed", "pid": 12345}`

**Cost/Performance:** Minimal. ~50-100ms.

---

## Web Tools

### WebSearch

Searches the web for live, up-to-date information (not from training data).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `str` | Yes | Search query (e.g., `"Claude API pricing 2026"`) |
| `allowed_domains` | `list[str]` | No | Restrict results to these domains |
| `blocked_domains` | `list[str]` | No | Exclude these domains |

**When to use:**
- Finding latest package versions
- Checking current API pricing
- Researching recent news or events
- Looking up information beyond training cutoff
- Discovering URLs to fetch with WebFetch

**When NOT to use:**
- Don't use for internal documentation (use Read)
- Don't use if you already have the information
- Avoid excessive searches (each = token cost)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "WebSearch",
  "input": {
    "query": "claude-agent-sdk latest version PyPI 2026"
  }
}
```

**Returns:** List of search results with titles, snippets, URLs.

**Cost/Performance:** High token cost. Each search ≈ 50-100 output tokens per result. ~500ms latency.

**Common pattern:** Use WebSearch to find URLs, then WebFetch to read full content.

---

### WebFetch

Fetch the full content of a specific URL you already know.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Full HTTP(S) URL to fetch |
| `prompt` | `str` | Yes | What to extract from the page |

**When to use:**
- Reading documentation pages
- Fetching API reference docs
- Reading articles or blog posts
- Getting full content after WebSearch found the URL

**When NOT to use:**
- Don't use without a specific URL (use WebSearch first)
- Don't use for large binaries (text pages only)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "WebFetch",
  "input": {
    "url": "https://platform.claude.com/docs/en/agent-sdk/overview",
    "prompt": "Summarize available tools"
  }
}
```

**Returns:** AI-extracted page content (HTML cleaned to readable text).

**Cost/Performance:** Moderate cost. Page content = input tokens. ~1-2 seconds per fetch.

---

## Orchestration Tools

### Agent (Subagents)

Spawns child agents that work independently. Multiple subagents can run in parallel.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | `str` | Yes | Task prompt for the subagent |
| `description` | `str` | Yes | Short summary (3-5 words) |
| `subagent_type` | `str` | No | Name of custom agent from `agents={}` config |
| `model` | `str` | No | Model override for this subagent |
| `run_in_background` | `bool` | No | Run async, get notified on completion |

**KEY BEHAVIORS:**
- Each subagent starts with FRESH context (no parent history)
- Multiple subagents can run in PARALLEL
- Subagents CANNOT spawn their own subagents (no nesting)
- Parent receives final result as a tool result
- Each subagent has its own model/tools (if defined in `agents={}`)

**When to use:**
- Parallel analysis of multiple files
- Specialized sub-tasks (one agent security, one for bugs)
- Divide-and-conquer for large problems
- Offloading work to cheaper models

**When NOT to use:**
- Don't use for sequential tasks (just use turns)
- Avoid if subagents need parent context/conversation history
- Don't overuse (each subagent = full API call)

**Configuration (defining custom agents):**

```python
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Agent", "Read", "Glob"],
    agents={
        "bug-finder": AgentDefinition(
            description="Finds bugs in code",
            prompt="Look for logic errors, edge cases, and runtime issues.",
            tools=["Read"],
            model="sonnet",
        ),
        "security-scanner": AgentDefinition(
            description="Finds security issues",
            prompt="Look for hardcoded secrets, injection risks, unsafe patterns.",
            tools=["Read", "Grep"],
            model="sonnet",
        ),
    }
)
```

**Claude call example (general-purpose subagent):**

```json
{
  "type": "tool_use",
  "name": "Agent",
  "input": {
    "description": "Calculate revenue totals",
    "prompt": "Read data/sales.csv and calculate total revenue by region"
  }
}
```

**Claude call example (custom named agent):**

```json
{
  "type": "tool_use",
  "name": "Agent",
  "input": {
    "subagent_type": "bug-finder",
    "description": "Scan auth module",
    "prompt": "Analyze src/auth.py for security bugs"
  }
}
```

**Cost/Performance:** Very high. Each subagent = full API call. 2-3x cost of a single turn.

---

### AskUserQuestion

Pause and ask the user a question. Claude waits for the answer to continue.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | `str` | Yes | Question to ask the user |
| `options` | `list[str]` | No | Multiple choice options |

**CRITICAL:** Only works with `ClaudeSDKClient` (multi-turn stateful). Does NOT work with single-call `query()`.

**When to use:**
- Interactive CLI applications
- Human-in-the-loop workflows
- Getting clarification or choices
- Decision points in complex tasks
- User approval gates

**When NOT to use:**
- Don't use with `query()` — no way to send reply back
- Don't use in batch/non-interactive pipelines

**How to handle in code:**

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient(options=options) as client:
    await client.query("Ask which file to analyze")
    async for message in client.receive_response():
        if block.name == "AskUserQuestion":
            answer = input("→ Your answer: ")
            await client.query(answer)  # Send reply back
```

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "AskUserQuestion",
  "input": {
    "question": "Which file should I refactor?",
    "options": ["auth.py", "db.py", "api.py"]
  }
}
```

**Cost/Performance:** Blocks execution. No token cost while waiting.

---

### TodoWrite

Manage a task list. Claude updates it as it works (`pending` → `in_progress` → `completed`).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `todos` | `list[TodoItem]` | Yes | Array of todo items |

**TodoItem structure:**

```python
{
    "id": "todo-1",                    # unique ID
    "content": "Read database schema",  # task description
    "status": "completed",              # "pending" | "in_progress" | "completed"
    "priority": "high"                  # "high" | "medium" | "low"
}
```

**When to use:**
- Multi-step complex tasks
- Auditing many files (one todo per file)
- Long workflows needing visibility
- Coordinating parallel subagent work

**When NOT to use:**
- Don't use for simple one-turn tasks
- This is in-memory only (not persisted externally)

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "TodoWrite",
  "input": {
    "todos": [
      {"id": "task-1", "content": "Analyze schema.sql", "status": "completed", "priority": "high"},
      {"id": "task-2", "content": "Find all DATEDIFF() calls", "status": "in_progress", "priority": "high"},
      {"id": "task-3", "content": "Check window functions", "status": "pending", "priority": "medium"}
    ]
  }
}
```

**Cost/Performance:** Minimal. ~5-10 output tokens per todo item.

---

### ExitPlanMode

Requests approval to transition from plan mode (read-only) to execution mode (modifications allowed).

**Parameters:** None (just a signal)

**How it works:**

```
Phase 1: permission_mode="plan"
  Claude CAN: Read, Glob, Grep, TodoWrite
  Claude CANNOT: Write, Edit, Bash

  → Claude calls ExitPlanMode() when ready
  → Parent decides: approve or reject
  → If approved: run Phase 2 with permission_mode="bypassPermissions"
```

**When to use:**
- Preview-then-execute workflows
- Getting approval before modifications
- Safety-critical operations

**Configuration:**

```python
# Phase 1: Plan
options1 = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep", "ExitPlanMode"],
    permission_mode="plan",
)

# Phase 2: Execute (after approval)
options2 = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    permission_mode="bypassPermissions",
)
```

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "ExitPlanMode",
  "input": {}
}
```

**Cost/Performance:** Minimal. Just signals readiness.

---

## MCP Tools

### ToolSearch

Dynamically discovers and loads tool definitions from MCP servers. Enabled by default to save context window space — tool definitions are only loaded when needed.

**When to use:**
- You have many MCP tools (>20) and don't want them all in context
- Dynamic tool discovery at runtime

**Configuration:**

```python
# Disable tool search (load all tool definitions into context upfront)
options = ClaudeAgentOptions(extra_args={"--no-tool-search": None})
```

> **When to disable:** If you have few MCP tools (<20) and want Claude to always see them all without searching.

---

### ListMcpResources

List available "resources" from connected MCP servers (like browsing a virtual filesystem).

**Parameters:** None (or server name if multiple servers)

**MCP Resources vs Tools:**
- **Tools** = functions Claude can call
- **Resources** = data Claude can browse and read

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "ListMcpResources",
  "input": {}
}
```

**Returns:** List of available resources with URIs and descriptions.

**Cost/Performance:** Depends on MCP server. Usually ~50-100ms.

---

### ReadMcpResource

Read the full content of a specific MCP resource identified by URI.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uri` | `str` | Yes | Resource URI from `ListMcpResources` |

**Common pattern:**

```
Step 1: ListMcpResources()
  → Returns: ["db://tables/users", "db://tables/orders", ...]

Step 2: ReadMcpResource(uri="db://tables/users")
  → Returns: Full schema and sample data
```

**Claude call example:**

```json
{
  "type": "tool_use",
  "name": "ReadMcpResource",
  "input": {
    "uri": "db://tables/users"
  }
}
```

**Cost/Performance:** Proportional to resource size. ~1-5 seconds for large resources.

---

## Controlling Tool Availability

Three mechanisms control which tools the agent can use:

### 1. `tools` — Restrict Built-in Tools

Limits which built-in tools exist. Does NOT affect MCP tools.

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

### 3. `disallowed_tools` — Always Deny

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

### Permission Modes

| Mode | Behavior |
|------|----------|
| `"default"` | Requires `can_use_tool` callback or asks user interactively |
| `"acceptEdits"` | Auto-approve Read/Write/Edit; ask about Bash and destructive ops |
| `"plan"` | Allow Read/Glob/Grep only, block modifications |
| `"bypassPermissions"` | Auto-approve everything not in `disallowed_tools` |
| `"dontAsk"` | Only allow `allowed_tools`; deny everything else silently |

---

## Tool Search

Tool search is enabled by default. When many MCP tools are available, the SDK withholds their definitions from the context window and uses a search mechanism to load only relevant tools per turn.

```python
# Disable tool search (load all tool definitions into context)
options = ClaudeAgentOptions(extra_args={"--no-tool-search": None})
```

> **When to disable:** If you have few MCP tools (<20) and want Claude to always see them all.

---

## Decision Tree: Which Tool?

```
START
├─ Want to READ content?
│  ├─ File on disk? → Read
│  ├─ URL on web? → WebFetch (after WebSearch if needed)
│  └─ MCP resource? → ReadMcpResource (after ListMcpResources)
│
├─ Want to FIND files?
│  ├─ By name pattern? → Glob
│  ├─ By content (regex)? → Grep
│  └─ On web? → WebSearch
│
├─ Want to MODIFY code?
│  ├─ Complete rewrite or new file? → Write
│  ├─ Targeted fix (surgical edit)? → Edit
│  ├─ Notebook cells? → NotebookEdit
│  └─ Shell commands? → Bash
│
├─ Want to RUN something?
│  ├─ Shell command (short)? → Bash
│  ├─ Long task (background)? → Bash(run_in_background=true)
│  ├─ Check background progress? → BashOutput
│  └─ Stop background process? → KillBash
│
├─ Want to COORDINATE work?
│  ├─ Track progress? → TodoWrite
│  ├─ Parallel specialists? → Agent (with custom agents)
│  └─ Wait for human input? → AskUserQuestion (ClaudeSDKClient only)
│
├─ Want custom logic?
│  └─ → @tool() + create_sdk_mcp_server()
│
├─ Want to PLAN first?
│  └─ → permission_mode="plan" + ExitPlanMode
│
└─ Want STRUCTURED data from MCP?
   ├─ List available? → ListMcpResources
   └─ Read one? → ReadMcpResource
```

---

## Cost and Performance Reference

| Tool | Cost | Speed | Notes |
|------|------|-------|-------|
| Read | Low | Fast (1-2ms) | Token cost = file size |
| Glob | Minimal | Fast (10-50ms) | No token cost |
| Grep | Low | Medium (50-500ms) | Token cost = matched lines |
| Write | Low | Very fast (1-2ms) | Token cost = file content |
| Edit | Low | Very fast (1-5ms) | Token cost = change size |
| Bash | Medium-High | Varies | Token cost = execution output |
| NotebookEdit | Minimal | Fast (5-10ms) | No token cost |
| WebSearch | High | Slow (500ms+) | 50-100 tokens per result |
| WebFetch | Medium | Medium (1-2s) | Token cost = page content |
| TodoWrite | Minimal | Fast (instant) | 5-10 tokens per item |
| BashOutput | Minimal | Fast (10-50ms) | No token cost (reads buffer) |
| KillBash | Minimal | Fast (50-100ms) | No token cost |
| Agent | Very High | Slow (2-5s) | Full API call per subagent |
| AskUserQuestion | Zero | User wait time | Blocks execution |
| ExitPlanMode | Minimal | Instant | Just a signal |
| ListMcpResources | Medium | 50-100ms | Depends on MCP server |
| ReadMcpResource | Medium | 1-5s | Depends on resource size |

---

## Common Patterns

### Pattern 1: Glob + Read Combo

Find files, then read them.

```python
allowed_tools=["Glob", "Read"]

# Claude flow:
# 1. Glob(pattern="**/*.sql") → finds files
# 2. Read(file_path="...") → reads first file
# 3. Read(file_path="...") → reads second file
# 4. Analyzes all content
```

### Pattern 2: WebSearch + WebFetch Combo

Search for URLs, then read full content.

```python
allowed_tools=["WebSearch", "WebFetch"]

# Claude flow:
# 1. WebSearch(query="documentation") → finds URLs
# 2. WebFetch(url="...") → reads first page
# 3. WebFetch(url="...") → reads second page
# 4. Synthesizes information
```

### Pattern 3: Bash Background + BashOutput + KillBash

Start a long task, monitor, optionally stop.

```python
allowed_tools=["Bash", "BashOutput", "KillBash"]

# Claude flow:
# 1. Bash(command="long_task.py", run_in_background=true) → gets PID
# 2. BashOutput(pid=123) → checks progress
# 3. BashOutput(pid=123) → checks again
# 4. KillBash(pid=123) → stops if needed
```

### Pattern 4: Per-Phase Tool Restriction

Different tools for different phases.

```python
phase1_tools = ["Read", "Glob", "Grep"]       # Explore
phase2_tools = ["Read"]                        # Reference only
phase3_tools = []                              # Generate (no reads)
phase4_tools = ["Bash"]                        # Validate (run tests)

for phase, tools in [
    ("explore", phase1_tools),
    ("reference", phase2_tools),
    ("generate", phase3_tools),
    ("validate", phase4_tools),
]:
    options = ClaudeAgentOptions(
        allowed_tools=tools,
        permission_mode="bypassPermissions",
    )
    result = await invoke_claude(prompt=phase_prompt, options=options)
```

### Pattern 5: Subagent Divide-and-Conquer

Spawn specialized agents in parallel.

```python
options = ClaudeAgentOptions(
    allowed_tools=["Agent", "Read", "Glob", "Grep"],
    agents={
        "analyzer": AgentDefinition(
            description="Analyzes code quality",
            tools=["Read"],
            model="sonnet",
        ),
        "reviewer": AgentDefinition(
            description="Reviews security",
            tools=["Read", "Grep"],
            model="haiku",  # cheaper for simpler scans
        ),
    },
)

# Claude calls both in parallel:
# Agent(subagent_type="analyzer", prompt="analyze src/")
# Agent(subagent_type="reviewer", prompt="scan for secrets in src/")
# Results merge back to parent
```

### Pattern 6: Read-Only Agent (No Write/Execute)

```python
options = ClaudeAgentOptions(
    tools=["Read", "Glob", "Grep", "WebSearch", "WebFetch"],
    disallowed_tools=["Write", "Edit", "Bash", "NotebookEdit"],
)
```

### Pattern 7: Code-Writing Agent (No Web, No Bash)

```python
options = ClaudeAgentOptions(
    tools=["Read", "Write", "Edit", "Glob", "Grep"],
    disallowed_tools=["Bash", "WebSearch", "WebFetch"],
)
```

### Pattern 8: MCP-Only Agent

```python
options = ClaudeAgentOptions(
    tools=[],  # No built-in tools
    mcp_servers={"myserver": server_config},
    allowed_tools=["mcp__myserver__*"],
)
```

### Pattern 9: Selective Tool Approval

```python
options = ClaudeAgentOptions(
    permission_mode="default",
    allowed_tools=[
        "Read", "Glob", "Grep",         # Auto-approve read ops
        "mcp__github__get_issue",        # Auto-approve specific MCP tools
    ],
    # Write, Edit, Bash still require permission prompt
)
```

---

## Best Practices

1. **Restrict tools by phase** — Different operations need different permissions
2. **Use `disallowed_tools` for safety** — Block Bash in user-facing apps
3. **Combine Read + Edit/Write** — Read first, then modify (Edit requires exact match)
4. **Use WebSearch → WebFetch** — Don't fetch URLs without finding them first
5. **Package related custom tools** — One MCP server per domain (validators, calculators, etc.)
6. **Consider costs** — WebSearch is expensive; use Read for local docs
7. **Plan before executing** — Use `permission_mode="plan"` for safety-critical operations
8. **Monitor background tasks** — Don't fire-and-forget Bash background processes
9. **Use TodoWrite for visibility** — Especially for multi-step tasks
10. **Prefer specific tools over broad permissions** — Better control = safer execution

---

## Related Topics

- [Custom Tools](03-custom-tools.md) — Define your own tools
- [MCP Integration](04-mcp-integration.md) — Connect external MCP servers
- [Permissions](06-permissions.md) — Permission modes and evaluation
- [Subagents](08-subagents.md) — Spawning and configuring subagents
- [User Input](12-user-input.md) — AskUserQuestion and approval flows
