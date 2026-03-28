# Claude Agent SDK — Deployment

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [System Requirements](#system-requirements)
- [Deployment Patterns](#deployment-patterns)
- [Sandbox Providers](#sandbox-providers)
- [Cost Tracking](#cost-tracking)
- [Security Hardening](#security-hardening)
- [File Checkpointing](#file-checkpointing)
- [Claude Code Features in SDK](#claude-code-features-in-sdk)
- [Scaling Considerations](#scaling-considerations)
- [Monitoring](#monitoring)
- [Common Pitfalls](#common-pitfalls)

## System Requirements

Per SDK instance (one running agent):

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 1 GiB | 2 GiB |
| Disk | 5 GiB | 10 GiB |
| CPU | 1 core | 2 cores |
| Node.js | 18+ | 20+ (LTS) |
| Python | 3.10+ | 3.12+ |

The SDK bundles the Claude Code CLI binary — no separate installation needed. Platform-specific wheels are provided for macOS (arm64, x86-64), Linux (x86-64, aarch64), and Windows (x86-64).

## Deployment Patterns

### Ephemeral Sessions

Create a new container/VM per task, destroy when done.

```
Request → Spin up container → Run agent → Return result → Destroy container
```

**Best for:** CI/CD pipelines, one-shot tasks, untrusted code execution.

```python
# Ephemeral: no session persistence needed
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    max_turns=50,
    max_budget_usd=2.00,
    cwd="/workspace",
    setting_sources=[],  # Clean environment
)
```

### Long-Running Sessions

Persistent containers that handle multiple requests over time.

```
Container starts → Agent runs → Idles → Agent runs again → ...
```

**Best for:** Interactive assistants, development environments, multi-turn workflows.

```python
client = ClaudeSDKClient(options)
async with client:
    await client.connect()
    # Handle multiple queries over time
    while True:
        user_input = await get_next_request()
        await client.query(user_input)
        async for msg in client.receive_response():
            await send_to_user(msg)
```

### Hybrid Sessions

Ephemeral containers hydrated with session history from a previous run.

```
Load session → Spin up container → Resume agent → Return result → Destroy container
```

```python
options = ClaudeAgentOptions(
    resume="previous-session-id",
    cwd="/workspace",  # Must match original session's cwd
)
```

### Multiple Agents Per Container

Run several SDK processes in a single container for resource efficiency.

```python
import asyncio

async def run_agent(task: str, task_id: str):
    options = ClaudeAgentOptions(
        max_turns=20,
        max_budget_usd=0.50,
        cwd=f"/workspace/{task_id}",
    )
    async for msg in query(prompt=task, options=options):
        yield msg

# Run multiple agents concurrently
tasks = [
    run_agent("Fix bug in auth.py", "task-1"),
    run_agent("Add tests for utils.py", "task-2"),
    run_agent("Update README.md", "task-3"),
]
# Process results as they come
```

> **Resource note:** Each agent process needs ~1 GiB RAM. Size containers accordingly.

## Sandbox Providers

The SDK can run agents in sandboxed environments for security:

| Provider | Type | Best For |
|----------|------|----------|
| **Modal** | Serverless containers | Scalable, pay-per-second |
| **E2B** | Cloud sandboxes | Quick spin-up, AI-focused |
| **Cloudflare** | Edge containers | Low latency, global |
| **Daytona** | Dev environments | Full IDE-like environments |
| **Fly Machines** | Micro VMs | Fast boot, persistent storage |
| **Vercel Sandbox** | Serverless | Web app integration |

### Custom Process Spawning (TypeScript)

For advanced sandboxing, use `spawnClaudeCodeProcess` to run agents in custom environments:

```typescript
const q = query({
  prompt: "...",
  options: {
    spawnClaudeCodeProcess: async ({ args, env, cwd }) => {
      // Launch agent in a VM, container, or remote server
      const container = await createContainer({
        image: "node:20",
        cmd: ["claude-agent", ...args],
        env,
        workdir: cwd,
      });
      return {
        stdout: container.stdout,
        stderr: container.stderr,
        stdin: container.stdin,
        kill: () => container.stop(),
        exitCode: container.exitCode,
      };
    },
  },
});
```

## Cost Tracking

### Budget Limits

```python
options = ClaudeAgentOptions(
    max_budget_usd=1.00,  # Hard cap per query
    max_turns=30,          # Limit iterations
)
```

### Reading Cost from Results

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "result":
        print(f"Cost: ${msg.total_cost_usd:.4f}")
        print(f"Duration: {msg.duration_ms}ms")
        print(f"Input tokens: {msg.usage.get('input_tokens', 0)}")
        print(f"Output tokens: {msg.usage.get('output_tokens', 0)}")
```

### Cost Estimation

| Component | Approximate Cost |
|-----------|-----------------|
| Container runtime | ~$0.05/hour minimum |
| Claude API tokens | Varies by model and usage |
| Typical simple task | $0.02-0.10 |
| Complex multi-turn task | $0.50-5.00 |

> Token cost dominates — container cost is negligible for most workloads.

## Security Hardening

### Principle of Least Privilege

```python
options = ClaudeAgentOptions(
    permission_mode="default",
    tools=["Read", "Glob", "Grep", "Edit"],      # Only needed tools
    disallowed_tools=["Bash", "WebFetch"],          # Block risky tools
    max_turns=20,
    max_budget_usd=0.50,
    cwd="/sandboxed/workspace",                     # Restricted directory
    setting_sources=[],                              # No filesystem settings
)
```

### Network Isolation

```python
# Block all web tools for offline-only agents
options = ClaudeAgentOptions(
    disallowed_tools=["WebSearch", "WebFetch"],
    env={"HTTP_PROXY": "", "HTTPS_PROXY": ""},  # No network
)
```

### Input Validation with Hooks

```python
async def validate_bash(input_data, tool_use_id, context):
    command = input_data.get("command", "")
    blocked = ["rm -rf /", "sudo", "curl | sh", "wget | sh", "chmod 777"]
    for pattern in blocked:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked: {pattern}",
                }
            }
    return {}
```

### Secrets Management

```python
# Pass secrets via env, not in prompts
options = ClaudeAgentOptions(
    env={
        "DATABASE_URL": os.environ["DATABASE_URL"],
        "API_KEY": os.environ["API_KEY"],
    },
)
# Never include secrets in the prompt string
```

## File Checkpointing

Track and revert file changes made by the agent:

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True,
)

async for msg in query(prompt="Refactor the auth module", options=options):
    if msg.type == "result":
        # If unhappy with changes, revert
        # Use rewind_files() with the user_message_id to restore
        pass
```

### Rewind Changes

```python
# ClaudeSDKClient pattern
client = ClaudeSDKClient(options)
async with client:
    await client.connect(prompt="Make changes to auth.py")
    async for msg in client.receive_messages():
        if msg.type == "assistant":
            user_msg_id = msg.id  # Track message IDs

    # Revert all file changes after a specific message
    await client.rewind_files(user_message_id=user_msg_id)
```

## Claude Code Features in SDK

The SDK provides access to Claude Code features when `setting_sources` includes project settings:

| Feature | Description | Requires |
|---------|-------------|----------|
| **Skills** | Specialized capabilities in Markdown | `setting_sources=["project"]` |
| **CLAUDE.md** | Project-level instructions | `setting_sources=["project"]` |
| **Memory** | Persistent context | `setting_sources=["user", "project"]` |
| **Plugins** | Custom commands and agents | `plugins=[...]` |

```python
# Enable Claude Code features
options = ClaudeAgentOptions(
    setting_sources=["user", "project", "local"],
    # Now CLAUDE.md, skills, and hooks from settings files are loaded
)
```

## Scaling Considerations

### Horizontal Scaling

- Each agent runs independently — scale by adding more containers
- No shared state between agents (sessions are local)
- Use a task queue (Redis, SQS) to distribute work

### Rate Limits

- Anthropic API has rate limits per organization
- Multiple concurrent agents share the rate limit
- Implement backoff and retry logic for rate limit errors

### Session Storage

- Sessions are stored locally as JSONL files
- For multi-container deployments, use shared storage (NFS, EBS) if session resumption is needed
- Or use ephemeral sessions and reconstruct context from external sources

## Monitoring

### Logging

```python
options = ClaudeAgentOptions(
    stderr=lambda line: logger.debug(f"[claude-agent] {line}"),
)
```

### Metrics to Track

| Metric | Source | Purpose |
|--------|--------|---------|
| `total_cost_usd` | ResultMessage | Cost per task |
| `duration_ms` | ResultMessage | Latency |
| `usage.input_tokens` | ResultMessage | Token consumption |
| `usage.output_tokens` | ResultMessage | Token consumption |
| `subtype` | ResultMessage | Success/error rate |
| Tool call counts | Hooks (PostToolUse) | Tool usage patterns |

### Health Checks

```python
async def health_check():
    try:
        async for msg in query(prompt="Say hello", options=ClaudeAgentOptions(max_turns=1)):
            if msg.type == "result":
                return msg.subtype == "success"
    except Exception:
        return False
```

## Common Pitfalls

1. **Forgetting `max_budget_usd`** — without a budget cap, a misbehaving agent can rack up significant costs
2. **`bypassPermissions` in production** — only use in sandboxed environments; prefer `acceptEdits` + `allowed_tools` otherwise
3. **Ignoring `setting_sources`** — defaults to `[]`, so CLAUDE.md and skills won't load unless explicitly enabled
4. **Session `cwd` mismatch** — resuming a session with a different working directory fails silently or behaves unexpectedly
5. **Container sizing** — each agent needs ~1 GiB RAM; under-provisioned containers cause OOM kills
6. **Rate limit exhaustion** — multiple concurrent agents share your organization's API rate limit
7. **No persistent storage in ephemeral containers** — sessions are lost when the container is destroyed; use `persistSession: false` (TypeScript) or don't rely on resumption

## Related Topics

- [Configuration](01-configuration.md) — Full options reference
- [Permissions](06-permissions.md) — Security configuration
- [Sessions](07-sessions.md) — Session management and resumption
