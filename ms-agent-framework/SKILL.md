---
name: ms-agent-framework
description: "Expert skill for building AI agent systems with Microsoft Agent Framework (Python). Triggers on: 'Microsoft Agent Framework', 'agent-framework', 'Azure AI agents', multi-agent orchestration, building production AI agents on Azure, agentic workflows, Azure OpenAI agents. Covers: creating agents, running agents (streaming/non-streaming), tools (@tool, MCP, code interpreter, file search, Bing grounding, Azure AI Search), structured output (Pydantic), multimodal agents (vision/images), background responses, RAG agents, declarative agents, observability/DevUI, sessions/memory/storage, middleware (agent/function/chat), providers (Azure/OpenAI/Anthropic/Ollama/GitHub), workflows (graph orchestration), multi-agent patterns, hosting/deployment (Azure Functions/Container Apps/A2A)."
---

# Microsoft Agent Framework — Python Expert Skill

> **Version:** 1.0.0b260130 (Public Preview) | **Python only** | **Repo:** https://github.com/microsoft/agent-framework

## Navigation — Read ONLY the file(s) needed for the user's task

### ROUTING TABLE

Use this table to decide which reference file(s) to load. Match the user's intent to a topic, then `Read` that file. **Never load all files at once.**

| User wants to... | Load this file |
|---|---|
| Create first agent, install, setup, hello world | `references/01-getting-started.md` |
| Run agents, streaming vs non-streaming, ResponseStream, run options | `references/02-running-agents.md` |
| Structured output, Pydantic models, response_format, typed responses | `references/03-structured-output.md` |
| Add function tools, @tool decorator, tool parameters | `references/04-tools-function.md` |
| MCP servers, hosted MCP, code interpreter, file search, Bing, Azure AI Search | `references/05-tools-hosted.md` |
| RAG agents, file search, knowledge-enhanced agents | `references/06-rag.md` |
| Multi-turn conversations, sessions, AgentSession, persistence | `references/07-sessions.md` |
| Memory, InMemoryHistoryProvider, context providers, custom providers | `references/08-memory.md` |
| Middleware — agent, function, chat middleware, class/function/decorator patterns | `references/09-middleware.md` |
| Model providers — Azure OpenAI, OpenAI, Anthropic, Ollama, GitHub, custom | `references/10-providers.md` |
| **Workflows overview** — concepts, architecture, getting started | `references/11-workflows-core.md` |
| **Executors** — @handler, @executor, class-based, function-based, types, lifecycle | `references/11a-workflow-executors.md` |
| **Edges** — connections, conditional routing, fan-out, fan-in, SwitchCase | `references/11b-workflow-edges.md` |
| **Events** — WorkflowEvent types, streaming, superstep model, monitoring | `references/11c-workflow-events.md` |
| **Workflow Builder & Execution** — WorkflowBuilder, run, run_stream, results | `references/11d-workflow-builder-execution.md` |
| **Agents in Workflows** — AgentExecutor, streaming agents, structured data | `references/11e-workflow-agents.md` |
| **Human-in-the-Loop** — approval gates, request_info, response_handler | `references/11f-workflow-human-in-loop.md` |
| **State Management** — shared state, isolation, context data, kwargs | `references/11g-workflow-state.md` |
| **Checkpoints & Resuming** — persistence, recovery, durable workflows | `references/11h-workflow-checkpoints.md` |
| **Declarative Workflows** — YAML definition, config-driven, no-code | `references/11i-workflow-declarative.md` |
| **Observability in Workflows** — monitoring, tracing, debugging workflows | `references/11j-workflow-observability.md` |
| **Workflows as Agents** — composability, wrapping, reuse, reflection | `references/11k-workflow-as-agent.md` |
| **Visualization** — Mermaid diagrams, GraphViz, workflow export | `references/11l-workflow-visualization.md` |
| Sequential orchestration — SequentialBuilder, linear agent pipelines | `references/12a-orchestration-sequential.md` |
| Concurrent orchestration — ConcurrentBuilder, parallel agents, aggregation | `references/12b-orchestration-concurrent.md` |
| Handoff orchestration — HandoffBuilder, dynamic routing, autonomous mode | `references/12c-orchestration-handoff.md` |
| Group Chat orchestration — GroupChatBuilder, managers, collaborative discussion | `references/12d-orchestration-groupchat.md` |
| Magentic orchestration — MagenticBuilder, plan review, stall detection | `references/12e-orchestration-magentic.md` |
| Deploy overview, hosting options, production checklist | `references/13-deployment.md` |
| **Azure Functions** — AgentFunctionApp, serverless, durable, threads | `references/13a-azure-functions.md` |
| **A2A Protocol** — agent-to-agent, A2AAgent, A2AServer, AgentCard | `references/13b-a2a-protocol.md` |
| **AG-UI Protocol** — agent-frontend, SSE streaming, event types | `references/13c-ag-ui-protocol.md` |
| **OpenAI-Compatible** — /v1/chat/completions, Responses API, clients | `references/13d-openai-compatible.md` |
| **Deployment Guide** — FastAPI, Container Apps, AKS, CI/CD, scaling | `references/13e-deployment-guide.md` |
| Declarative agents, YAML-based agent definition | `references/14-declarative.md` |
| Observability overview, DevUI, telemetry basics | `references/15-observability.md` |
| **Tracing & Observability** — OpenTelemetry, spans, metrics, Azure Monitor | `references/15a-tracing-observability.md` |
| Multimodal, vision, images, Content types, data URIs | `references/16-multimodal.md` |
| Custom agents, BaseAgent, SupportsAgentRun, extend framework | `references/17-custom-agents.md` |
| API reference — all classes, methods, signatures | `references/18-api-reference.md` |
| **Security** — authentication, guardrails, content safety, data protection | `references/19-security.md` |
| **Purview** — data governance, compliance, responsible AI, audit | `references/20-purview.md` |
| **M365 Integration** — Copilot agents, Teams, Graph API, SharePoint | `references/21-m365-integration.md` |
| **Design Patterns: Core** — debate, reflection, hierarchical, supervisor, pipeline, guardrails, retry | `references/22-design-patterns-core.md` |
| **Design Patterns: Advanced** — circuit breaker, load balancing, batch, mock testing, time-travel, caching, event-driven, dynamic fan-out | `references/23-design-patterns-advanced.md` |

