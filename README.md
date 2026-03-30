<p align="center">
  <h1 align="center">Skills Graph</h1>
  <p align="center">
    <strong>Precision-engineered AI agent skills with interconnected reference architectures.</strong>
    <br />
    <em>A methodology for building skills that carry 68,000+ lines of knowledge<br />while loading only what the AI actually needs.</em>
  </p>
  <p align="center">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
    <a href="#-the-agent-skills-standard"><img src="https://img.shields.io/badge/Agent%20Skills-Universal%20Standard-purple.svg" alt="Skills Standard"></a>
    <a href="#-platform-compatibility"><img src="https://img.shields.io/badge/Platforms-25%2B-green.svg" alt="Platforms"></a>
    <a href="#-skills-catalog"><img src="https://img.shields.io/badge/Skills-10%20Production%20Ready-orange.svg" alt="Skills"></a>
    <a href="#-the-technique-progressive-reference-architecture"><img src="https://img.shields.io/badge/Knowledge-68%2C300%2B%20Lines-red.svg" alt="Lines"></a>
  </p>
</p>

<br />

<details open>
<summary><strong>Table of Contents</strong></summary>

&nbsp;

| Section | |
|:--------|:--|
| [Overview](#-overview) | What Skills Graph is and why it exists |
| [Skills Catalog](#-skills-catalog) | All available skills at a glance |
| [The Problem](#-the-problem-with-current-skills) | Why conventional skills fail |
| [Side-by-Side Comparison](#-skills-graph-vs-conventional-skills) | Token economics, quality, maintenance |
| [The Technique](#-the-technique-progressive-reference-architecture) | The 3-level progressive loading system |
| [Five Pillars](#-the-five-pillars) | Deep dive into the methodology |
| [Skill Workflows](#-skill-workflows-cross-skill-orchestration) | How skills collaborate on complex tasks |
| [Graph in Action](#-how-the-interconnected-graph-works) | Navigation flows and dependency visualization |
| [Skill Anatomy](#-anatomy-of-a-skill) | The 6 standard components |
| [Installation](#-installation) | Smithery, manual, and native integration |
| [Platform Compatibility](#-platform-compatibility) | 25+ supported platforms |
| [Maintenance](#-maintenance--tooling) | Automated scripts and version tracking |
| [Contributing](#-contributing) | How to build your own Skills Graph skill |

</details>

<br />

---

## Overview

> *"A 68,000-line knowledge base that costs the same as a 50-line skill -- until you actually need it."*

Skills Graph is a **methodology** and a **collection** of production-grade AI agent skills built using **Progressive Reference Architecture (PRA)** -- a systematic approach to creating deeply interconnected, graph-structured knowledge bases that AI coding assistants can navigate with surgical precision.

Instead of dumping documentation into a single monolithic file or a flat folder of loosely related references, Skills Graph organizes knowledge as a **directed acyclic graph (DAG)** where every reference file is a node, every cross-reference is an edge, and a lightweight router sits at the root to guide the AI to exactly the information it needs -- nothing more, nothing less.

<table>
<tr><td><strong>Skills</strong></td><td>10 production-ready (Agno, MS Agent Framework, Remotion Prompt Generator, Trigger.dev, Drizzle ORM, Hono, Zod, Claude Agent SDK, Langfuse, Better Auth)</td></tr>
<tr><td><strong>Total Knowledge</strong></td><td>68,300+ lines across 282 reference files</td></tr>
<tr><td><strong>Router Overhead</strong></td><td>69-231 lines (the only cost when skill triggers)</td></tr>
<tr><td><strong>Context Efficiency</strong></td><td>~97% reduction vs monolithic approach</td></tr>
<tr><td><strong>Platform Support</strong></td><td>25+ AI coding assistants</td></tr>
<tr><td><strong>Maintenance</strong></td><td>Automated version checking, staleness detection, integrity validation</td></tr>
</table>

---

## Skills Catalog

Production-ready skills built with the Skills Graph methodology.

| # | Skill | Framework | Version | Files | Lines | Status |
|:-:|:------|:----------|:-------:|:-----:|:-----:|:------:|
| 1 | **[Agno](agno-skill/)** | [Agno](https://github.com/agno-agi/agno) v2.5.3 | `1.2.0` | 116 | 23,431 | Production |
| 2 | **[MS Agent Framework](ms-agent-framework/)** | [MS Agent Framework](https://github.com/microsoft/agent-framework) 1.0.0b | `2.0.0` | 61 | ~14,000 | Production |
| 3 | **[Remotion Prompt Generator](skills/remotion-prompt-generator/)** | [Remotion](https://remotion.dev) 4.x | `1.1.0` | 15 | ~2,733 | Production |
| 4 | **[Trigger.dev](skills/trigger-dev/)** | [Trigger.dev](https://trigger.dev) v4.4.3 | `1.0.0` | 11 | ~3,512 | Production |
| 5 | **[Drizzle ORM](skills/drizzle-orm/)** | [Drizzle ORM](https://orm.drizzle.team) v0.45.1 | `1.0.0` | 12 | ~3,539 | Production |
| 6 | **[Hono](skills/hono/)** | [Hono](https://hono.dev) v4.12.0 | `1.0.0` | 12 | ~3,430 | Production |
| 7 | **[Zod](skills/zod/)** | [Zod](https://zod.dev) v4.x | `1.0.0` | 13 | ~3,686 | Production |
| 8 | **[Claude Agent SDK](skills/claude-agent-sdk/)** | [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) Python 0.1.51 / TS 0.2.86 | `1.1.0` | 16 | ~5,817 | Production |
| 9 | **[Langfuse](skills/langfuse/)** | [Langfuse](https://langfuse.com/docs) v3.162.0 | `1.0.0` | 13 | ~3,993 | Production |
| 10 | **[Better Auth](skills/better-auth/)** | [Better Auth](https://www.better-auth.com/docs) v1.5.6 | `1.0.0` | 13 | ~4,232 | Production |
| | | | | **282** | **~68,373** | |

<br />

<details>
<summary><strong>Agno Skill -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Build AI agents, multi-agent teams, and agentic workflows with the Agno open-source framework.

| Domain | Topics |
|:-------|:-------|
| **Core** | Agents, Teams, Workflows, Workflow Patterns (8 types) |
| **Tools** | 120+ built-in toolkits across 11 categories (search, data, web, dev, comms, media, productivity), custom tools, MCP |
| **Models** | 40+ providers, model-as-string syntax, response caching, multimodal compatibility matrix |
| **Storage** | 18 database backends (Postgres, MongoDB, Redis, DynamoDB, SQLite, Supabase, and more) |
| **Knowledge** | RAG pipelines, 14+ vector databases, 12+ embedding providers, chunking, hybrid search |
| **Memory** | Automatic and agentic memory, MemoryManager, MemoryTools, multi-user isolation |
| **Learning** | Learning Machines, 6 learning stores, 3 modes (Always/Agentic/Propose) |
| **Safety** | Guardrails (PII, prompt injection, content moderation), Human-in-the-Loop, hooks |
| **Observability** | 12 monitoring platforms, OpenTelemetry tracing, custom logging |
| **Production** | AgentOS (50+ API endpoints), deployment templates (Docker, Railway, AWS ECS), 6 chat interfaces |
| **Advanced** | Reasoning (3 approaches), multimodal (image/audio/video), evals, context management, culture |

**Graph topology:** 12 router nodes / 104 leaf nodes / 34 routing entries

</details>

<br />

<details>
<summary><strong>Remotion Prompt Generator -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Generate detailed, production-ready prompts for the Remotion Dev skill to create programmatic React-based videos.

| Domain | Topics |
|:-------|:-------|
| **Remotion Capabilities** | Core architecture, compositions, sequences, hooks, output formats, platform dimensions, animation system, asset support, audio, data-driven videos, 3D, rendering options, limitations, packages ecosystem |
| **Intelligent Inference** | Signal extraction from vague prompts, keyword-to-capability mapping, auto-fill decision engine, industry auto-detection (10 industries), smart scene generation, uploaded asset analysis, context clue mining |
| **Video Types** | Marketing & SaaS, Social Media, Data & Analytics, Education & Explainer, E-commerce & Real Estate, Entertainment & Media, Personalized & Data-Driven |
| **Prompt Engineering** | 12-section structured prompt format, scene description format, animation specification language, spring presets, color palettes, font recommendations, quality checklist |
| **Discovery Workflow** | 16 follow-up questions in 4 tiers, progressive questioning strategy, requirement validation, vague request handling, asset inventory |
| **Asset & Styling** | Platform safe zones, logo placement patterns, image treatments, background patterns, branding by industry, text sizing, aspect ratio reference |
| **Animation & Effects** | Entrance/exit/continuous animations, spring physics presets, transition catalog, text animation patterns (8 types), scene composition layouts (6 patterns), timing guide, 3D basics |
| **Domain Examples** | Prompt patterns for SaaS, e-commerce, finance, real estate, education, healthcare, events, personal brand, agency, crypto/web3 |

**Graph topology:** 1 router node / 14 leaf nodes / 8 routing entries

</details>

<br />

<details>
<summary><strong>Trigger.dev -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Build and deploy TypeScript background jobs, AI workflows, and scheduled tasks with retries, queues, observability, and elastic scaling.

| Domain | Topics |
|:-------|:-------|
| **Overview & Setup** | Architecture, installation, quickstart, SDK imports, framework support (Next.js, Express, Hono, Remix, etc.), key terminology |
| **Writing Tasks** | Task definition, configuration (retry/queue/machine/maxDuration), lifecycle hooks (init, onStart, onSuccess, onFailure, catchError), machine presets (micro to large-2x), payload/output limits, Zod validation, structured logging |
| **Triggering Tasks** | tasks.trigger(), batchTrigger(), triggerAndWait(), batch.triggerByTaskAndWait(), streaming batches, trigger options (delay, TTL, idempotency, debounce, concurrencyKey, queue, priority, tags, metadata) |
| **Runs** | 10 run states, run lifecycle, metadata API (set/append/increment), tags (max 5 per run), runs.list/retrieve/subscribe/poll, cancellation, replay, reschedule |
| **Scheduled Tasks** | Declarative cron (in-code), imperative cron (dynamic/per-user), 5-field cron syntax, timezone + DST handling, schedule management API (create/update/deactivate/delete), environment rules |
| **Concurrency & Queues** | Queue mechanics, environment concurrency (base + burst), task-level limits, shared queues, per-tenant queuing (concurrencyKey), free vs paid tier pattern, queue management API, priority queues |
| **Error Handling** | Retry config (maxAttempts, factor, backoff), global vs task-level, retry.onThrow (block-level), retry.fetch (HTTP with status codes + Retry-After), catchError (dynamic), AbortTaskRunError, OpenAI retry pattern |
| **Wait & HITL** | wait.for/wait.until duration pauses, waitpoint tokens (create/complete/list), HTTP + SDK + client-side completion, approval workflows, multi-step chains, drip campaigns, AI + human review |
| **Realtime & Streaming** | Run subscriptions (SSE), streams.define + write, React hooks (useRealtimeRun, useRealtimeStream, useRealtimeBatch, useRealtimeRunsWithTag), TriggerAuthContext, public access tokens, progress bars, AI chat streaming |
| **Configuration** | trigger.config.ts reference, runtime (Node/Bun), build config, 8 build extensions (Prisma, Puppeteer, FFmpeg, Python, aptGet, envSync, packages, files), OpenTelemetry + exporters, process keep-alive |
| **Deployment** | dev command, deploy command (all flags), 4 environments (DEV/STAGING/PREVIEW/PROD), CI/CD (GitHub Actions, GitLab CI), self-hosting (Docker, Kubernetes), preview branches, monorepo setup |

**Graph topology:** 0 router nodes / 11 leaf nodes / 11 routing entries

</details>

<br />

**Planned:**&ensp; LangGraph &middot; CrewAI &middot; OpenAI Agents SDK &middot; Semantic Kernel

> Want a skill for a framework not listed? [Open an issue](../../issues) or [contribute one](#-contributing).

---

## The Problem with Current Skills

Most AI agent skills today are built using one of three broken patterns:

<table>
<tr>
<th width="33%">The Monolith</th>
<th width="33%">The Flat Dump</th>
<th width="33%">The Copy-Paste</th>
</tr>
<tr>
<td>

```
my-skill/
└── SKILL.md  # 3,000-5,000+ lines
```

AI loads **everything** every time. 5,000 tokens burned on a simple question.

</td>
<td>

```
my-skill/
├── SKILL.md
└── references/
    ├── agents.md
    ├── tools.md
    └── ...40 more files
```

Files exist but AI has **no guidance** on which to read. Guesses wrong.

</td>
<td>

```
my-skill/
└── SKILL.md  # 500 lines of fragments
```

Cherry-picked docs with **no version tracking**. Stale within weeks.

</td>
</tr>
</table>

**What all three share:** no version tracking, no staleness detection, no integrity validation, no self-audit, no cross-platform awareness.

---

## Skills Graph vs. Conventional Skills

### Token Economics

| Scenario | Monolith | Flat Files | **Skills Graph** |
|:---------|:--------:|:----------:|:----------------:|
| Skill idle (not triggered) | ~100 | ~100 | ~100 |
| Skill triggers (any query) | **~5,000** | ~500 | ~500 |
| Simple question | **~5,000** | ~800 (maybe wrong file) | **~700** |
| Moderate question | **~5,000** | ~1,500 (2-3 files, guessing) | **~900** |
| Complex question | **~5,000** | ~3,000 (5+ files) | **~1,200** |
| Total knowledge available | 5,000 lines | varies | **40,000+ lines** |

> **Skills Graph skills carry 7x more knowledge while using 4-7x fewer tokens per query.**

### Architecture

| Dimension | Conventional | Skills Graph |
|:----------|:------------|:-------------|
| Structure | Single file or flat folder | Hierarchical DAG with router nodes |
| Entry point | SKILL.md (500-5,000 lines) | SKILL.md (69-231 lines, pure router) |
| Navigation | None -- AI guesses | Routing tables with "Read When" conditions |
| Reference organization | Flat list | Graph: routers branch to sub-references |
| Loading strategy | All-or-nothing | Progressive: metadata -> router -> specific leaf |
| Depth of knowledge | Shallow (limited by file size) | Deep (unlimited -- leaf nodes expand the graph) |

### Maintenance

| Capability | Conventional | Skills Graph |
|:-----------|:------------|:-------------|
| Version tracking | None | `VERSION.json` with semantic versioning |
| Framework version pinning | None | Per-file `written_for` metadata |
| Staleness detection | Manual | Automated (`--stale` flag, configurable) |
| Integrity validation | None | Automated (`--integrity` verifies routing table) |
| Upstream change detection | None | PyPI version check + docs sitemap diffing |
| Architecture audit | Never | `AUDIT-REPORT.md` with scorecard |

---

## The Technique: Progressive Reference Architecture

PRA is built on a single principle: **the AI should pay only for the knowledge it actually uses.**

```
                    ALWAYS IN CONTEXT
                    +-------------------------+
  Level 1           |  YAML Metadata          |  ~100 tokens
  (Metadata)        |  name + description     |  Same cost whether skill
                    |  + trigger keywords     |  has 5 files or 500
                    +------------+------------+
                                 |
                    LOADED WHEN SKILL TRIGGERS
                    +------------v------------+
  Level 2           |  SKILL.md Router Body   |  ~500 tokens
  (Router)          |  Routing table with     |  Maps intent -> file
                    |  "Read When" conditions |  34 routes in 69 lines
                    +------------+------------+
                                 |
                    LOADED ON DEMAND (specific path only)
                    +------------v------------+
  Level 3           |  Reference Graph        |  ~200-400 tokens per node
  (References)      |  Router nodes -> Leaves |  Only the relevant path
                    |  116 files, 23,431 lines|  is ever loaded
                    +-------------------------+
```

**Level 1 -- Metadata** (always loaded): YAML frontmatter with name, description, trigger keywords. ~100 tokens. Identical cost whether the skill has 5 or 500 reference files.

**Level 2 -- Router** (loaded on trigger): The SKILL.md body -- a lean routing table mapping user intent to specific files via "Read When" conditions. ~500 tokens.

**Level 3 -- References** (loaded on demand): The knowledge graph itself. Router nodes fan out to sub-references; leaf nodes contain actual knowledge. The AI navigates the graph, loading only the path relevant to the current query.

---

## The Five Pillars

### 1. Intent-Based Routing

Every navigation decision is driven by **user intent**, not file naming or alphabetical order.

```markdown
| Reference     | File                    | Read When                                              |
|---------------|-------------------------|---------------------------------------------------------|
| **Knowledge** | `references/knowledge.md` | RAG pipelines, vector databases, embedders, chunking... |
| **Memory**    | `references/memory.md`    | Automatic vs agentic memory, MemoryManager...           |
```

The "Read When" column is the critical innovation. When a user asks *"how do I set up a RAG pipeline with Pinecone?"*, the AI sees "RAG pipelines, vector databases" and loads `knowledge.md` directly -- no guessing.

For router nodes, the pattern repeats at a deeper level with **Sub-Reference tables**, giving two levels of intent matching before the AI ever reads content.

### 2. Hierarchical Decomposition

Large topics are recursively split using the **router + sub-files** pattern:

```
tools.md (router -- 56 lines)
  |-- tools/creating-tools.md        (leaf -- @tool decorator)
  |-- tools/custom-toolkits.md       (leaf -- Toolkit classes)
  |-- tools/advanced.md              (leaf -- hooks, caching, RunContext)
  |-- tools/mcp-tools.md             (leaf -- Model Context Protocol)
  |-- tools/builtin-search.md        (leaf -- DuckDuckGo, Tavily, Exa...)
  |-- tools/builtin-data.md          (leaf -- SQL, Pandas, BigQuery...)
  |-- tools/builtin-web.md           (leaf -- Firecrawl, Crawl4AI...)
  |-- tools/builtin-dev.md           (leaf -- GitHub, Docker, Shell...)
  |-- tools/builtin-comms.md         (leaf -- Email, Slack, Discord...)
  |-- tools/builtin-media.md         (leaf -- DALL-E, ElevenLabs...)
  +-- tools/builtin-productivity.md  (leaf -- Google Calendar, Notion...)
```

**The rules:** >500 lines = must split. >300 lines = must have TOC. Routers under 100 lines. Leaves 200-500 lines.

### 3. Zero-Cost Idle State

A 50-line skill and a 23,431-line skill have **identical idle cost** (~100 tokens). Install dozens of Skills Graph skills without bloating your AI's context. They only consume tokens when you actually need them.

### 4. Version-Aware Maintenance

Every skill tracks versions at three levels:

```json
{
  "skill_version": "1.2.0",
  "agno_version_tracked": "2.5.3",
  "references": {
    "agents.md": { "written_for": "2.5.2", "last_updated": "2026-02-18" },
    "evals.md":  { "written_for": "2.5.3", "last_updated": "2026-02-21" }
  }
}
```

When Agno 2.6.0 releases, you know exactly which files target 2.5.2 and might need updates. Automated scripts handle staleness detection and integrity validation.

### 5. Self-Auditing Architecture

Every skill includes an `AUDIT-REPORT.md` scoring itself across quality dimensions:

| Category | Score |
|:---------|:-----:|
| SKILL.md size (69 lines) | 5/5 |
| Progressive disclosure | 4/5 |
| Reference splitting | 4/5 |
| YAML frontmatter | 5/5 |
| TOC on large files | 4/5 |
| Description triggering | 4/5 |
| Tooling & maintenance | 5/5 |

Plus: comparison with exemplary skills, cross-platform compatibility analysis, and a prioritized improvement plan.

---

## Skill Workflows: Cross-Skill Orchestration

Skills Graph skills are powerful individually, but the full potential emerges when **multiple skills collaborate on a single complex task** -- what we call **Skill Workflows**.

### The Problem

A developer says: *"Build me a production-ready multi-agent customer support system."*

No single skill can answer this. The task spans agent architecture, tool integration, workflow orchestration, database/memory, deployment, and safety. With conventional skills, the AI either picks one skill (partial answer) or loads everything (blows the context budget).

### The Solution

Skill Workflows **decompose the task into phases** and traverse multiple skill graphs surgically:

```
  PLAN                          EXECUTE                       SYNTHESIZE
+------------------+          +------------------+          +------------------+
| Decompose task   |          | For each phase:  |          | Combine outputs  |
| into phases      |--------->| Route to skill(s)|--------->| from all phases  |
| Identify which   |          | Traverse graph   |          | into a coherent  |
| skills per phase |          | Load only needed |          | solution         |
|                  |          | leaf nodes       |          |                  |
+------------------+          +------------------+          +------------------+
```

### Complex Example: Multi-Framework Agent Migration

> **Task:** *"Migrate a customer support system from Microsoft Agent Framework (sequential orchestration, Azure Functions, Cosmos DB, content safety) to Agno with AgentOS."*

**Phase 1 -- Understand Source** (MS Agent Framework skill):

```
SKILL.md (109 routes)
    |
    |-->  12c-orchestration-handoff.md      <-- handoff pattern
    |-->  12a-orchestration-sequential.md   <-- sequential builder
    |-->  08-memory.md                      <-- memory providers
    |-->  19-security.md                    <-- content safety
    +-->  13a-azure-functions.md            <-- deployment model

Tokens loaded: ~2,000
```

**Phase 2 -- Design Target** (Agno skill):

```
SKILL.md (34 routes)
    |
    |-->  teams.md                          <-- multi-agent coordination
    |-->  database.md (router)
    |       +-->  database/backends.md      <-- MongoDB/Cosmos equivalent
    |-->  memory.md (router)
    |       +-->  memory/core-concepts.md   <-- map memory model
    |-->  guardrails.md (router)
    |       +-->  guardrails/builtin-guardrails.md
    +-->  agentos.md (router)
            +-->  agentos/setup-api.md      <-- production deployment

Tokens loaded: ~2,500
```

**Phase 3 -- Migration Mapping:**

```
Source (MS Agent Framework)          Target (Agno)
---------------------------------    ------------------------------
HandoffBuilder + 4 agents            Team(mode="route") + 4 agents
SequentialBuilder pipeline           Workflow with Router step
InMemoryHistoryProvider + Cosmos     MongoDb(db_url="cosmos://...")
Content Safety middleware            @guardrail + input validation
Azure Functions deployment           AgentOS + Docker on Azure
A2A protocol                         AgentOS SSE streaming API
```

**Phase 4 -- Generate Code** using leaf nodes already loaded.

<table>
<tr>
<th>Without Skill Workflows</th>
<th>With Skill Workflows</th>
</tr>
<tr>
<td>

Load entire MS skill: ~14,000 tokens<br />
Load entire Agno skill: ~23,000 tokens<br />
**Total: ~37,000 tokens**<br />
(likely exceeds context budget)

</td>
<td>

Phase 1 (5 MS leaves): ~2,000 tokens<br />
Phase 2 (9 Agno nodes): ~2,500 tokens<br />
Phases 3-4: 0 additional<br />
**Total: ~4,500 tokens (88% reduction)**

</td>
</tr>
</table>

The AI accessed 37,000+ lines of knowledge while loading only 4,500 tokens -- because the graph structure let it navigate to exactly 14 nodes (out of 177) relevant to this specific task.

### Workflow Skills (Future Vision)

The natural evolution: **Workflow Skills** -- meta-skills whose references are not documentation but **execution plans** that orchestrate other skills.

```
workflow-skills/
|-- SKILL.md                        # Routes by task type
+-- references/
    |-- agent-migration.md          # Cross-framework migration
    |-- greenfield-agent-system.md  # New agent system from scratch
    |-- rag-pipeline-design.md      # RAG system design
    |-- production-hardening.md     # Prototype -> production
    +-- multi-agent-debug.md        # Debug multi-agent issues
```

Each workflow reference would contain phase decomposition, skill routing maps, decision points, and synthesis templates. A Workflow Skill doesn't contain framework knowledge -- it contains **orchestration intelligence** that composes knowledge from other skills.

This is the endgame: from individual skill graphs to a **graph of graphs**.

---

## How the Interconnected Graph Works

### Router Pattern

Every complex topic uses a **router file** with conditional loading guidance:

```markdown
# Agno Memory

## Sub-References

| Sub-Reference    | File                             | Read When                              |
|------------------|----------------------------------|----------------------------------------|
| **Core Concepts**| `memory/core-concepts.md`        | Automatic vs agentic memory, setup...  |
| **Tools & Mgr**  | `memory/tools-manager.md`        | MemoryTools, MemoryManager, sharing... |
| **Patterns**     | `memory/patterns-best-practices.md` | Teams with memory, optimization...  |

## Quick Start
[minimal code -- enough for simple cases without loading sub-references]
```

The router itself answers simple queries. The Sub-Reference table guides deeper for complex ones.

### Navigation Flow

```
User: "How do I add persistent memory to my Agno agent with Postgres?"

  Step 1   SKILL.md metadata (always in context)
           AI sees "agno" in user's stack --> skill triggers
           Cost: 0 additional tokens

  Step 2   SKILL.md routing table loads
           Finds: Memory --> references/memory.md
           Cost: +500 tokens

  Step 3   AI reads references/memory.md (router node)
           Sees Sub-References, picks "Core Concepts"
           Cost: +200 tokens

  Step 4   AI reads memory/core-concepts.md (leaf node)
           Gets detailed memory setup with database config
           Cost: +350 tokens

  Total:   ~1,050 tokens out of 23,431 available (4.5%)
```

### Dependency Graph (Agno Skill)

```
                            SKILL.md
                          (34 routes)
                               |
         +-------------+-------+-------+--------------+
         |             |       |       |              |
    Foundation    Execution    |   State & Memory   Safety
    +----+---+   +----+---+   |   +----+----+    +---+---+
  agents   teams tools/  models|  memory/ database/ guardrails/
  (leaf)  (leaf) (router)(leaf)|  (router)(router)  (router)
                   |           |     |       |         |
           +-------+-----+    |  +--+--+  +-+--+   +--+--+
        creating custom  MCP  | core tools backends builtin
        (leaf)  kits   (leaf) | (leaf)(leaf)(leaf)  (leaf)
               (leaf)         |
                 |            |        Production
         +-------+------+    |     +-----+------+
      search    data   web   |   agentos/     deploy
      (leaf)   (leaf) (leaf) |   (router)     (leaf)
                             |      |
       ...6 more builtin     |   +--+--+
          categories         |  setup config
                             |  (leaf)(leaf)
                             |
                        Knowledge & Learning
                       +-----+------+
                    knowledge    learning
                     (leaf)      (leaf)
```

Each root-to-leaf path is a navigation sequence. The AI never loads sibling branches.

---

## Anatomy of a Skill

Every Skills Graph skill has six standard components:

| Component | Purpose |
|:----------|:--------|
| **`SKILL.md`** | The router. Only file with YAML frontmatter. Routing table mapping intent to references. Under 100 lines. |
| **`references/`** | The knowledge graph. Router nodes (Sub-Reference tables) and leaf nodes (actual knowledge). No frontmatter on any reference file. |
| **`VERSION.json`** | Version tracking. Skill version, framework version, per-file metadata, docs sitemap, statistics. |
| **`CHANGELOG.md`** | Release history. Added, Changed, Split, Fixed, Stats categories per version. |
| **`scripts/`** | Maintenance automation. Version checking, sitemap diffing, staleness detection, integrity validation. |
| **`AUDIT-REPORT.md`** | Architecture quality. Self-assessment scorecard, exemplary skill comparison, improvement plan. |

---

## Repository Structure

```
skills-graph/
|-- README.md
|-- CONTRIBUTING.md                     # Full skill creation guide with templates
|-- SECURITY.md                         # Security policy and vulnerability reporting
|-- CODE_OF_CONDUCT.md                  # Community standards
|-- LICENSE
|-- .github/
|   |-- PULL_REQUEST_TEMPLATE.md        # PR checklist for skill contributions
|   +-- ISSUE_TEMPLATE/                 # Bug reports, skill requests, improvements
|
|-- _template/                          # Copy-paste starter for new skills
|   |-- SKILL.md                        # Router template with instructions
|   |-- VERSION.json                    # Version tracking template
|   |-- CHANGELOG.md                    # Release history template
|   |-- AUDIT-REPORT.md                 # Quality scorecard template
|   |-- scripts/check-updates.py        # Maintenance script template
|   +-- references/                     # Leaf + router node examples
|
|-- skills/
|   |-- agno-skill/                     # v1.2.0 | 116 files | 23,431 lines
|   |   |-- SKILL.md                    # 69 lines, 34 routing entries
|   |   |-- VERSION.json
|   |   |-- CHANGELOG.md
|   |   |-- AUDIT-REPORT.md
|   |   |-- scripts/
|   |   |   +-- check-updates.py
|   |   +-- references/
|   |       |-- agents.md               teams.md       workflows.md
|   |       |-- models.md               knowledge.md   learning.md
|   |       |-- reasoning.md            multimodal.md  deploy.md
|   |       |-- tools.md -------> tools/           (11 sub-files)
|   |       |-- memory.md ------> memory/          (3 sub-files)
|   |       |-- database.md ----> database/        (3 sub-files)
|   |       |-- guardrails.md --> guardrails/      (3 sub-files)
|   |       |-- context-mgmt.md > context-mgmt/    (5 sub-files)
|   |       |-- agentos.md -----> agentos/         (2 sub-files)
|   |       |-- evals.md -------> evals/           (4 sub-files)
|   |       +-- ... (30+ more topic files)
|   |
|   |-- ms-agent-framework/             # v2.0.0 | 61 files | ~14,000 lines
|   |   |-- SKILL.md                    # ~55 lines, 22 routing entries
|   |   |-- metadata/
|   |   |-- scripts/
|   |   +-- references/                 # 01-10 core, 11-11l workflows,
|   |                                   # 12a-12e orchestration, 13-23 deploy+patterns
|   |
|   |-- remotion-prompt-generator/      # v1.1.0 | 15 files | ~2,733 lines
|   |   |-- SKILL.md                    # 56 lines, 8 routing entries
|   |   |-- VERSION.json
|   |   |-- CHANGELOG.md
|   |   |-- AUDIT-REPORT.md
|   |   |-- scripts/
|   |   |   +-- check-updates.py
|   |   +-- references/
|   |       |-- remotion-capabilities.md    [ALWAYS LOADED]
|   |       |-- intelligent-inference.md    [ALWAYS LOADED]
|   |       |-- video-types.md (router) --> video-types/  (7 sub-files)
|   |       |-- prompt-engineering.md
|   |       |-- discovery-workflow.md
|   |       |-- asset-styling-guide.md
|   |       |-- animation-effects.md
|   |       +-- prompt-engineering/domain-examples.md
|   |
|   +-- trigger-dev/                    # v1.0.0 | 11 files | ~3,512 lines
|       |-- SKILL.md                    # 48 lines, 11 routing entries
|       |-- VERSION.json
|       |-- CHANGELOG.md
|       |-- AUDIT-REPORT.md
|       |-- scripts/
|       |   +-- check-updates.py
|       +-- references/
|           |-- 00-overview.md          # Setup, quickstart, architecture
|           |-- 01-writing-tasks.md     # Task definition, hooks, machines
|           |-- 02-triggering-tasks.md  # Trigger methods, batches, options
|           |-- 03-runs.md             # Lifecycle, states, metadata, tags
|           |-- 04-scheduled-tasks.md  # Cron, timezones, schedule API
|           |-- 05-concurrency-queues.md # Queues, per-tenant, burst
|           |-- 06-error-handling-retries.md # Retries, backoff, catchError
|           |-- 07-wait-and-human-in-loop.md # Tokens, approvals, HITL
|           |-- 08-realtime-streaming.md # React hooks, SSE, streaming
|           |-- 09-configuration.md    # Config, build extensions, telemetry
|           +-- 10-deployment-cli.md   # Deploy, CI/CD, self-hosting
|
+-- drizzle-orm/                      # v1.0.0 | 12 files | ~3,539 lines
    |-- SKILL.md                      # 53 lines, 12 routing entries
    |-- VERSION.json
    |-- CHANGELOG.md
    |-- AUDIT-REPORT.md
    |-- scripts/
    |   +-- check-updates.py
    +-- references/
        |-- 00-overview.md            # Setup, drivers, quickstart
        |-- 01-schema-declaration.md  # Tables, column types, enums
        |-- 02-indexes-constraints.md # PKs, FKs, unique, check, indexes
        |-- 03-relations.md           # 1:1, 1:N, M:N, self-referencing
        |-- 04-select-queries.md      # SELECT, filters, aggregations, CTEs
        |-- 05-mutations.md           # INSERT, UPDATE, DELETE, upsert
        |-- 06-joins.md              # Inner, left, right, full, lateral
        |-- 07-relational-queries.md # findMany, findFirst, nested with
        |-- 08-transactions.md       # Transactions, savepoints, isolation
        |-- 09-migrations.md         # drizzle-kit, generate, push, pull
        |-- 10-performance.md        # Prepared stmts, replicas, logging
        +-- 11-validation.md         # Zod, Valibot, TypeBox integration
|
+-- hono/                             # v1.0.0 | 12 files | ~3,430 lines
    |-- SKILL.md                      # 52 lines, 12 routing entries
    |-- VERSION.json
    |-- CHANGELOG.md
    |-- AUDIT-REPORT.md
    |-- scripts/
    |   +-- check-updates.py
    +-- references/
        |-- 00-overview.md            # Setup, runtimes, quickstart
        |-- 01-routing.md             # HTTP methods, params, wildcards, groups
        |-- 02-context-api.md         # c.json, c.text, c.req, c.env, streaming
        |-- 03-middleware.md          # Built-in, custom, factory pattern
        |-- 04-authentication.md      # JWT, Bearer, Basic auth, API keys
        |-- 05-validation.md          # Zod validator, all targets, RPC types
        |-- 06-rpc-type-safety.md     # hc client, AppType, SWR/TanStack
        |-- 07-jsx-rendering.md       # SSR JSX, Suspense, streaming, client
        |-- 08-error-handling.md      # HTTPException, onError, notFound
        |-- 09-testing.md             # app.request, Vitest, env mocking
        |-- 10-runtime-adapters.md    # Node.js, CF Workers, Bun, Deno, Lambda
        +-- 11-best-practices.md      # Structure, security, performance, CI/CD
```

---

## Installation

### Via skills CLI (Recommended)

> **[Browse all skills on skills.sh](https://skills.sh)**

```bash
# See what skills are available before installing
npx skills add AbhishekSharma-17/skills-graph --list

# Install all skills from this repo
npx skills add AbhishekSharma-17/skills-graph

# Install a specific skill
npx skills add AbhishekSharma-17/skills-graph --skill agno
npx skills add AbhishekSharma-17/skills-graph --skill ms-agent-framework
npx skills add AbhishekSharma-17/skills-graph --skill remotion-prompt-generator
npx skills add AbhishekSharma-17/skills-graph --skill trigger-dev
npx skills add AbhishekSharma-17/skills-graph --skill drizzle-orm
npx skills add AbhishekSharma-17/skills-graph --skill hono
npx skills add AbhishekSharma-17/skills-graph --skill zod
npx skills add AbhishekSharma-17/skills-graph --skill claude-agent-sdk

# Install globally (available across all projects)
npx skills add AbhishekSharma-17/skills-graph -g

# Search for any skill in the ecosystem
npx skills find
```

### Via Smithery

```bash
smithery install agno
```

### Via Install Script

```bash
# Interactive menu — pick which skills to install
./install/install-skills.sh

# Install all skills at once
./install/install-skills.sh --all

# Install a specific skill
./install/install-skills.sh --skill claude-agent-sdk

# See all available commands
./install/install-skills.sh --help
```

> See **[install/COMMANDS.md](install/COMMANDS.md)** for the full copy-paste command reference for every skill.

### Manual Install

Copy the skill folder to your platform's skill directory:

| Platform | Project Path | Global Path |
|:---------|:-------------|:------------|
| Claude Code | `.claude/skills/agno/` | `~/.claude/skills/agno/` |
| Gemini CLI | `.gemini/skills/agno/` | `~/.gemini/skills/agno/` |
| Cursor | `.cursor/skills/agno/` | `~/.cursor/skills/agno/` |
| Windsurf | `.windsurf/skills/agno/` | `~/.codeium/windsurf/skills/agno/` |
| Codex | `.codex/skills/agno/` | `~/.codex/skills/agno/` |
| Trae | `.trae/skills/agno/` | `~/.trae/skills/agno/` |
| Antigravity | `.agent/skills/agno/` | `~/.gemini/antigravity/skills/agno/` |

### Agno Native Integration

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills("/path/to/agno-skill")])
)
```

---

## Platform Compatibility

The Agent Skills standard (`SKILL.md` format) works on 25+ platforms with identical semantics.

| Platform | Type | Status |
|:---------|:-----|:------:|
| Claude Code | CLI | Full |
| Gemini CLI | CLI | Full |
| Cursor | IDE | Full |
| Windsurf | IDE | Full |
| Codex | CLI | Full |
| Trae | IDE | Full |
| Antigravity | IDE | Full |
| Amp | IDE | Full |
| Goose | CLI | Full |
| OpenCode | CLI | Full |
| GitHub Copilot | Extension | Partial |

---

## The Agent Skills Standard

Agent Skills is a universal format for extending AI coding assistants. Originally introduced in Claude Code (Oct 2025), went open Dec 2025, adopted by 25+ platforms.

1. `SKILL.md` with YAML frontmatter (`name` + `description`) as entry point
2. Optional `references/` for knowledge files
3. Optional `scripts/` for executable tools
4. 3-level loading: metadata (always) -> SKILL.md (on trigger) -> references (on demand)

Skills Graph builds on this by structuring references as an interconnected graph and adding version tracking, maintenance automation, and self-auditing -- practices that don't exist in the base spec.

---

## Maintenance & Tooling

```bash
# Full report
python skills/agno-skill/scripts/check-updates.py --report

# Individual checks
python skills/agno-skill/scripts/check-updates.py --version     # PyPI latest
python skills/agno-skill/scripts/check-updates.py --sitemap     # New doc pages
python skills/agno-skill/scripts/check-updates.py --stale 30    # Files older than 30 days
python skills/agno-skill/scripts/check-updates.py --integrity   # Verify routing table

# MS Agent Framework
python skills/ms-agent-framework/scripts/check-freshness.py --verbose

# Remotion Prompt Generator
python skills/remotion-prompt-generator/scripts/check-updates.py --report

# Trigger.dev
python skills/trigger-dev/scripts/check-updates.py --report
```

```
====== AGNO VERSION CHECK ======
Skill version:     1.2.0
Tracked Agno:      2.5.3
Latest on PyPI:    2.5.3
  UP TO DATE

====== FILE INTEGRITY ======
34 routing entries checked
116 reference files verified
0 broken references found
  ALL REFERENCES VALID
```

---

## Contributing

> **[Read the full Contributing Guide (CONTRIBUTING.md)](CONTRIBUTING.md)** -- complete standards, copy-paste templates, and step-by-step instructions for building a Skills Graph skill from scratch.

### Quick Summary

1. **Start with the router** -- `SKILL.md` with routing table and "Read When" conditions. Under 100 lines.
2. **Organize as a graph** -- Router files for complex topics, leaf files for focused content.
3. **Add intent-based navigation** -- Every entry tells the AI when to load that file.
4. **No frontmatter on references** -- Only `SKILL.md` gets YAML frontmatter.
5. **Track versions** -- `VERSION.json` with per-file metadata.
6. **Add maintenance scripts** -- Automate version checking and integrity validation.
7. **Audit yourself** -- `AUDIT-REPORT.md` with quality scorecard.

### Quality Checklist

- [ ] `SKILL.md` `name` exactly matches the folder name
- [ ] `SKILL.md` under 100 lines (pure router)
- [ ] Every reference reachable from routing table
- [ ] Router files have "Read When" / "Sub-References" tables
- [ ] Files >300 lines have TOC
- [ ] Files >500 lines split into router + sub-files
- [ ] `VERSION.json` tracks framework version + per-file metadata
- [ ] `CHANGELOG.md` documents all releases
- [ ] Maintenance script passes integrity checks
- [ ] `AUDIT-REPORT.md` exists with scorecard
- [ ] Description includes explicit trigger keywords

The full guide includes templates for every file (SKILL.md, VERSION.json, CHANGELOG.md, AUDIT-REPORT.md, check-updates.py), size rules, naming conventions, common mistakes, and production examples from both the Agno and MS Agent Framework skills.

---

## Author

**Abhishek Sharma**

---

## License

MIT License -- see [LICENSE](LICENSE).

Reference documentation is curated from frameworks under their own licenses:
**Agno** ([Apache 2.0](https://github.com/agno-agi/agno/blob/main/LICENSE)) &middot;
**MS Agent Framework** ([MIT](https://github.com/microsoft/agent-framework/blob/main/LICENSE))

---

## Acknowledgments

[Agno](https://github.com/agno-agi/agno) &middot;
[Microsoft Agent Framework](https://github.com/microsoft/agent-framework) &middot;
[Trigger.dev](https://github.com/triggerdotdev/trigger.dev) &middot;
[Agent Skills Standard](https://docs.anthropic.com) (Anthropic) &middot;
[Smithery](https://smithery.ai)
