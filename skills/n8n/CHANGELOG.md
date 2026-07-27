# Changelog

## [1.0.0] — 2026-07-27

Source version tracked: n8n 2.31

### Added

- **00-overview.md** — What n8n is, architecture, installation (npx, Docker, npm, Cloud), environment variables
- **01-workflow-fundamentals.md** — Workflows, nodes, connections, canvas, executions, publishing, debugging
- **02-triggers-and-webhooks.md** — Schedule triggers, webhooks (dual URL system, auth, response modes), app triggers, form/chat triggers
- **03-data-structure-and-expressions.md** — Items, JSON format, binary data, expression syntax, built-in variables ($json, $input, $now, etc.), Luxon dates
- **04-flow-logic.md** — If/Switch conditionals, Merge node, looping, Wait node, sub-workflows, execution order
- **05-code-node.md** — JavaScript/Python modes, run-once vs run-for-each, built-in variables, workflow static data, cookbook recipes
- **06-http-request-and-apis.md** — HTTP methods, authentication (OAuth2, API key, etc.), pagination, cURL import, AI tool mode, n8n REST API
- **07-credentials-and-security.md** — Credential types, OAuth2 setup, dynamic credentials, domain restrictions, encryption, SSL, SSO, SSRF protection
- **08-error-handling.md** — Error workflows, Error Trigger node, Stop and Error, retry/continue on fail, debugging executions
- **09-ai-agents-and-tools.md** — Agents, chains, tools ($fromAI), memory types, vector stores, embeddings, RAG, testing AI workflows
- **10-deployment-and-scaling.md** — Docker, npm, cloud providers, n8n Cloud, PostgreSQL, queue mode, scaling, OpenTelemetry, Prometheus
- **11-workflow-management.md** — Settings, tags, change history, import/export, sharing, variables, MCP server, source control, community packages
- **12-integrations-ecosystem.md** — Core nodes, app nodes (500+), AI/LangChain nodes, trigger nodes, community nodes, custom node development

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,900
