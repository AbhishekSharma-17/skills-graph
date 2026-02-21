# FAQs

Common troubleshooting and decision guides for Agno.

## Environment Variables

Set API keys for model providers:

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# Windows CMD
set OPENAI_API_KEY=sk-...
```

Make permanent by adding to `~/.zshrc`, `~/.bashrc`, or PowerShell profile.

## Workflow vs Team — When to Use Which

| Use Case | Choose |
|----------|--------|
| Sequential/parallel steps with dependencies | **Workflow** |
| Conditional routing based on content | **Workflow** |
| Quality assurance loops with end conditions | **Workflow** |
| Data transformation with predictable patterns | **Workflow** |
| Reasoning, collaboration, multi-tool decisions | **Team** |
| Research and planning tasks | **Team** |
| Tasks where agents divide responsibilities | **Team** |

> Workflows = assembly lines for known tasks. Teams = collaborative task forces for open-ended problems.

## Structured Outputs vs JSON Mode

| Method | When to Use |
|--------|-------------|
| **Structured Outputs** (default) | Model supports it — reliable, validated automatically |
| **JSON Mode** (`use_json_mode=True`) | Model doesn't support structured outputs, or broader compatibility needed |

```python
# Structured Outputs (preferred)
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    output_schema=User,
)

# JSON Mode (fallback)
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    output_schema=User,
    use_json_mode=True,
)
```

## TPM Rate Limiting

If hitting tokens-per-minute limits, enable exponential backoff:

```python
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    exponential_backoff=True,
    delay_between_retries=2,
)
```

Or configure at model level with `retries`, `retry_delay`, `exponential_backoff`.

## Switching Models

### Same provider (safe)
```python
# Start with expensive model
agent1 = Agent(model=OpenAIChat(id="gpt-4o"), db=db, add_history_to_context=True)
agent1.print_response("Query", session_id=sid, user_id=uid)

# Switch to budget model — history shared via session_id
agent2 = Agent(model=OpenAIChat(id="gpt-4o-mini"), db=db, add_history_to_context=True)
agent2.print_response("Follow up", session_id=sid, user_id=uid)
```

### Cross-provider (may have issues)
Different providers have different message format expectations. Cross-provider switching using shared session_id may produce unpredictable results due to message history format differences.

## OpenAI Key Required for Other Models

Some Agno features (embeddings, structured output validation) may default to OpenAI. Set `OPENAI_API_KEY` even when using other models, or explicitly configure an alternative embedder.

## AgentOS Connection Issues

1. Verify AgentOS is running: `curl http://localhost:7777/config`
2. Check CORS: ensure `cors_allowed_origins` includes your frontend URL
3. Check firewall/network if connecting from a different machine
4. For HTTPS: ensure SSL certificates are valid

## Docker Connection Error

If `could not connect to Docker`, ensure:
1. Docker Desktop is running
2. Docker socket is accessible: `docker ps`
3. On macOS, check Docker Desktop → Settings → General → "Start Docker Desktop when you log in"

## Authorization Failed (JWT)

If getting "Authorization Failed - JWT Verification":
1. Ensure `JWT_VERIFICATION_KEY` environment variable is set
2. Verify the key matches the one generated in the control plane
3. Check token expiration — tokens have a TTL
4. Ensure `authorization=True` is set on AgentOS

## Connecting to TablePlus

To inspect Agno's database with TablePlus:
1. Open TablePlus → New Connection
2. For Docker PostgreSQL: Host=localhost, Port=5532, User=ai, Password=ai, Database=ai
3. For SQLite: select the .db file directly
