<p align="center">
  <h1 align="center">Skills Graph</h1>
  <p align="center">
    <strong>Precision-engineered AI agent skills with interconnected reference architectures.</strong>
  </p>
  <p align="center">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
    <a href="#-the-agent-skills-standard"><img src="https://img.shields.io/badge/Agent%20Skills-Universal%20Standard-purple.svg" alt="Skills Standard"></a>
    <a href="#-platform-compatibility"><img src="https://img.shields.io/badge/Platforms-25%2B-green.svg" alt="Platforms"></a>
    <a href="#-available-skills"><img src="https://img.shields.io/badge/Skills-2%20Production%20Ready-orange.svg" alt="Skills"></a>
    <a href="#-the-technique-progressive-reference-architecture"><img src="https://img.shields.io/badge/Lines%20of%20Knowledge-37%2C000%2B-red.svg" alt="Lines"></a>
  </p>
</p>

---

<details>
<summary><strong>Table of Contents</strong></summary>

- [What is Skills Graph?](#-what-is-skills-graph)
- [The Problem with Current Skills](#-the-problem-with-current-skills)
- [Skills Graph vs. Conventional Skills — Side-by-Side](#-skills-graph-vs-conventional-skills--side-by-side)
- [The Technique: Progressive Reference Architecture](#-the-technique-progressive-reference-architecture)
- [Deep Dive: The Five Pillars of the Methodology](#-deep-dive-the-five-pillars-of-the-methodology)
- [How the Interconnected Graph Works](#-how-the-interconnected-graph-works)
- [Repository Structure](#-repository-structure)
- [Anatomy of a Skill](#-anatomy-of-a-skill)
- [Available Skills](#-available-skills)
- [Installation](#-installation)
- [Platform Compatibility](#-platform-compatibility)
- [The Agent Skills Standard](#-the-agent-skills-standard)
- [Maintenance & Tooling](#-maintenance--tooling)
- [Contributing](#-contributing)
- [Author](#-author)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

</details>

---

## Overview

> *"A 23,000-line knowledge base that costs the same as a 50-line skill — until you actually need it."*

Skills Graph is a methodology and collection of production-grade AI agent skills built using a technique called **Progressive Reference Architecture (PRA)** — a systematic approach to creating deeply interconnected, graph-structured knowledge bases that AI coding assistants can navigate with surgical precision.

Instead of dumping documentation into a single monolithic file or a flat folder of loosely related references, Skills Graph organizes knowledge as a **directed acyclic graph (DAG)** where every reference file is a node, every cross-reference is an edge, and a lightweight router sits at the root to guide the AI to exactly the information it needs — nothing more, nothing less.

### At a Glance

| | |
|---|---|
| **Skills** | 2 production-ready (Agno, MS Agent Framework) |
| **Total Knowledge** | 37,000+ lines across 177 reference files |
| **Router Overhead** | 69–231 lines (the only cost when skill triggers) |
| **Context Efficiency** | ~97% reduction vs monolithic approach |
| **Platform Support** | 25+ AI coding assistants |
| **Maintenance** | Automated version checking, staleness detection, integrity validation |

---

## The Problem with Current Skills

Most AI agent skills today are built in one of two broken patterns:

### Pattern 1: The Monolith

```
my-skill/
└── SKILL.md          # 3,000-5,000+ lines of everything
```

- The AI loads the **entire file** into context every time the skill triggers
- A simple question like "how do I create a tool?" forces the AI to wade through 5,000 lines
- Token budget is consumed by irrelevant content (deployment docs when the user asked about memory)
- Response quality degrades because the signal-to-noise ratio is terrible
- Common in: early Claude Code skills, Cursor rules, most community skills

### Pattern 2: The Flat Dump

```
my-skill/
├── SKILL.md            # Brief overview
├── references/
│   ├── agents.md       # No structure
│   ├── tools.md        # No structure
│   ├── memory.md       # No structure
│   ├── database.md     # No structure
│   └── ... 40 more files with no navigation
```

- Files exist but the AI has **no guidance** on which one to read
- The AI guesses based on filename alone — often wrong
- No hierarchical organization — a file on "tools" might be 800 lines covering 11 different sub-topics
- No "Read When" conditions — the AI loads files speculatively, wasting tokens
- Common in: documentation dumps, auto-generated skills

### Pattern 3: The Copy-Paste

```
my-skill/
└── SKILL.md            # 500 lines of cherry-picked docs
```

- Someone copies fragments from official documentation
- No version tracking — content drifts from the source immediately
- No update mechanism — stale within weeks
- Missing context — the fragments don't cover edge cases or advanced patterns
- Common in: quick community contributions, personal snippets

### What all three patterns share

- No version tracking against the upstream framework
- No automated staleness detection
- No integrity validation (routing table points to files that don't exist)
- No self-audit mechanism
- No cross-platform awareness

---

## Skills Graph vs. Conventional Skills — Side-by-Side

### Architecture Comparison

| Dimension | Conventional Skill | Skills Graph Skill |
|-----------|-------------------|-------------------|
| **Structure** | Single file or flat folder | Hierarchical DAG with router nodes |
| **Entry Point** | `SKILL.md` (often 500-5,000 lines) | `SKILL.md` (69-231 lines, pure router) |
| **Navigation** | None (AI guesses) or basic headings | Routing tables with "Read When" conditions |
| **Reference Organization** | Flat list of files | Graph: routers branch to sub-references |
| **Loading Strategy** | All-or-nothing | Progressive: metadata, router, then specific leaf |
| **Depth of Knowledge** | Shallow (limited by file size) | Deep (unlimited — leaf files expand the graph) |
| **Cross-References** | None | Explicit via Sub-Reference tables |
| **YAML Frontmatter** | Sometimes on every file | Only on `SKILL.md` (correct per spec) |

### Token Economics

| Scenario | Conventional (Monolith) | Conventional (Flat) | Skills Graph |
|----------|------------------------|--------------------|----|
| Skill sits idle (not triggered) | ~100 tokens (description) | ~100 tokens | ~100 tokens |
| Skill triggers (any query) | **~5,000 tokens** (full file) | ~500 tokens (SKILL.md) | ~500 tokens (router) |
| Simple question ("how do I create an agent?") | **~5,000 tokens** | ~800 tokens (1 file, maybe wrong) | **~700 tokens** (router + 1 leaf) |
| Moderate question ("set up memory with Postgres") | **~5,000 tokens** | ~1,500 tokens (2-3 files, guessing) | **~900 tokens** (router + router + 1 leaf) |
| Complex question ("build a RAG pipeline with guardrails") | **~5,000 tokens** | ~3,000 tokens (5+ files) | **~1,200 tokens** (2 precise paths) |
| Total knowledge available | 5,000 lines max | Varies, no guarantees | **37,000+ lines** on demand |

**Key insight:** Skills Graph skills carry 7x more knowledge while using 4-7x fewer tokens per query.

### Maintenance Comparison

| Capability | Conventional Skill | Skills Graph Skill |
|------------|-------------------|-------------------|
| Version tracking | None | `VERSION.json` with semantic versioning |
| Framework version pinning | None | Per-file `written_for` metadata |
| Staleness detection | Manual | Automated (`--stale` flag, configurable threshold) |
| Integrity validation | None | Automated (`--integrity` verifies routing table) |
| Upstream change detection | None | PyPI version check + docs sitemap diffing |
| Changelog | Rarely | Structured `CHANGELOG.md` with categories |
| Architecture audit | Never | `AUDIT-REPORT.md` with scorecard |
| Update script | None | Full CLI tool with `--report` mode |

### Quality Comparison

| Quality Metric | Conventional Skill | Skills Graph Skill |
|---------------|-------------------|-------------------|
| Navigation accuracy | Low-Medium (AI guesses) | High (guided by "Read When" conditions) |
| Response relevance | Diluted by irrelevant context | Focused (only relevant knowledge loaded) |
| Coverage completeness | Partial (limited by size) | Comprehensive (unlimited reference depth) |
| Scalability | Degrades at >500 lines | Proven at 23,431 lines, scales further |
| Cross-platform | Usually single-platform | 25+ platforms, tested compatibility matrix |
| Self-documenting | No | AUDIT-REPORT.md, VERSION.json, CHANGELOG.md |

---

## The Technique: Progressive Reference Architecture

Progressive Reference Architecture (PRA) is the core methodology behind Skills Graph. It is built on a single principle: **the AI should pay only for the knowledge it actually uses**.

### The 3-Level Progressive Loading System

```
                    ALWAYS IN CONTEXT
                    ┌─────────────────────────┐
  Level 1           │  YAML Metadata          │  ~100 tokens
  (Metadata)        │  name + description     │  Same cost whether skill
                    │  + trigger keywords     │  has 5 files or 500
                    └────────────┬────────────┘
                                 │
                    LOADED WHEN SKILL TRIGGERS
                    ┌────────────┴────────────┐
  Level 2           │  SKILL.md Router Body   │  ~500 tokens
  (Router)          │  Routing table with     │  Maps intent → file
                    │  "Read When" conditions │  34 routes in 69 lines
                    └────────────┬────────────┘
                                 │
                    LOADED ON DEMAND (specific path only)
                    ┌────────────┴────────────┐
  Level 3           │  Reference Graph        │  ~200-400 tokens per node
  (References)      │  Router nodes → Leaves  │  Only the relevant path
                    │  116 files, 23,431 lines│  is ever loaded
                    └─────────────────────────┘
```

#### Level 1: Metadata (Always Loaded)

```yaml
---
name: agno
description: "Build AI agents, multi-agent teams, and agentic workflows
  using the Agno framework. MANDATORY TRIGGERS: Agno, agno-agi, AgentOS..."
license: MIT
metadata:
  version: "1.2.0"
  author: Abhishek Sharma
  tags: ["agno", "ai-agents", "multi-agent", "agentos", "rag", "workflows"]
---
```

The YAML frontmatter is the only thing always present in the AI's context. It contains:
- **Name** — lowercase identifier for discovery
- **Description** — carefully crafted with explicit trigger keywords and "MANDATORY TRIGGERS" directive
- **License** — SPDX identifier
- **Metadata** — version, author, tags for marketplace discovery

Cost: ~100 tokens. Identical whether the skill has 5 reference files or 500.

#### Level 2: Router (Loaded on Trigger)

```markdown
| Reference | File | Read When |
|-----------|------|-----------|
| **Agents** | `references/agents.md` | Creating agents, tools, structured output... |
| **Teams** | `references/teams.md` | Multi-agent coordination, team modes... |
| **Memory** | `references/memory.md` | Automatic vs agentic memory, MemoryManager... |
```

When the skill triggers, the AI loads `SKILL.md` — a lean routing table that maps user intent to specific reference files. The "Read When" column is the critical innovation: it gives the AI precise, unambiguous guidance on which file to load for any given query. Cost: ~500 tokens.

#### Level 3: Reference Graph (Loaded on Demand)

The reference layer is organized as a graph, not a flat list. Two types of nodes:

- **Router nodes** — intermediate files containing a Sub-Reference table that further narrows the search
- **Leaf nodes** — terminal files containing the actual knowledge (code examples, API patterns, configuration)

The AI navigates from root (SKILL.md) through router nodes to the specific leaf, loading only the path relevant to the current query.

---

## Deep Dive: The Five Pillars of the Methodology

### Pillar 1: Intent-Based Routing

Every navigation decision in Skills Graph is driven by user intent, not by file naming conventions or alphabetical ordering.

**The "Read When" column** is the most important element in the entire architecture. It maps natural language intent to specific files:

```markdown
| Reference | File | Read When |
|-----------|------|-----------|
| **Knowledge** | `references/knowledge.md` | RAG pipelines, vector databases, embedders, readers, chunking strategies, search types, filtering, reranking |
```

This means when a user asks "how do I set up a RAG pipeline with Pinecone?", the AI doesn't need to guess — it sees "RAG pipelines, vector databases" in the Read When column and loads `knowledge.md` directly.

For router nodes, the pattern repeats at a deeper level with Sub-Reference tables:

```markdown
## Sub-References

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **Backends** | `database/backends.md` | Setting up PostgreSQL, MongoDB, Redis... |
| **Chat History** | `database/chat-history.md` | Enabling multi-turn context... |
| **Sessions & Memory** | `database/session-memory.md` | Automatic vs agentic memory... |
```

The result: **two levels of intent matching** before the AI ever reads content, ensuring it lands on the right 200-400 lines out of 23,000+.

### Pillar 2: Hierarchical Decomposition

Large topics are recursively split into manageable sub-topics using the **router + sub-files** pattern:

```
tools.md (router — 56 lines)
├── tools/creating-tools.md        (leaf — tool functions, @tool decorator)
├── tools/custom-toolkits.md       (leaf — reusable Toolkit classes)
├── tools/advanced.md              (leaf — hooks, caching, RunContext)
├── tools/mcp-tools.md             (leaf — Model Context Protocol)
├── tools/builtin-search.md        (leaf — DuckDuckGo, Tavily, Exa...)
├── tools/builtin-data.md          (leaf — SQL, Pandas, BigQuery...)
├── tools/builtin-web.md           (leaf — Firecrawl, Crawl4AI, Spider...)
├── tools/builtin-dev.md           (leaf — GitHub, Docker, Shell...)
├── tools/builtin-comms.md         (leaf — Email, Slack, Discord...)
├── tools/builtin-media.md         (leaf — DALL-E, ElevenLabs...)
└── tools/builtin-productivity.md  (leaf — Google Calendar, Notion...)
```

**The splitting rules:**
- Files over **500 lines** must be split into router + sub-files
- Files over **300 lines** must have a table of contents
- Router files should be under **100 lines** — just enough context to route correctly
- Leaf files should be **200-500 lines** — focused, self-contained knowledge units

This ensures no single file overwhelms the AI's context while maintaining complete coverage.

### Pillar 3: Zero-Cost Idle State

A critical property of Skills Graph skills: **they cost nothing when idle**.

The only always-loaded component is the YAML description (~100 tokens). This means:
- A 50-line skill and a 23,431-line skill have identical idle cost
- Skills can be massively comprehensive without penalizing users who don't need them
- You can install dozens of Skills Graph skills without bloating your AI's context

This is fundamentally different from monolithic skills where installing a 5,000-line skill permanently consumes 5,000 tokens of context budget every time the skill triggers, regardless of the query.

### Pillar 4: Version-Aware Maintenance

Every Skills Graph skill tracks versions at three levels:

1. **Skill version** — semantic versioning of the skill itself (e.g., v1.2.0)
2. **Framework version** — the upstream framework version being tracked (e.g., Agno 2.5.3)
3. **Per-file version** — which framework version each reference was written for

```json
{
  "skill_version": "1.2.0",
  "agno_version_tracked": "2.5.3",
  "references": {
    "agents.md": { "written_for": "2.5.2", "last_updated": "2026-02-18" },
    "evals.md": { "written_for": "2.5.3", "last_updated": "2026-02-21" },
    "hooks.md": { "written_for": "2.5.3", "last_updated": "2026-02-21" }
  }
}
```

This enables:
- **Targeted updates** — when Agno 2.6.0 releases, you know exactly which files were written for 2.5.2 and might need updates
- **Staleness detection** — automated scripts flag files that haven't been updated in N days
- **Integrity validation** — verify every routing table entry has a corresponding file on disk

### Pillar 5: Self-Auditing Architecture

Every Skills Graph skill includes an `AUDIT-REPORT.md` — a structured self-assessment that scores the skill across quality dimensions:

| Category | Score | Notes |
|----------|-------|-------|
| SKILL.md size | 5/5 | 69 lines — exemplary lean router |
| Progressive disclosure | 4/5 | Great router pattern, few oversized flat files |
| Reference splitting | 4/5 | Most topics well-split |
| YAML frontmatter | 5/5 | Correct placement, correct fields |
| TOC on large files | 4/5 | Added to all files >300 lines |
| Description triggering | 4/5 | Explicit MANDATORY TRIGGERS |
| Tooling & maintenance | 5/5 | VERSION.json + updater + changelog |

The audit report also includes:
- Comparison with exemplary skills from the ecosystem
- Cross-platform compatibility analysis
- Prioritized improvement action plan

---

## How the Interconnected Graph Works

The key differentiator of Skills Graph is that reference files are not independent documents — they form an interconnected knowledge graph with explicit navigation paths.

### Router Pattern

Every complex topic uses a **router file** that acts as a table of contents with conditional loading guidance:

```markdown
# Agno Memory

Memory stores learned user facts that persist across sessions.

## Sub-References

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **Core Concepts** | `memory/core-concepts.md` | Understanding automatic vs agentic memory... |
| **Tools & Manager** | `memory/tools-manager.md` | MemoryTools, MemoryManager, sharing memory... |
| **Patterns** | `memory/patterns-best-practices.md` | Teams with memory, multi-user, optimization... |

## Quick Start
[minimal code example — enough for simple cases without loading sub-references]
```

The router file itself contains enough context (quick start, key parameters) for simple queries, while the Sub-Reference table guides the AI deeper for complex queries.

### Navigation Flow Example

```
User: "How do I add persistent memory to my Agno agent with Postgres?"

  Step 1 ─ SKILL.md metadata (always in context)
           AI sees "agno" in user's stack → skill triggers
           Cost: 0 additional tokens (already loaded)

  Step 2 ─ SKILL.md routing table loads
           AI scans 34 routes, finds:
           Memory → references/memory.md → "Automatic vs agentic memory..."
           Database → references/database.md → "All storage backends, Postgres..."
           Cost: +500 tokens

  Step 3 ─ AI reads references/memory.md (router node)
           Sees Sub-References table, decides: "Core Concepts" matches
           Also sees Quick Start with basic memory setup
           Cost: +200 tokens

  Step 4 ─ AI reads memory/core-concepts.md (leaf node)
           Gets detailed memory setup with database configuration
           Cost: +350 tokens

  Total: ~1,050 tokens loaded out of 23,431 available (4.5%)
```

### Dependency Graph Visualization

```
                            SKILL.md
                          (34 routes)
                               │
         ┌─────────────┬───────┼───────┬──────────────┐
         │             │       │       │              │
    Foundation    Execution    │   State & Memory   Safety
    ┌────┴───┐   ┌────┴───┐   │   ┌────┴────┐    ┌───┴───┐
  agents   teams tools/  models│  memory/ database/ guardrails/
  (leaf)  (leaf) (router)(leaf)│  (router)(router)  (router)
                   │           │     │       │         │
           ┌───────┼─────┐    │  ┌──┼──┐  ┌─┼──┐   ┌──┼──┐
        creating custom  MCP  │ core tools backends builtin
        (leaf)  kits   (leaf) │ (leaf)(leaf)(leaf)  (leaf)
               (leaf)         │
                 │            │        Production
         ┌───────┼──────┐    │     ┌─────┴──────┐
      search    data   web   │   agentos/     deploy
      (leaf)   (leaf) (leaf) │   (router)     (leaf)
                             │      │
       ...6 more builtin     │   ┌──┼──┐
          categories         │  setup config
                             │  (leaf)(leaf)
                             │
                        Knowledge & Learning
                       ┌─────┴──────┐
                    knowledge    learning
                     (leaf)      (leaf)
```

Each path from root to leaf represents a possible navigation sequence. The AI never loads sibling branches — only the path relevant to the current query.

---

## Repository Structure

```
skills-graph/
├── README.md                           # This file
├── LICENSE                             # MIT License
│
├── agno-skill/                         # Agno Framework skill (v1.2.0)
│   ├── SKILL.md                        # Router — 69 lines, 34 routing entries
│   ├── VERSION.json                    # Machine-readable version tracking
│   ├── CHANGELOG.md                    # Release history (v1.0.0 → v1.2.0)
│   ├── AUDIT-REPORT.md                 # Architecture audit & cross-platform analysis
│   ├── scripts/
│   │   └── check-updates.py            # PyPI checker, staleness, integrity
│   └── references/                     # 116 files, ~23,431 lines
│       ├── agents.md                   #   Agent creation, tools, state
│       ├── teams.md                    #   Multi-agent coordination
│       ├── workflows.md               #   Pipeline orchestration
│       ├── tools.md → tools/           #   Router → 11 sub-files (120+ builtins)
│       ├── memory.md → memory/         #   Router → 3 sub-files
│       ├── database.md → database/     #   Router → 3 sub-files (18 backends)
│       ├── knowledge.md                #   RAG, 14+ vector DBs, 12+ embedders
│       ├── guardrails.md → guardrails/ #   Router → 3 sub-files
│       ├── hooks.md → hooks/           #   Router → 2 sub-files
│       ├── context-mgmt.md → context-mgmt/ # Router → 5 sub-files
│       ├── agentos.md → agentos/       #   Router → 2 sub-files (50+ APIs)
│       ├── evals.md → evals/           #   Router → 4 sub-files
│       ├── models.md                   #   40+ model providers
│       ├── reasoning.md                #   Reasoning models, tools, agents
│       ├── multimodal.md               #   Image, audio, video handling
│       ├── deploy.md                   #   Docker, Railway, AWS ECS
│       └── ... (30+ more topic files)
│
└── ms-agent-framework/                 # MS Agent Framework skill (v2.0.0)
    ├── SKILL.md                        # Router — 231 lines, 109 routing entries
    ├── metadata/
    │   ├── version-tracking.json       # Version history with timestamps
    │   └── sources.json                # Per-file source URL mapping
    ├── scripts/
    │   └── check-freshness.py          # 7 validation checks
    └── references/                     # 61 files, ~14,000 lines
        ├── 01–10                       #   Core foundations (10 files)
        ├── 11–11l                      #   Workflow deep-dive (13 files)
        ├── 12a–12e                     #   Orchestration patterns (5 files)
        ├── 13–23                       #   Deployment, security, patterns (14 files)
        └── legacy wrappers             #   Backwards-compatible aliases (12 files)
```

---

## Anatomy of a Skill

Every skill in Skills Graph follows a standardized structure with six core components:

### 1. `SKILL.md` — The Router

The only file with YAML frontmatter. Contains the routing table that maps user intent to reference files. Kept deliberately lean (under 100 lines) to minimize context cost when the skill triggers. Includes install instructions and version summary.

### 2. `references/` — The Knowledge Graph

Markdown files organized as a directed graph. Two types of nodes:
- **Router nodes** — contain a Sub-Reference table pointing to child files, plus a Quick Start for simple queries
- **Leaf nodes** — contain the actual knowledge (code examples, API docs, configuration patterns)

No reference file has YAML frontmatter. This is by design — frontmatter is only needed for skill discovery, not for reference loading.

### 3. `VERSION.json` — Version Tracking

Machine-readable metadata tracking:
- Skill version (semantic versioning)
- Framework version being tracked (e.g., Agno 2.5.3)
- Per-file metadata: which framework version each reference was written for, last update date
- Documentation sitemap: all known doc pages for diffing against new releases
- Statistics: routing entries, reference files, total lines

### 4. `CHANGELOG.md` — Release History

Human-readable release notes following Keep a Changelog conventions. Documents what changed in each version with categories: Added, Changed, Split, Fixed, Stats.

### 5. `scripts/` — Maintenance Automation

Python scripts for automated maintenance:
- **Version checking** — compare tracked version against PyPI/GitHub latest
- **Sitemap diffing** — detect new documentation pages
- **Staleness detection** — flag reference files older than a configurable threshold
- **Integrity validation** — verify all routing table entries have corresponding files on disk

### 6. `AUDIT-REPORT.md` — Architecture Quality

Self-assessment document analyzing the skill against best practices:
- Progressive disclosure compliance scoring
- Comparison with exemplary skills from the ecosystem
- Cross-platform compatibility matrix
- Prioritized improvement action plan

---

## Available Skills

### Agno Framework (v1.2.0)

Full-coverage skill for the [Agno](https://github.com/agno-agi/agno) open-source agent framework.

| Metric | Value |
|--------|-------|
| Routing Entries | 34 |
| Reference Files | 116 |
| Total Lines | 23,431 |
| Framework Version Tracked | Agno 2.5.3 |
| Router Nodes | 12 (tools, memory, database, guardrails, hooks, context-mgmt, agentos, evals, tracing, workflow-patterns, input-output, agno-skills) |
| Leaf Nodes | 104 |

**Coverage:** Agents, Teams, Workflows, Tools (120+ builtins), Models (40+ providers), Database (18 backends), Memory, Knowledge/RAG (14+ vector DBs, 12+ embedders), Learning, Guardrails, Human-in-the-Loop, Evals, Hooks, Tracing, Context Management, AgentOS (50+ API endpoints), Multimodal, Reasoning, Deploy, Observability (12 platforms), Integrations, Migrations, Culture, Custom Logging, FAQs.

### Microsoft Agent Framework (v2.0.0)

Full-coverage skill for [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (Python).

| Metric | Value |
|--------|-------|
| Routing Entries | 109 (63 explicit + 46 fuzzy) |
| Reference Files | 61 |
| Total Lines | ~14,000 |
| Framework Version Tracked | 1.0.0b260130 (Public Preview) |

**Coverage:** Agents, Running Agents, Structured Output, Tools (function + hosted + MCP), RAG, Sessions, Memory, Middleware, Providers (6), Workflows (13 deep-dive files), Orchestration (sequential, concurrent, handoff, group chat, magentic), Deployment (Azure Functions, A2A, AG-UI), Observability, Security, Purview Governance, M365 Integration, Design Patterns (core + advanced).

---

## Installation

Skills Graph skills work with any AI coding assistant that supports the Agent Skills standard.

### Quick Install (Smithery)

```bash
# Install a skill via the Smithery marketplace
smithery install agno
```

### Manual Install

Copy the skill folder to your platform's skill directory:

| Platform | Project-Level Path | Global Path |
|----------|-------------------|-------------|
| Claude Code | `.claude/skills/agno/` | `~/.claude/skills/agno/` |
| Gemini CLI | `.gemini/skills/agno/` | `~/.gemini/skills/agno/` |
| Cursor | `.cursor/skills/agno/` | `~/.cursor/skills/agno/` |
| Windsurf | `.windsurf/skills/agno/` | `~/.codeium/windsurf/skills/agno/` |
| Codex | `.codex/skills/agno/` | `~/.codex/skills/agno/` |
| Trae | `.trae/skills/agno/` | `~/.trae/skills/agno/` |
| Antigravity | `.agent/skills/agno/` | `~/.gemini/antigravity/skills/agno/` |

### Agno Native Integration

Agno has first-class skills support (v2.5+). Load skills directly from code:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills("/path/to/agno-skill")])
)
# Agent automatically gets: get_skill_instructions(), get_skill_reference(), get_skill_script()
```

---

## Platform Compatibility

The Agent Skills standard (`SKILL.md` format) is supported by 25+ AI coding platforms. All platforms use the same discovery/activation/execution pattern: scan descriptions, load `SKILL.md` on match, read references on demand.

| Platform | Type | Compatibility |
|----------|------|:---:|
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

Agent Skills is a universal format for extending AI coding assistants with domain-specific knowledge. Originally introduced in Claude Code (October 2025), the format went open in December 2025 and has since been adopted by 25+ platforms.

The standard defines:

1. A `SKILL.md` file with YAML frontmatter (`name` + `description`) as the entry point
2. Optional `references/` directory for additional knowledge files
3. Optional `scripts/` directory for executable tools
4. A 3-level loading model: metadata (always) → SKILL.md (on trigger) → references (on demand)

Skills Graph builds on this standard by introducing a disciplined methodology for structuring the reference layer as an interconnected graph rather than a flat collection of files, and adding version tracking, maintenance automation, and self-auditing practices that don't exist in the base specification.

---

## Maintenance & Tooling

### Checking for Updates

Each skill includes a maintenance script that validates freshness and integrity:

```bash
# Agno skill — full report
python agno-skill/scripts/check-updates.py --report

# Individual checks
python agno-skill/scripts/check-updates.py --version     # Compare against PyPI latest
python agno-skill/scripts/check-updates.py --sitemap     # Detect new doc pages
python agno-skill/scripts/check-updates.py --stale 30    # Files older than 30 days
python agno-skill/scripts/check-updates.py --integrity   # Verify routing table

# Microsoft Agent Framework skill
python ms-agent-framework/scripts/check-freshness.py --verbose
```

### Example Output

```
====== AGNO VERSION CHECK ======
Skill version:     1.2.0
Tracked Agno:      2.5.3
Docs snapshot:     2026-02-21
Latest on PyPI:    2.5.3
  UP TO DATE — skill tracks the latest version

====== FILE INTEGRITY ======
34 routing entries checked
116 reference files verified
0 broken references found
  ALL REFERENCES VALID
```

### Version Tracking

Every skill maintains a `VERSION.json` with:
- Skill version and framework version tracked
- Per-file metadata (which framework version each reference targets, last updated date)
- Documentation sitemap for diffing new releases
- Aggregate statistics (routing entries, files, lines)

---

## Contributing

Contributions are welcome. Whether you want to improve existing skills or create new ones, here's how to participate.

### Creating a New Skill

Follow the Skills Graph methodology:

1. **Start with the router** — Write `SKILL.md` with a clear routing table and "Read When" conditions. Keep it under 100 lines.
2. **Organize references as a graph** — Use router files for complex topics (5+ sub-topics) and leaf files for focused content.
3. **Add intent-based navigation** — Every routing entry tells the AI exactly when to load that file.
4. **No frontmatter on references** — Only `SKILL.md` gets YAML frontmatter.
5. **Track versions** — Create a `VERSION.json` with per-file metadata.
6. **Add maintenance scripts** — Automate version checking, staleness detection, and integrity validation.
7. **Audit yourself** — Write an `AUDIT-REPORT.md` scoring your skill against the five pillars.

### Quality Checklist

- [ ] `SKILL.md` is under 100 lines (pure router)
- [ ] Every reference file is reachable from the routing table
- [ ] Router files have "Read When" / "Sub-References" tables
- [ ] Files over 300 lines have a table of contents
- [ ] Files over 500 lines are split into router + sub-files
- [ ] `VERSION.json` tracks framework version and per-file metadata
- [ ] `CHANGELOG.md` documents all releases
- [ ] Maintenance script passes all integrity checks
- [ ] `AUDIT-REPORT.md` exists with quality scorecard
- [ ] Description includes explicit trigger keywords

---

## Author

**Abhishek Sharma**

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

The skills in this repository contain curated reference documentation for their respective frameworks. The original framework documentation is subject to its own licensing:

- **Agno** — [Apache 2.0](https://github.com/agno-agi/agno/blob/main/LICENSE)
- **Microsoft Agent Framework** — [MIT](https://github.com/microsoft/agent-framework/blob/main/LICENSE)

---

## Acknowledgments

- [Agno](https://github.com/agno-agi/agno) — Open-source agent framework by Agno AGI
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) — AI agent framework by Microsoft
- The Agent Skills standard — Originally by Anthropic (Claude Code), now a universal format across 25+ platforms
- [Smithery](https://smithery.ai) — Skills marketplace for distribution