### FUZZY ROUTING — When user is vague

| User says something like... | They probably need... |
|---|---|
| "build an agent", "create a bot", "AI assistant" | `01-getting-started.md` → `02-running-agents.md` |
| "call a function", "agent uses tools", "API calls" | `04-tools-function.md` |
| "search the web", "search files", "run code" | `05-tools-hosted.md` |
| "remember things", "conversation history", "persist" | `07-sessions.md` → `08-memory.md` |
| "multiple agents", "agent team", "coordinate agents" | Start with `12a-orchestration-sequential.md`, then route by pattern |
| "pipeline", "chain steps", "process flow" | `11-workflows-core.md` (low-level) or `12a-orchestration-sequential.md` (high-level) |
| "sequential agents", "agent chain", "one after another" | `12a-orchestration-sequential.md` |
| "parallel agents", "concurrent", "run at same time" | `12b-orchestration-concurrent.md` |
| "route to agent", "handoff", "transfer to specialist" | `12c-orchestration-handoff.md` |
| "agents discuss", "brainstorm", "group chat", "debate" | `12d-orchestration-groupchat.md` |
| "complex task", "manager agent", "magentic", "plan review" | `12e-orchestration-magentic.md` |
| "executor", "handler", "workflow graph", "nodes" | `11a-workflow-executors.md` |
| "edges", "routing", "fan-out", "fan-in", "conditional" | `11b-workflow-edges.md` |
| "workflow events", "streaming events", "superstep" | `11c-workflow-events.md` |
| "workflow builder", "build workflow", "run workflow" | `11d-workflow-builder-execution.md` |
| "agent in workflow", "agent as node", "AgentExecutor" | `11e-workflow-agents.md` |
| "human approval", "human-in-the-loop", "approval gate" | `11f-workflow-human-in-loop.md` |
| "workflow state", "shared state", "context data" | `11g-workflow-state.md` |
| "checkpoint", "resume workflow", "save state", "durable" | `11h-workflow-checkpoints.md` |
| "YAML workflow", "declarative workflow", "config workflow" | `11i-workflow-declarative.md` |
| "workflow debugging", "workflow tracing", "workflow monitor" | `11j-workflow-observability.md` |
| "workflow as agent", "wrap workflow", "reuse workflow" | `11k-workflow-as-agent.md` |
| "workflow visualization", "diagram", "mermaid", "graphviz" | `11l-workflow-visualization.md` |
| "which orchestration", "compare patterns" | Read all 12a-12e routing tables then recommend |
| "JSON output", "typed response", "parse response" | `03-structured-output.md` |
| "deploy", "production", "host", "serverless" | `13e-deployment-guide.md` |
| "Azure Functions", "serverless agent", "AgentFunctionApp" | `13a-azure-functions.md` |
| "A2A", "agent-to-agent", "remote agent", "interop" | `13b-a2a-protocol.md` |
| "AG-UI", "frontend protocol", "agent UI", "SSE events" | `13c-ag-ui-protocol.md` |
| "OpenAI compatible", "chat completions", "/v1/chat" | `13d-openai-compatible.md` |
| "container apps", "docker", "kubernetes", "CI/CD" | `13e-deployment-guide.md` |
| "debug", "trace", "monitor", "logs", "OpenTelemetry" | `15a-tracing-observability.md` |
| "spans", "metrics", "Azure Monitor", "Application Insights" | `15a-tracing-observability.md` |
| "DevUI", "agent debugger" | `15-observability.md` |
| "intercept", "filter", "transform", "logging" | `09-middleware.md` |
| "security", "authentication", "managed identity" | `19-security.md` |
| "content safety", "guardrails", "PII", "jailbreak" | `19-security.md` |
| "Purview", "governance", "compliance", "audit" | `20-purview.md` |
| "M365", "Microsoft 365", "Teams", "Copilot agent" | `21-m365-integration.md` |
| "Graph API", "Outlook", "SharePoint", "OneDrive" | `21-m365-integration.md` |
| "YAML agent", "config-based", "no code agent" | `14-declarative.md` |
| "images", "vision", "multimodal", "analyze image" | `16-multimodal.md` |
| "custom agent class", "extend agent", "own agent" | `17-custom-agents.md` |
| "which model", "switch provider", "use Claude/GPT" | `10-providers.md` |
| "documents", "knowledge base", "search docs" | `06-rag.md` |
| "design pattern", "best practice", "pattern for" | `22-design-patterns-core.md` (start here) → `23-design-patterns-advanced.md` |
| "debate", "agents argue", "consensus", "multiple perspectives" | `22-design-patterns-core.md` |
| "reflection", "self-critique", "self-improve", "iterative quality" | `22-design-patterns-core.md` |
| "hierarchical", "task decomposition", "coordinator", "subtasks" | `22-design-patterns-core.md` |
| "supervisor", "monitor agents", "quality control" | `22-design-patterns-core.md` |
| "pipeline", "transform chain", "stage by stage" | `22-design-patterns-core.md` |
| "guardrails", "input validation", "output validation", "safety filter" | `22-design-patterns-core.md` + `19-security.md` |
| "retry", "backoff", "exponential", "transient failure" | `22-design-patterns-core.md` |
| "circuit breaker", "fault tolerance", "fallback", "cascade failure" | `23-design-patterns-advanced.md` |
| "load balancing", "distribute work", "round robin", "weighted" | `23-design-patterns-advanced.md` |
| "batch processing", "bulk", "concurrency limit", "parallel batch" | `23-design-patterns-advanced.md` |
| "mock testing", "unit test agent", "test without LLM" | `23-design-patterns-advanced.md` |
| "time travel", "debug workflow", "replay", "execution history" | `23-design-patterns-advanced.md` |
| "caching", "cache LLM", "reduce cost", "response cache" | `23-design-patterns-advanced.md` |
| "event driven", "webhook", "queue", "event trigger" | `23-design-patterns-advanced.md` |
| "dynamic fan-out", "dynamic routing", "variable workers" | `23-design-patterns-advanced.md` |
| "research this framework", "what can it do" | Read this SKILL.md only (overview below) |

