---
name: n8n
description: "Fair-code workflow automation platform with visual canvas, 1500+ integrations, and native AI agent capabilities. MANDATORY TRIGGERS: n8n, workflow automation, n8n workflow, n8n node, n8n trigger, n8n webhook, n8n credential, n8n expression, n8n agent. Also trigger when the user wants to build automated workflows, connect APIs visually, create webhook endpoints, orchestrate multi-step processes, build AI agents with visual tools, or automate tasks across SaaS applications. When in doubt about whether to use this skill for workflow automation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["workflow", "automation", "integrations", "webhooks", "ai-agents", "low-code", "api"]
---

# n8n

> v2.31 | https://docs.n8n.io | https://github.com/n8n-io/n8n

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with n8n, understanding architecture, installation |
| [01-workflow-fundamentals.md](references/01-workflow-fundamentals.md) | Creating workflows, nodes, connections, canvas, publishing |
| [02-triggers-and-webhooks.md](references/02-triggers-and-webhooks.md) | Schedule triggers, webhook triggers, polling, event-based starts |
| [03-data-structure-and-expressions.md](references/03-data-structure-and-expressions.md) | Data flow, items, JSON structure, expressions, $json, $input |
| [04-flow-logic.md](references/04-flow-logic.md) | Conditionals, branching, loops, merging, sub-workflows |
| [05-code-node.md](references/05-code-node.md) | JavaScript/Python code, built-in variables, custom logic |
| [06-http-request-and-apis.md](references/06-http-request-and-apis.md) | REST API calls, authentication, pagination, curl import |
| [07-credentials-and-security.md](references/07-credentials-and-security.md) | Credential management, OAuth, API keys, domain restrictions |
| [08-error-handling.md](references/08-error-handling.md) | Error workflows, retry, debugging, error triggers, execution history |
| [09-ai-agents-and-tools.md](references/09-ai-agents-and-tools.md) | AI agents, chains, tools, memory, vector stores, LLM integration |
| [10-deployment-and-scaling.md](references/10-deployment-and-scaling.md) | Self-hosting, Docker, cloud deploy, queue mode, scaling |
| [11-workflow-management.md](references/11-workflow-management.md) | Settings, tags, versioning, import/export, sharing, MCP server |
| [12-integrations-ecosystem.md](references/12-integrations-ecosystem.md) | Built-in nodes, community packages, custom nodes, app integrations |

## Installation

```bash
# Quick start with npx (requires Node.js)
npx n8n

# Docker
docker volume create n8n_data
docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n

# npm global install
npm install n8n -g && n8n start
```

## Quick Reference

- [Official Docs](https://docs.n8n.io)
- [GitHub Repository](https://github.com/n8n-io/n8n)
- [npm Package](https://www.npmjs.com/package/n8n)
- [Workflow Templates](https://n8n.io/workflows)
- [Community Forum](https://community.n8n.io)
