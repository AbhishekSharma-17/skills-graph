# Claude Agent SDK — Agent Loop, Errors & Cost Tracking

> Source: [platform.claude.com/docs/en/agent-sdk/agent-loop](https://platform.claude.com/docs/en/agent-sdk/agent-loop), [cost-tracking](https://platform.claude.com/docs/en/agent-sdk/cost-tracking) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [How the Agent Loop Works](#how-the-agent-loop-works)
- [Turns and Max Turns](#turns-and-max-turns)
- [Parallel Tool Execution](#parallel-tool-execution)
- [Context Window and Compaction](#context-window-and-compaction)
- [Stop Reasons](#stop-reasons)
- [Result Subtypes](#result-subtypes)
- [Error Types](#error-types)
- [AssistantMessage Errors](#assistantmessage-errors)
- [Rate Limiting](#rate-limiting)
- [Cost Tracking](#cost-tracking)
- [Per-Step Usage](#per-step-usage)
- [Cache Tokens](#cache-tokens)
- [Model Usage Breakdown (TypeScript)](#model-usage-breakdown-typescript)
- [Cost Tracking Patterns](#cost-tracking-patterns)

## How the Agent Loop Works

The agent loop is the core execution cycle. Unlike stateless API calls, it runs as a long-running process:

```
1. Receive prompt
   └→ Yields SystemMessage (subtype: "init")
       Contains: session_id, mcp_servers status, slash_commands

2. Claude evaluates and responds
   └→ Yields AssistantMessage
       Contains: text blocks, tool_use blocks, thinking blocks

3. SDK executes requested tools
   └→ Tool results collected (parallel for read-only, sequential for writes)

4. Results feed back to Claude
   └→ Claude sees tool results and decides next action

5. Repeat steps 2-4 until:
   - No more tool calls (agent is done)
   - max_turns reached
   - max_budget_usd exceeded
   - Error occurs

6. Final result
   └→ Yields ResultMessage
       Contains: subtype, duration_ms, total_cost_usd, usage, session_id
```

## Turns and Max Turns

A **turn** is one round trip: Claude outputs (possibly with tool calls) → tools execute → results return.

```python
# Limit turns to prevent runaway agents
options = ClaudeAgentOptions(max_turns=30)
```

When `max_turns` is reached, the agent stops and returns a `ResultMessage` with `subtype: "error_max_turns"`.

> **Default:** No limit (TypeScript) or no limit (Python). Always set `max_turns` in production.

### Effort Levels and Turn Behavior

| Effort | Behavior |
|--------|----------|
| `"low"` | Quick responses, minimal tool usage |
| `"medium"` | Balanced |
| `"high"` | Thorough analysis (TypeScript default) |
| `"max"` | Maximum effort, comprehensive |

```python
options = ClaudeAgentOptions(effort="high")
```

> **Note:** TypeScript defaults to `"high"` effort; Python leaves it unset (uses server default).

## Parallel Tool Execution

The SDK executes tools in parallel when safe:

| Tool Category | Execution | Reason |
|--------------|-----------|--------|
| **Read-only** (Read, Glob, Grep, WebSearch) | Concurrent | No side effects |
| **State-modifying** (Write, Edit, Bash) | Sequential | Order matters |
| **Mixed** | Read-only parallel first, then writes sequential | Safety |

```
Claude requests: [Read("a.py"), Read("b.py"), Edit("c.py"), Read("d.py")]

Execution:
  ├── Read("a.py")  ─┐
  ├── Read("b.py")   ├── Parallel (all read-only)
  ├── Read("d.py")  ─┘
  └── Edit("c.py")  ──── Sequential (after reads complete)
```

## Context Window and Compaction

The agent accumulates context across turns. When the context window approaches its limit, the SDK automatically compacts older history:

1. **Before compaction:** Emits `SystemMessage` with `subtype: "compact_boundary"`
2. **During compaction:** Summarizes older messages, preserving key information
3. **After compaction:** Agent continues with summarized history

### Customizing Compaction

```python
# Via CLAUDE.md (loaded when settingSources includes "project")
# Add instructions about what to preserve during compaction

# Via PreCompact hook
async def before_compact(input_data, tool_use_id, context):
    return {
        "systemMessage": "IMPORTANT: Preserve all database schema details during compaction.",
    }

options = ClaudeAgentOptions(
    hooks={"PreCompact": [{"matcher": None, "hooks": [before_compact]}]},
)
```

> **Best practice:** Put persistent instructions in `system_prompt` or CLAUDE.md files, not in the initial prompt. The initial prompt may be summarized during compaction.

## Stop Reasons

The `stop_reason` field on `AssistantMessage` indicates why Claude stopped generating:

| stop_reason | Meaning |
|-------------|---------|
| `end_turn` | Claude chose to stop (normal completion) |
| `max_tokens` | Hit output token limit |
| `refusal` | Claude refused the request |

## Result Subtypes

The `subtype` field on `ResultMessage` indicates the overall outcome:

| Subtype | Meaning | Action |
|---------|---------|--------|
| `success` | Agent completed normally | Process results |
| `error_max_turns` | Hit `max_turns` limit | Increase limit or resume session |
| `error_max_budget_usd` | Hit `max_budget_usd` limit | Increase budget or break into smaller tasks |
| `error_during_execution` | Tool execution error | Check error details, retry |
| `error_max_structured_output_retries` | Structured output validation failed | Simplify schema or increase retries |

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "result":
        match msg.subtype:
            case "success":
                print("Completed successfully")
            case "error_max_turns":
                print(f"Ran out of turns. Resume with: {msg.session_id}")
            case "error_max_budget_usd":
                print(f"Budget exceeded: ${msg.total_cost_usd:.2f}")
            case "error_during_execution":
                print("Execution error occurred")
            case "error_max_structured_output_retries":
                print("Could not produce valid structured output")
```

## Error Types

The SDK defines an error hierarchy:

### Python

```python
from claude_agent_sdk import ClaudeSDKError

# Base error
class ClaudeSDKError(Exception): ...

# CLI binary not found
class CLINotFoundError(CLIConnectionError): ...

# Connection to CLI process failed
class CLIConnectionError(ClaudeSDKError): ...

# CLI process exited with error
class ProcessError(ClaudeSDKError):
    exit_code: int
    stderr: str

# Invalid JSON from CLI
class CLIJSONDecodeError(ClaudeSDKError):
    line: str
    original_error: Exception
```

### Handling Errors

```python
from claude_agent_sdk import ClaudeSDKError, ProcessError, CLINotFoundError

try:
    async for msg in query(prompt="...", options=options):
        ...
except CLINotFoundError:
    print("Claude CLI binary not found. Install claude-agent-sdk.")
except ProcessError as e:
    print(f"Process exited with code {e.exit_code}: {e.stderr}")
except ClaudeSDKError as e:
    print(f"SDK error: {e}")
```

## AssistantMessage Errors

`AssistantMessage` can contain error information when Claude encounters issues:

| Error Value | Cause |
|-------------|-------|
| `authentication_failed` | Invalid API key or auth failure |
| `billing_error` | Billing/payment issue |
| `rate_limit` | API rate limit exceeded |
| `invalid_request` | Malformed request |
| `server_error` | Anthropic server error |
| `max_output_tokens` | Output too long |
| `unknown` | Unclassified error |

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "assistant" and hasattr(msg, "error"):
        if msg.error == "rate_limit":
            print("Rate limited — waiting...")
        elif msg.error == "authentication_failed":
            print("Check your API key")
```

## Rate Limiting

The SDK handles rate limits with `RateLimitEvent` messages:

### Rate Limit Status

| Status | Meaning |
|--------|---------|
| `allowed` | Request processed normally |
| `allowed_warning` | Processed but approaching limit |
| `rejected` | Request rejected — must wait |

### Rate Limit Types

| Type | Window |
|------|--------|
| `five_hour` | 5-hour rolling window |
| `seven_day` | 7-day rolling window |
| `seven_day_opus` | 7-day Opus-specific limit |
| `seven_day_sonnet` | 7-day Sonnet-specific limit |
| `overage` | Billing overage limit |

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "rate_limit":
        print(f"Rate limit: {msg.status} ({msg.limit_type})")
        if msg.status == "rejected":
            print(f"Retry after: {msg.retry_after_ms}ms")
```

## Cost Tracking

### Query-Level Cost

The authoritative cost is on the `ResultMessage`:

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "result":
        print(f"Total cost: ${msg.total_cost_usd:.4f}")
        print(f"Duration: {msg.duration_ms}ms")
        print(f"Input tokens: {msg.usage.get('input_tokens', 0)}")
        print(f"Output tokens: {msg.usage.get('output_tokens', 0)}")
```

### Budget Limits

```python
options = ClaudeAgentOptions(
    max_budget_usd=1.00,  # Hard cap — agent stops when reached
)
```

> Both success and error results include `total_cost_usd` — you can always see what was spent.

## Per-Step Usage

### TypeScript (Per-Step Available)

TypeScript exposes per-step usage on `AssistantMessage`:

```typescript
for await (const msg of q) {
  if (msg.type === "assistant" && msg.message?.usage) {
    console.log(`Step tokens: ${msg.message.usage.input_tokens} in, ${msg.message.usage.output_tokens} out`);
  }
}
```

### Python (Result-Level Only)

Python provides usage only on the final `ResultMessage`. Use hooks for per-tool tracking:

```python
async def track_usage(input_data, tool_use_id, context):
    # Log each tool call for cost attribution
    tool_name = input_data.get("tool_name", "unknown")
    log_tool_invocation(tool_name, tool_use_id)
    return {}

options = ClaudeAgentOptions(
    hooks={"PostToolUse": [{"matcher": None, "hooks": [track_usage]}]},
)
```

## Cache Tokens

The SDK uses prompt caching to reduce costs. Cache-related fields in usage:

| Field | Description |
|-------|-------------|
| `cache_creation_input_tokens` | Tokens used to create new cache entries |
| `cache_read_input_tokens` | Tokens read from cache (cheaper) |

Cache reads are significantly cheaper than non-cached input tokens. Long-running sessions benefit from caching as system prompts and early context get cached.

## Model Usage Breakdown (TypeScript)

TypeScript provides per-model cost breakdown when multiple models are used (e.g., via subagents):

```typescript
for await (const msg of q) {
  if (msg.type === "result" && msg.modelUsage) {
    for (const [model, usage] of Object.entries(msg.modelUsage)) {
      console.log(`${model}: $${usage.cost_usd.toFixed(4)}`);
    }
  }
}
```

> **Parallel tool call deduplication:** When Claude requests parallel tool calls, they share the same message ID. Deduplicate by ID to avoid double-counting usage.

## Cost Tracking Patterns

### Budget Guard with Hooks

```python
spent = 0.0
BUDGET = 5.00

async def budget_check(input_data, tool_use_id, context):
    global spent
    if spent > BUDGET:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Budget exceeded: ${spent:.2f}/{BUDGET}",
            }
        }
    return {}
```

### Cost Logging

```python
import json

async for msg in query(prompt="...", options=options):
    if msg.type == "result":
        cost_log = {
            "session_id": msg.session_id,
            "cost_usd": msg.total_cost_usd,
            "duration_ms": msg.duration_ms,
            "input_tokens": msg.usage.get("input_tokens", 0),
            "output_tokens": msg.usage.get("output_tokens", 0),
            "subtype": msg.subtype,
        }
        with open("costs.jsonl", "a") as f:
            f.write(json.dumps(cost_log) + "\n")
```

## Related Topics

- [Overview](00-overview.md) — Basic message types and iteration
- [Configuration](01-configuration.md) — max_turns, max_budget_usd, effort
- [Streaming](11-streaming.md) — StreamEvent and real-time output
- [Deployment](10-deployment.md) — Production cost management