---

## Framework Overview

Microsoft Agent Framework is an open-source Python SDK for building AI agents. It unifies AutoGen's multi-agent orchestration with Semantic Kernel's enterprise features.

### Core Architecture

```
Agent = LLM Client + Instructions + Tools + Memory + Middleware
Workflow = Graph of Agents/Functions connected by Edges
```

**Two building blocks:**
- **Agents** — Individual AI entities: one LLM + tools + memory. Use for open-ended tasks.
- **Workflows** — Graph-based orchestration of multiple agents/functions. Use for defined processes.

### Canonical Pattern (Python)

```python
import asyncio, os
from azure.identity.aio import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import tool
from typing import Annotated

@tool
def get_weather(location: Annotated[str, "City name"]) -> str:
    """Get weather for a location."""
    return f"Sunny, 72°F in {location}"

async def main():
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )
    agent = client.as_agent(
        name="Assistant",
        instructions="You are a helpful assistant.",
        tools=[get_weather],
    )

    # Non-streaming
    result = await agent.run("What's the weather in Seattle?")
    print(result.text)

    # Streaming
    async for chunk in agent.run("Tell me about Seattle", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### Provider Feature Matrix

| Provider | Client Class | Tools | Structured Output | Code Interpreter | File Search | MCP | Background |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **Azure OpenAI Responses** | `AzureOpenAIResponsesClient` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **OpenAI Responses** | `OpenAIResponsesClient` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Azure AI Foundry** | `AzureAIAgentClient` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Anthropic Claude** | `AnthropicChatClient` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Ollama** | `OllamaChatClient` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **GitHub Copilot** | `GitHubCopilotClient` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Critical Rules

1. **All operations are async** — always use `async/await` and `asyncio.run(main())`
2. **Tools MUST have**: `@tool` decorator + docstring + type hints + `Annotated` descriptions
3. **Sessions required for multi-turn** — without session, no memory between `agent.run()` calls
4. **Use `AzureCliCredential`** in dev, `DefaultAzureCredential` in production
5. **Framework is Public Preview** — pin version in `requirements.txt`
6. **Only one history provider** should use `load_messages=True`

### Installation

```bash
pip install agent-framework --pre
az login  # For Azure authentication
```

```bash
# Required environment variables (Azure OpenAI)
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.openai.azure.com"
export AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME="gpt-4o"
```

### Common Errors

| Error | Fix |
|---|---|
| `InvalidAuthenticationTokenError` | Run `az login` |
| `ResourceNotFoundError` | Check endpoint and deployment name env vars |
| `RateLimitError` | Wait or upgrade Azure plan |
| Tool missing docstring | Add `"""docstring"""` to every `@tool` function |
| Tool missing type hints | Use `Annotated[type, "description"]` on all params |
| No memory between turns | Pass `session=session` to `agent.run()` |
| Middleware not running | Check registration: agent-level vs run-level |
