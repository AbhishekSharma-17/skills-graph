# Audit Report — n8n Skill

## Assessment Date: 2026-07-27

## Scores (1–5)

| Category | Score | Notes |
|----------|-------|-------|
| **Architecture** | 5 | Clean router + 13 leaf nodes, no file exceeds 500 lines, logical topic separation |
| **Content Quality** | 4 | Comprehensive coverage of core concepts, practical code examples, well-structured tables |
| **Completeness** | 4 | Covers all major areas (workflows, triggers, data, code, AI, deployment, integrations); individual app node documentation deferred to n8n docs |
| **Maintainability** | 5 | VERSION.json tracks all references, check-updates.py validates integrity, clear npm version tracking |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover primary keywords; description includes broad use cases and fallback trigger |

## Overall: 4.6 / 5

## Detailed Notes

### Architecture
- SKILL.md is a pure router under 100 lines
- 13 reference files cover the full n8n surface area
- Topics flow logically: overview → fundamentals → data → logic → code → APIs → security → errors → AI → deploy → management → ecosystem
- No router nodes needed (each topic fits within 500 lines)

### Content Quality
- All reference files include practical code examples
- Tables used for quick reference on node types, configuration options, and comparison
- Common Pitfalls sections highlight real gotchas developers encounter
- Expressions and data structure well-documented with runnable examples

### Completeness
- Core workflow engine thoroughly covered
- AI integration (agents, chains, tools, memory, vector stores) given dedicated treatment
- Deployment options from development to production queue mode
- Individual integration documentation (500+ app nodes) intentionally deferred to n8n's own docs — skill focuses on patterns and core concepts
- MCP server integration documented as a key modern feature

### Maintainability
- check-updates.py validates against npm registry
- VERSION.json tracks per-file source pages and update dates
- 90-day staleness threshold appropriate for n8n's release cadence

### Trigger Quality
- Primary triggers: n8n, workflow automation, n8n workflow, n8n node, n8n trigger, n8n webhook
- Broad triggers: build automated workflows, connect APIs visually, orchestrate multi-step processes
- Includes AI-related triggers: build AI agents with visual tools
