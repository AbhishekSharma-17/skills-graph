# Claude Agent SDK — User Input & Approval Flows

> Source: [platform.claude.com/docs/en/agent-sdk/user-input](https://platform.claude.com/docs/en/agent-sdk/user-input) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Two Types of User Input](#two-types-of-user-input)
- [Tool Approval (canUseTool)](#tool-approval-canusetool)
- [AskUserQuestion Tool](#askuserquestion-tool)
- [Question Structure](#question-structure)
- [Processing Responses](#processing-responses)
- [Option Previews (TypeScript)](#option-previews-typescript)
- [Free Text Input](#free-text-input)
- [Python canUseTool Deep Dive](#python-canusetool-deep-dive)
- [TypeScript canUseTool Deep Dive](#typescript-canusetool-deep-dive)
- [Modifying Tool Input via Approval](#modifying-tool-input-via-approval)
- [Limitations](#limitations)
- [Common Patterns](#common-patterns)

## Two Types of User Input

The SDK surfaces two kinds of requests for human input:

| Type | Trigger | Purpose |
|------|---------|---------|
| **Tool Approval** | Agent wants to use a tool not pre-approved | User allows or denies the tool call |
| **AskUserQuestion** | Agent needs clarification or choices | User answers questions with options |

Both are handled via the `canUseTool` callback. When the callback receives a tool call, it can distinguish between approval requests and questions by checking the tool name.

## Tool Approval (canUseTool)

The `canUseTool` callback fires when a tool isn't auto-approved by `allowed_tools` or permission mode.

### Python

```python
from claude_agent_sdk import ClaudeAgentOptions

async def handle_permission(
    tool_name: str,
    input_data: dict,
    context,
) -> dict:
    if tool_name in ("Read", "Glob", "Grep"):
        return {"type": "allow"}

    if tool_name == "Bash":
        command = input_data.get("command", "")
        print(f"Agent wants to run: {command}")
        approved = await prompt_user(f"Allow Bash: {command}?")
        if approved:
            return {"type": "allow"}
        return {"type": "deny", "message": "User denied Bash command"}

    if tool_name == "Edit":
        file_path = input_data.get("file_path", "")
        print(f"Agent wants to edit: {file_path}")
        return {"type": "allow"}

    return {"type": "deny", "message": f"Unknown tool: {tool_name}"}

options = ClaudeAgentOptions(
    can_use_tool=handle_permission,
    # Required workaround: need at least one PreToolUse hook for can_use_tool to work
    hooks={"PreToolUse": [{"matcher": None, "hooks": [lambda *a: {}]}]},
)
```

### TypeScript

```typescript
const q = query({
  prompt: "...",
  options: {
    canUseTool: async (toolName, input, context) => {
      if (["Read", "Glob", "Grep"].includes(toolName)) {
        return { type: "allow" };
      }

      if (toolName === "Bash") {
        const approved = await promptUser(`Allow: ${input.command}?`);
        return approved
          ? { type: "allow" }
          : { type: "deny", message: "User denied" };
      }

      return { type: "deny", message: `Unknown tool: ${toolName}` };
    },
  },
});
```

## AskUserQuestion Tool

When Claude needs clarification, it uses the `AskUserQuestion` tool. This surfaces as a permission request in `canUseTool`:

```python
async def handle_permission(tool_name, input_data, context):
    if tool_name == "AskUserQuestion":
        questions = input_data.get("questions", [])
        answers = {}

        for q in questions:
            question_text = q.get("question", "")
            options = q.get("options", [])
            print(f"\n{question_text}")
            for i, opt in enumerate(options):
                print(f"  {i+1}. {opt['label']} — {opt.get('description', '')}")
            print(f"  {len(options)+1}. Other (custom text)")

            choice = await get_user_choice(len(options) + 1)
            if choice <= len(options):
                answers[question_text] = options[choice - 1]["label"]
            else:
                custom = await get_user_text()
                answers[question_text] = custom

        return {
            "type": "allow",
            "updated_input": {**input_data, "answers": answers},
        }

    # Handle other tools...
    return {"type": "allow"}
```

## Question Structure

The `AskUserQuestion` tool input follows this structure:

```python
{
    "questions": [
        {
            "question": "Which database should we use?",  # Full question text
            "header": "Database",                           # Short label (max 12 chars)
            "options": [
                {
                    "label": "PostgreSQL",                  # Display text (1-5 words)
                    "description": "Relational, mature, best for complex queries",
                    "preview": "```sql\nCREATE TABLE...\n```",  # Optional preview content
                },
                {
                    "label": "MongoDB",
                    "description": "Document store, flexible schema",
                },
                {
                    "label": "SQLite",
                    "description": "Embedded, zero config, great for local dev",
                },
            ],
            "multiSelect": False,  # True allows multiple selections
        }
    ]
}
```

### Constraints

| Field | Constraint |
|-------|-----------|
| `questions` | 1-4 questions per call |
| `options` | 2-4 options per question |
| `header` | Max 12 characters |
| `label` | 1-5 words, concise |
| `multiSelect` | `True` allows selecting multiple options |

## Processing Responses

The response comes back via `updated_input` with an `answers` dict:

```python
# Response format
{
    "answers": {
        "Which database should we use?": "PostgreSQL",
        "Which features do you need?": "Authentication, API routes",  # Multi-select joined
    }
}
```

### Multi-Select Responses

When `multiSelect: True`, the user can select multiple options. The response joins selected labels:

```python
# Multi-select question
{
    "question": "Which features do you need?",
    "multiSelect": True,
    "options": [
        {"label": "Authentication", "description": "User login/signup"},
        {"label": "API routes", "description": "REST endpoints"},
        {"label": "Database", "description": "Data persistence"},
    ]
}

# Response: answers["Which features do you need?"] = "Authentication, API routes"
```

## Option Previews (TypeScript)

TypeScript supports rich previews for options. Configure the preview format:

```typescript
const q = query({
  prompt: "...",
  options: {
    toolConfig: {
      askUserQuestion: {
        previewFormat: "markdown",  // or "html"
      },
    },
  },
});
```

When `previewFormat` is set, option `preview` fields are rendered as markdown or HTML when the user hovers/focuses on an option.

## Free Text Input

Users can always provide custom text input ("Other" option). When custom text is entered, it becomes the answer value:

```python
async def handle_ask(tool_name, input_data, context):
    if tool_name == "AskUserQuestion":
        questions = input_data.get("questions", [])
        answers = {}

        for q in questions:
            options = q.get("options", [])
            # Show options + "Other"
            choice = await display_options_with_other(q["question"], options)

            if choice == "other":
                custom_text = await get_free_text()
                answers[q["question"]] = custom_text
            else:
                answers[q["question"]] = choice

        return {"type": "allow", "updated_input": {**input_data, "answers": answers}}
```

## Python canUseTool Deep Dive

### Callback Signature

```python
async def can_use_tool(
    tool_name: str,        # Name of the tool (e.g., "Bash", "mcp__github__create_issue")
    input_data: dict,      # Tool input arguments
    context: ToolPermissionContext,  # Additional context
) -> PermissionResultAllow | PermissionResultDeny
```

### Return Types

```python
# Allow (no modifications)
{"type": "allow"}

# Allow with modified input
{"type": "allow", "updated_input": {"command": "git status"}}

# Deny with reason
{"type": "deny", "message": "Not allowed in this context"}
```

### Required Setup (Python Gotcha)

In Python, `can_use_tool` only works in streaming mode with at least one `PreToolUse` hook registered:

```python
options = ClaudeAgentOptions(
    can_use_tool=my_handler,
    # This no-op hook is REQUIRED for can_use_tool to fire
    hooks={"PreToolUse": [{"matcher": None, "hooks": [lambda *a: {}]}]},
)
```

## TypeScript canUseTool Deep Dive

### Callback Signature

```typescript
canUseTool: async (
  toolName: string,
  input: Record<string, any>,
  context: { signal: AbortSignal },
) => Promise<{ type: "allow"; updatedInput?: any } | { type: "deny"; message: string }>
```

### With dontAsk Mode

In `dontAsk` mode, `canUseTool` is NOT called — tools not in `allowedTools` are automatically denied:

```typescript
const q = query({
  prompt: "...",
  options: {
    permissionMode: "dontAsk",
    allowedTools: ["Read", "Glob"],
    // canUseTool is NEVER called in dontAsk mode
  },
});
```

## Modifying Tool Input via Approval

You can modify tool inputs during the approval process:

```python
async def sanitize_on_approve(tool_name, input_data, context):
    if tool_name == "Bash":
        command = input_data.get("command", "")
        # Add safety timeout to all commands
        safe_command = f"timeout 30 {command}"
        return {
            "type": "allow",
            "updated_input": {**input_data, "command": safe_command},
        }
    return {"type": "allow"}
```

```typescript
const q = query({
  prompt: "...",
  options: {
    canUseTool: async (toolName, input) => {
      if (toolName === "Bash") {
        return {
          type: "allow",
          updatedInput: { ...input, command: `timeout 30 ${input.command}` },
        };
      }
      return { type: "allow" };
    },
  },
});
```

## Limitations

1. **Not available in subagents** — subagents cannot use `AskUserQuestion`; include all needed context in the subagent prompt
2. **1-4 questions per call** — Claude can only ask 1-4 questions at a time
3. **2-4 options per question** — each question must have 2-4 predefined options (plus implicit "Other")
4. **Python requires dummy hook** — `can_use_tool` needs at least one `PreToolUse` hook registered
5. **`dontAsk` mode skips canUseTool** — in TypeScript's `dontAsk` mode, the callback is never called
6. **Option previews TypeScript-only** — `previewFormat` is not available in Python
7. **Header max 12 chars** — the `header` field is displayed as a chip/tag and must be very short

## Common Patterns

### Tiered Approval

```python
async def tiered_approval(tool_name, input_data, context):
    # Tier 1: Auto-approve safe tools
    safe_tools = {"Read", "Glob", "Grep", "WebSearch"}
    if tool_name in safe_tools:
        return {"type": "allow"}

    # Tier 2: Approve with logging
    logged_tools = {"Edit", "Write"}
    if tool_name in logged_tools:
        log_tool_use(tool_name, input_data)
        return {"type": "allow"}

    # Tier 3: Require explicit approval
    return await prompt_for_approval(tool_name, input_data)
```

### Question-Based Workflow

```python
# Claude will use AskUserQuestion when it needs decisions:
# "Which testing framework?" → pytest / jest / vitest
# "What auth method?" → JWT / OAuth2 / API keys
# The canUseTool callback routes these to your UI
```

## Related Topics

- [Permissions](06-permissions.md) — Permission modes and evaluation order
- [Hooks](05-hooks.md) — PreToolUse hooks for permission decisions
- [Configuration](01-configuration.md) — canUseTool in options
