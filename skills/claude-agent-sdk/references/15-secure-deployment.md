# Claude Agent SDK — Secure Deployment

> Source: [platform.claude.com/docs/en/agent-sdk/secure-deployment](https://platform.claude.com/docs/en/agent-sdk/secure-deployment) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Threat Model](#threat-model)
- [Built-in Security](#built-in-security)
- [Security Principles](#security-principles)
- [Isolation Technologies](#isolation-technologies)
- [Docker Hardening](#docker-hardening)
- [Credential Management](#credential-management)
- [Proxy Patterns](#proxy-patterns)
- [Filesystem Controls](#filesystem-controls)
- [Credential Files to Exclude](#credential-files-to-exclude)
- [Network Isolation](#network-isolation)
- [File Checkpointing for Safety](#file-checkpointing-for-safety)
- [Production Checklist](#production-checklist)

## Threat Model

Two primary threats when deploying agents:

| Threat | Description | Mitigation |
|--------|-------------|-----------|
| **Prompt Injection** | Malicious content in files/web pages tricks the agent into unintended actions | Permission system, sandboxing, input validation hooks |
| **Model Error** | Claude makes a mistake (wrong file edit, dangerous command) | Permission prompts, sandboxing, file checkpointing |

Both threats can result in: data exfiltration, credential theft, filesystem corruption, unauthorized API calls, or code execution.

## Built-in Security

The SDK provides multiple layers of security by default:

| Layer | Protection |
|-------|-----------|
| **Permission system** | Tools require explicit approval unless pre-approved |
| **Static analysis** | Bash commands analyzed before execution |
| **Web summarization** | WebFetch summarizes content (doesn't execute scripts) |
| **Sandbox mode** | Optional sandboxed execution environment |
| **Tool restrictions** | `tools`, `allowedTools`, `disallowedTools` control access |

## Security Principles

### 1. Security Boundaries

Isolate the agent from the host system. The agent should not have access to:
- Host filesystem beyond the working directory
- Host network beyond required services
- Host credentials and secrets
- Other containers or processes

### 2. Principle of Least Privilege

Give the agent only what it needs:

```python
# Good: Minimal permissions
options = ClaudeAgentOptions(
    tools=["Read", "Edit", "Glob", "Grep"],        # Only needed tools
    disallowed_tools=["Bash", "WebSearch", "WebFetch"],  # Block risky tools
    cwd="/sandboxed/workspace",                      # Restricted directory
    setting_sources=[],                               # No filesystem settings
    max_turns=30,
    max_budget_usd=1.00,
)
```

### 3. Defense in Depth

Layer multiple security controls:

```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",                    # Layer 1: mode
    disallowed_tools=["mcp__*__delete_*"],            # Layer 2: blocklist
    hooks={"PreToolUse": [{"matcher": "Bash", "hooks": [bash_guard]}]},  # Layer 3: hooks
    can_use_tool=permission_callback,                  # Layer 4: callback
    max_turns=30,                                      # Layer 5: limits
    max_budget_usd=1.00,
)
```

## Isolation Technologies

| Technology | Isolation Level | Overhead | Best For |
|-----------|----------------|----------|----------|
| **Sandbox runtime** | Process-level | Low | Development, testing |
| **Docker containers** | Container-level | Medium | Production workloads |
| **gVisor** | Kernel-level | Medium | Untrusted code execution |
| **Firecracker** | VM-level | Medium-High | Strong isolation, multi-tenant |
| **QEMU/KVM** | Full VM | High | Maximum isolation |

### Recommended Stack

```
Production: Docker + gVisor (--runtime=runsc)
Development: Docker with standard runtime
Multi-tenant: Firecracker micro-VMs
```

## Docker Hardening

### Minimal Dockerfile

```dockerfile
FROM node:20-slim
WORKDIR /workspace
COPY package*.json ./
RUN npm ci --production
COPY . .
USER node
CMD ["node", "agent.js"]
```

### Security Flags

```bash
docker run \
  --cap-drop ALL \                        # Drop all Linux capabilities
  --security-opt no-new-privileges \      # Prevent privilege escalation
  --read-only \                           # Read-only root filesystem
  --tmpfs /tmp:rw,noexec,nosuid \         # Writable temp with restrictions
  --tmpfs /workspace:rw \                 # Writable workspace
  --network none \                        # No network (or use custom network)
  --user 1000:1000 \                      # Non-root user
  --memory 2g \                           # Memory limit
  --cpus 2 \                              # CPU limit
  --pids-limit 256 \                      # Process limit
  -e ANTHROPIC_API_KEY="$KEY" \           # Pass secrets via env
  my-agent:latest
```

### Docker Compose

```yaml
services:
  agent:
    build: .
    cap_drop: ["ALL"]
    security_opt: ["no-new-privileges"]
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid
      - /workspace:rw
    user: "1000:1000"
    mem_limit: 2g
    cpus: 2
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    networks:
      - agent-net
    volumes:
      - ./project:/workspace/project:ro  # Read-only source
```

## Credential Management

### Proxy Pattern (Recommended)

Route API calls through a proxy that injects credentials:

```
Agent → Proxy (adds API key) → Anthropic API
```

```python
options = ClaudeAgentOptions(
    env={
        "ANTHROPIC_BASE_URL": "http://proxy:8080",  # Local proxy
        # No API key in agent environment!
    },
)
```

### Proxy Options

| Proxy | Best For |
|-------|----------|
| **Envoy** | Production, load balancing, mTLS |
| **mitmproxy** | Development, debugging |
| **Squid** | Caching, access control |
| **LiteLLM** | Multi-model proxy, rate limiting |

### HTTP Proxy Environment

```python
options = ClaudeAgentOptions(
    env={
        "HTTP_PROXY": "http://proxy:8080",
        "HTTPS_PROXY": "http://proxy:8080",
    },
)
```

### Secrets via Environment

```python
# Pass secrets via env, never in prompts or files
options = ClaudeAgentOptions(
    env={
        "DATABASE_URL": os.environ["DATABASE_URL"],
        "API_TOKEN": os.environ["API_TOKEN"],
    },
)
```

> **Never** include secrets in the `prompt` string, system prompt, or CLAUDE.md files. They may be logged or summarized during compaction.

## Filesystem Controls

### Read-Only Mounting

```bash
# Mount source code read-only
docker run -v ./src:/workspace/src:ro my-agent

# Allow writes only to specific directories
docker run \
  -v ./src:/workspace/src:ro \
  -v ./output:/workspace/output:rw \
  my-agent
```

### Overlay Filesystem

```bash
# Overlay allows writes that don't modify the original
docker run \
  --mount type=tmpfs,destination=/workspace/overlay \
  my-agent
```

### tmpfs for Temporary Data

```bash
# Writable temp that's destroyed on exit
docker run --tmpfs /tmp:rw,noexec,nosuid my-agent
```

## Credential Files to Exclude

**Never mount these files into agent containers:**

| File | Contains |
|------|---------|
| `.env` | Application secrets |
| `.git-credentials` | Git auth tokens |
| `~/.aws/credentials` | AWS access keys |
| `~/.config/gcloud/` | Google Cloud credentials |
| `~/.azure/` | Azure credentials |
| `~/.docker/config.json` | Docker registry auth |
| `~/.kube/config` | Kubernetes cluster access |
| `.npmrc` | npm auth tokens |
| `.pypirc` | PyPI auth tokens |
| `*.pem`, `*.key` | TLS/SSH private keys |
| `~/.ssh/` | SSH keys |
| `~/.netrc` | Network credentials |

### Docker .dockerignore

```
.env
.git-credentials
*.pem
*.key
.npmrc
.pypirc
.aws/
.gcloud/
.azure/
.kube/
```

## Network Isolation

### No Network Access

```python
# Agent with no network — safest for code-only tasks
options = ClaudeAgentOptions(
    disallowed_tools=["WebSearch", "WebFetch"],
    env={"HTTP_PROXY": "", "HTTPS_PROXY": ""},
)
```

```bash
docker run --network none my-agent
```

### Restricted Network

```bash
# Create isolated network
docker network create --internal agent-net

# Only allow API access
docker run \
  --network agent-net \
  --add-host api.anthropic.com:allowed \
  my-agent
```

### Egress Control

Use a proxy to control which external services the agent can reach:

```python
options = ClaudeAgentOptions(
    env={
        "HTTP_PROXY": "http://egress-proxy:8080",
        "HTTPS_PROXY": "http://egress-proxy:8080",
        "NO_PROXY": "localhost,127.0.0.1",
    },
)
```

## File Checkpointing for Safety

Enable file checkpointing to revert changes if something goes wrong:

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},
)
```

### Tracked Tools

| Tool | Tracked | Notes |
|------|---------|-------|
| Write | Yes | File creation and overwrite |
| Edit | Yes | String replacements |
| NotebookEdit | Yes | Jupyter cell edits |
| Bash | **No** | Commands not tracked — use Docker for isolation |

### Rewind Pattern

```python
client = ClaudeSDKClient(options)
async with client:
    await client.connect(prompt="Refactor the auth module")
    checkpoint_id = None

    async for msg in client.receive_messages():
        if msg.type == "assistant":
            checkpoint_id = msg.id  # Save checkpoint

    # If unhappy with results:
    if checkpoint_id:
        await client.rewind_files(checkpoint_id)
```

> **Limitation:** File checkpointing only tracks Write/Edit/NotebookEdit. Bash commands (file moves, git operations) are NOT tracked and cannot be reverted.

## Production Checklist

### Essential

- [ ] Set `max_budget_usd` on all production queries
- [ ] Set `max_turns` to prevent runaway loops
- [ ] Use `disallowed_tools` to block unnecessary tools
- [ ] Run in containers with `--cap-drop ALL`
- [ ] Use non-root user in containers
- [ ] Never mount credential files into containers
- [ ] Set `setting_sources=[]` unless you need filesystem settings

### Recommended

- [ ] Use a proxy for API key management
- [ ] Enable file checkpointing for revertibility
- [ ] Add PreToolUse hooks for Bash command validation
- [ ] Implement cost logging on ResultMessage
- [ ] Use `--read-only` Docker flag with explicit tmpfs
- [ ] Set memory and CPU limits on containers
- [ ] Use gVisor (`--runtime=runsc`) for untrusted code
- [ ] Implement egress network controls

### Monitoring

- [ ] Log `total_cost_usd` from every ResultMessage
- [ ] Alert on `error_during_execution` subtypes
- [ ] Track tool usage patterns via PostToolUse hooks
- [ ] Monitor container resource usage
- [ ] Set up rate limit monitoring

## Related Topics

- [Permissions](06-permissions.md) — Permission modes and evaluation
- [Hooks](05-hooks.md) — PreToolUse security hooks
- [Deployment](10-deployment.md) — Deployment patterns and scaling
- [Configuration](01-configuration.md) — Security-related options
