# Skills Graph

**Precision-engineered AI agent skills with interconnected reference architectures.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skills Standard](https://img.shields.io/badge/Agent%20Skills-Universal%20Standard-purple.svg)](#the-agent-skills-standard)
[![Platforms](https://img.shields.io/badge/Platforms-25%2B-green.svg)](#platform-compatibility)

---

## What is Skills Graph?

Skills Graph is a methodology and collection of production-grade AI agent skills built using a technique called **Progressive Reference Architecture** — a systematic approach to creating deeply interconnected, graph-structured knowledge bases that AI coding assistants can navigate with surgical precision.

Instead of dumping documentation into a single monolithic file or a flat folder of loosely related references, Skills Graph organizes knowledge as a **directed acyclic graph (DAG)** where every reference file is a node, every cross-reference is an edge, and a lightweight router sits at the root to guide the AI to exactly the information it needs — nothing more, nothing less.

The result: a 23,000+ line knowledge base that costs the same as a 50-line skill until the AI actually needs help, at which point it loads only the 200-400 lines relevant to the current task.

---

## The Technique: Progressive Reference Architecture

Most AI skills fall into two traps:

1. **The Monolith** — Everything in one massive file. The AI loads 5,000+ lines of context when the user asks a simple question, wasting tokens and degrading response quality.
2. **The Flat Dump** — Dozens of unrelated files with no navigation structure. The AI doesn't know which file to read and either guesses wrong or reads too many.

Skills Graph solves both problems with a **3-level progressive loading system**:

### Level 1: Metadata (Always Loaded)

```yaml
---
name: agno
description: "Build AI agents, multi-agent teams, and agentic workflows..."
---
```

The YAML frontmatter is the only thing always present in the AI's context. It contains the skill name and a carefully crafted description with explicit trigger keywords. Cost: ~100 tokens. This is identical whether the skill has 5 reference files or 500.

### Level 2: Router (Loaded on Trigger)

```markdown
| Reference | File | Read When |
|-----------|------|-----------|
| **Agents** | `references/agents.md` | Creating agents, tools, structured output... |
| **Teams** | `references/teams.md` | Multi-agent coordination, team modes... |
| **Memory** | `references/memory.md` | Automatic vs agentic memory, MemoryManager... |
```

When the skill triggers, the AI loads `SKILL.md` — a lean routing table (69 lines for 34 topics) that maps user intent to specific reference files. The "Read When" column gives the AI precise guidance on which file to load. Cost: ~500 tokens.

### Level 3: Reference Graph (Loaded on Demand)

```
references/
├── tools.md (router)          ──→ tools/creating-tools.md
│                               ──→ tools/custom-toolkits.md
│                               ──→ tools/advanced.md
│                               ──→ tools/mcp-tools.md
│                               ──→ tools/builtin-search.md
│                               ──→ tools/builtin-data.md
│                               ──→ tools/builtin-web.md
│                               └──→ tools/builtin-media.md
├── memory.md (router)         ──→ memory/core-concepts.md
│                               ──→ memory/tools-manager.md
│                               └──→ memory/patterns-best-practices.md
├── database.md (router)       ──→ database/backends.md
│                               ──→ database/chat-history.md
│                               └──→ database/session-memory.md
└── agents.md (leaf)            [self-contained, 470 lines]
```

Reference files form a **graph**, not a list. Router files act as intermediate nodes that further narrow the search space. Leaf files contain the actual knowledge. The AI navigates this graph by reading only what it needs: first the router, then the specific sub-reference.

### Why This Matters

| Approach | Context Cost (Simple Query) | Context Cost (Complex Query) | Navigation Accuracy |
|----------|---------------------------|----------------------------|-------------------|
| Monolith (5,000 lines) | 5,000 tokens | 5,000 tokens | Low (buried in noise) |
| Flat files (50 files) | ~1,000 tokens (wrong file) | ~3,000 tokens (multiple files) | Medium |
| **Skills Graph** | **~700 tokens** | **~1,200 tokens** | **High (guided routing)** |

The progressive architecture means the AI pays only for what it uses, and the routing table ensures it finds the right information on the first try.

---

## Repository Structure

```
skills-graph/
├── README.md                     # This file
├── LICENSE                       # MIT License
│
├── agno-skill/                   # Agno Framework skill (v1.2.0)
│   ├── SKILL.md                  # Router — 69 lines, 34 routing entries
│   ├── VERSION.json              # Machine-readable version tracking
│   ├── CHANGELOG.md              # Release history
│   ├── AUDIT-REPORT.md           # Architecture audit and cross-platform analysis
│   ├── scripts/
│   │   └── check-updates.py      # PyPI version checker, staleness detection, integrity validation
│   └── references/               # 116 files, ~23,431 lines
│       ├── agents.md             # Agent creation, tools, state, streaming
│       ├── teams.md              # Multi-agent coordination
│       ├── workflows.md          # Pipeline orchestration
│       ├── tools.md              # Router → tools/ (11 sub-files)
│       ├── tools/                # Creating tools, toolkits, 120+ builtins by category
│       ├── memory.md             # Router → memory/ (3 sub-files)
│       ├── memory/               # Core concepts, tools/manager, best practices
│       ├── database.md           # Router → database/ (3 sub-files)
│       ├── database/             # Backends, chat history, session memory
│       ├── knowledge.md          # RAG, vector DBs, embedders, chunking
│       ├── guardrails.md         # Router → guardrails/ (3 sub-files)
│       ├── guardrails/           # PII, prompt injection, custom guardrails
│       ├── hooks.md              # Router → hooks/ (2 sub-files)
│       ├── context-mgmt.md       # Router → context-mgmt/ (5 sub-files)
│       ├── agentos.md            # Router → agentos/ (2 sub-files)
│       ├── evals.md              # Router → evals/ (4 sub-files)
│       ├── models.md             # 40+ model providers
│       ├── reasoning.md          # Reasoning models, tools, agents
│       ├── multimodal.md         # Image, audio, video handling
│       ├── deploy.md             # Docker, Railway, AWS ECS templates
│       └── ... (30+ more topic files)
│
└── ms-agent-framework/           # Microsoft Agent Framework skill (v2.0.0)
    ├── SKILL.md                  # Router — 231 lines, 109 routing entries
    ├── metadata/
    │   ├── version-tracking.json # Version history with timestamps
    │   └── sources.json          # Per-file source URL mapping
    ├── scripts/
    │   └── check-freshness.py    # PyPI/GitHub checker, 7 validation checks
    └── references/               # 61 files, ~14,000 lines
        ├── 01-getting-started.md # → 10 core foundation files
        ├── 11-workflows-core.md  # → 13 workflow deep-dive files (11a-11l)
        ├── 12a-orchestration-sequential.md  # → 5 orchestration patterns
        ├── 13-deployment.md      # → 9 deployment & integration files
        ├── 22-design-patterns-core.md       # → 2 design pattern files
        └── ... (61 total reference files)
```

---

## How the Interconnected Graph Works

The key differentiator of Skills Graph is that reference files are not independent documents — they form an interconnected knowledge graph with explicit navigation paths.

### Router Pattern

Every complex topic uses a **router file** that acts as a table of contents with conditional loading guidance:

```markdown
# Agno Tools — Reference Router

## Sub-References

| Reference | File | Read When |
|-----------|------|-----------|
| **Creating Tools** | `tools/creating-tools.md` | Writing tool functions, @tool decorator... |
| **Custom Toolkits** | `tools/custom-toolkits.md` | Building reusable Toolkit classes... |
| **Advanced Patterns** | `tools/advanced.md` | Tool hooks, RunContext, caching... |
| **MCP Tools** | `tools/mcp-tools.md` | Model Context Protocol integration... |
| **Search Toolkits** | `tools/builtin-search.md` | DuckDuckGo, Tavily, Exa, SerpAPI... |
```

The "Read When" column is the navigation intelligence — it tells the AI exactly which sub-reference to load based on the user's specific question.

### Navigation Flow

```
User: "How do I add memory to my Agno agent?"

  1. AI reads SKILL.md metadata (always in context)     → triggers skill
  2. AI reads SKILL.md routing table                     → finds "Memory" row
  3. AI reads references/memory.md (router)              → sees 3 sub-references
  4. AI reads memory/core-concepts.md                    → answers the question

Total context loaded: ~700 tokens (out of 23,431 available)
```

### Dependency Graph Visualization

```
                        SKILL.md (34 routes)
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
     Foundation          Execution          State & Memory
    ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
  agents   teams   tools/     models   memory/  database/
  (leaf)   (leaf)  (router)   (leaf)   (router) (router)
                      │                   │         │
              ┌───────┼──────┐        ┌───┼───┐   ┌─┼──┐
           creating  custom  MCP    core tools  backends
           (leaf)   toolkits (leaf) (leaf)(leaf) (leaf)
                    (leaf)
                      │
              ┌───────┼──────────┐
           search    data      web     ...6 more
           (leaf)   (leaf)   (leaf)    builtin categories
```

Each path from root to leaf represents a possible navigation sequence. The AI never loads sibling branches — only the path relevant to the current query.

---

## Anatomy of a Skill

Every skill in Skills Graph follows a standardized structure with five core components:

### 1. SKILL.md — The Router

The only file with YAML frontmatter. Contains the routing table that maps user intent to reference files. Kept deliberately lean (under 100 lines) to minimize context cost when the skill triggers.

### 2. References Directory — The Knowledge Graph

Markdown files organized as a graph. Two types of nodes:
- **Router files** — contain a sub-reference table pointing to child files
- **Leaf files** — contain the actual knowledge (code examples, API docs, patterns)

No reference file has YAML frontmatter. This is by design — frontmatter is only needed for skill discovery, not for reference loading.

### 3. VERSION.json — Version Tracking

Machine-readable metadata tracking:
- Skill version (semantic versioning)
- Framework version being tracked (e.g., Agno 2.5.3)
- Per-file metadata: which framework version each reference was written for, last update date
- Documentation sitemap: all known doc pages for diffing against new releases
- Statistics: routing entries, reference files, total lines

### 4. CHANGELOG.md — Release History

Human-readable release notes following Keep a Changelog conventions. Documents what changed in each version with categories: Added, Changed, Split, Fixed, Stats.

### 5. Scripts — Maintenance Automation

Python scripts for automated maintenance:
- **Version checking** — compare tracked version against PyPI/GitHub latest
- **Sitemap diffing** — detect new documentation pages
- **Staleness detection** — flag reference files older than a configurable threshold
- **Integrity validation** — verify all routing table entries have corresponding files on disk

### 6. AUDIT-REPORT.md — Architecture Quality

Self-assessment document analyzing the skill against best practices:
- Progressive disclosure compliance
- Comparison with exemplary skills
- Scorecard across 8 quality categories
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

**Coverage includes:** Agents, Teams, Workflows, Tools (120+ builtins), Models (40+ providers), Database (18 backends), Memory, Knowledge/RAG (14+ vector DBs, 12+ embedders), Learning, Guardrails, Human-in-the-Loop, Evals, Hooks, Tracing, Context Management, AgentOS, Multimodal, Reasoning, Deploy, Observability (12 platforms), Integrations, and more.

### Microsoft Agent Framework (v2.0.0)

Full-coverage skill for [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (Python).

| Metric | Value |
|--------|-------|
| Routing Entries | 109 (63 explicit + 46 fuzzy) |
| Reference Files | 61 |
| Total Lines | ~14,000 |
| Framework Version Tracked | 1.0.0b260130 (Public Preview) |

**Coverage includes:** Agents, Running Agents, Structured Output, Tools (function + hosted), RAG, Sessions, Memory, Middleware, Providers (6), Workflows (13 deep-dive files), Orchestration (5 patterns), Deployment (Azure Functions, A2A, AG-UI), Observability, Security, Design Patterns, and more.

---

## Installation

Skills Graph skills work with any AI coding assistant that supports the Agent Skills standard.

### Quick Install (Smithery)

```bash
# Install a skill via Smithery marketplace
smithery install agno
```

### Manual Install

Copy the skill folder to your platform's skill directory:

| Platform | Project-Level Path | Global Path |
|----------|-------------------|-------------|
| **Claude Code** | `.claude/skills/agno/` | `~/.claude/skills/agno/` |
| **Gemini CLI** | `.gemini/skills/agno/` | `~/.gemini/skills/agno/` |
| **Cursor** | `.cursor/skills/agno/` | `~/.cursor/skills/agno/` |
| **Windsurf** | `.windsurf/skills/agno/` | `~/.codeium/windsurf/skills/agno/` |
| **Codex** | `.codex/skills/agno/` | `~/.codex/skills/agno/` |
| **Trae** | `.trae/skills/agno/` | `~/.trae/skills/agno/` |
| **Antigravity** | `.agent/skills/agno/` | `~/.gemini/antigravity/skills/agno/` |

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
```

---

## Platform Compatibility

The Agent Skills standard (the `SKILL.md` format) is supported by 25+ AI coding platforms. All platforms use the same discovery/activation/execution pattern: scan descriptions, load `SKILL.md` on match, read references on demand.

| Platform | Type | Compatibility |
|----------|------|---------------|
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

The standard is simple:

1. A `SKILL.md` file with YAML frontmatter (`name` + `description`) acts as the entry point
2. Optional `references/` directory for additional knowledge files
3. Optional `scripts/` directory for executable tools
4. The AI discovers skills by scanning descriptions, loads `SKILL.md` when triggered, and reads references on demand

Skills Graph builds on this standard by introducing a disciplined methodology for structuring the reference layer as an interconnected graph rather than a flat collection of files.

---

## Maintenance

### Checking for Updates

Each skill includes a maintenance script that validates freshness and integrity:

```bash
# Agno skill
python agno-skill/scripts/check-updates.py --report

# Available flags:
#   --version    Compare tracked version against PyPI latest
#   --sitemap    Check for new documentation pages
#   --stale N    Show files older than N days (default: 30)
#   --integrity  Verify all routing table entries exist on disk
#   --report     Run all checks

# Microsoft Agent Framework skill
python ms-agent-framework/scripts/check-freshness.py --verbose
```

### Version Tracking

Every skill maintains a `VERSION.json` with:
- Skill version and framework version tracked
- Per-file metadata (which framework version each reference targets)
- Documentation sitemap for diffing new releases
- Aggregate statistics (routing entries, files, lines)

---

## Contributing

Contributions are welcome. If you want to create a new skill following the Skills Graph methodology:

1. **Start with the router** — Write `SKILL.md` with a clear routing table. Keep it under 100 lines.
2. **Organize references as a graph** — Use router files for complex topics (5+ sub-topics) and leaf files for focused content.
3. **Add "Read When" guidance** — Every routing entry should tell the AI exactly when to load that file.
4. **No frontmatter on references** — Only `SKILL.md` gets YAML frontmatter.
5. **Track versions** — Create a `VERSION.json` with per-file metadata.
6. **Add maintenance scripts** — Automate version checking and staleness detection.
7. **Audit yourself** — Write an `AUDIT-REPORT.md` scoring your skill against the progressive disclosure principles.

### Quality Checklist

- [ ] `SKILL.md` is under 100 lines
- [ ] Every reference file is reachable from the routing table
- [ ] Router files have "Read When" / "Sub-References" tables
- [ ] Files over 300 lines have a table of contents
- [ ] Files over 500 lines are split into router + sub-files
- [ ] `VERSION.json` tracks framework version and per-file metadata
- [ ] `CHANGELOG.md` documents all releases
- [ ] Maintenance script passes all integrity checks

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

- [Agno](https://github.com/agno-agi/agno) — The open-source agent framework
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) — AI agent framework by Microsoft
- The Agent Skills standard — Originally by Anthropic (Claude Code), now a universal format across 25+ platforms
