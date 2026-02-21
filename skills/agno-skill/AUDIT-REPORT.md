# Agno Skill — Architecture Audit Report

**Date:** 2026-02-21
**Skill version:** 1.1.0 | **Agno tracked:** 2.5.3
**Stats:** 34 routing entries, 103 reference files, ~22,800 lines

---

## How the Skills System Works (Progressive Disclosure)

The Claude Code skills architecture uses a **3-level progressive loading** system designed to minimize context usage:

| Level | What | When Loaded | Size Guideline |
|-------|------|-------------|----------------|
| **Metadata** | YAML `name` + `description` | Always in context | ~100 words |
| **SKILL.md body** | Main instructions/router | When skill triggers | <500 lines |
| **Bundled resources** | `references/`, `scripts/`, `assets/` | On demand via `Read` | Unlimited |

The key insight: only the YAML description is always loaded. SKILL.md loads when the skill triggers. Reference files only load when explicitly read. This means a 22,800-line skill costs the same as a 50-line skill until the user actually needs Agno help — at which point only the relevant reference file is loaded.

### Loading Functions

Claude uses three internal functions to access skill resources:
- `get_skill_instructions()` → reads SKILL.md body
- `get_skill_reference(filename)` → reads a reference file
- `get_skill_script(filename)` → reads a script file

Scripts can also execute without being loaded into context (via `Bash`), which is ideal for deterministic tasks.

---

## How Exemplary Skills Are Structured

### PDF Skill (3 files, 1,219 total lines)
```
pdf/
├── SKILL.md (314 lines) — Quick start + common tasks inline
├── REFERENCE.md (611 lines) — Advanced pypdfium2, JS libraries
└── FORMS.md (294 lines) — Form filling workflow
```
- SKILL.md contains the most common operations directly
- Splits by **task complexity** — basic vs advanced vs specialized

### PPTX Skill (3 files, 857 total lines)
```
pptx/
├── SKILL.md (232 lines) — Router + design guidance
├── editing.md (205 lines) — Template-based editing workflow
└── pptxgenjs.md (420 lines) — Creating from scratch
```
- SKILL.md is a **router** with a quick reference table + design principles
- Splits by **workflow type** — read vs edit vs create

### DOCX Skill (1 file, 590 lines)
```
docx/
└── SKILL.md (590 lines) — Everything in one file
```
- Exceeds the 500-line guideline (590 lines)
- Single-file approach — no references

### XLSX Skill (1 file, 291 lines)
```
xlsx/
└── SKILL.md (291 lines) — Everything in one file
```
- Well under limit, no need for references

### Key Pattern: Reference Files Have NO YAML Frontmatter

None of the exemplary skills' reference files (REFERENCE.md, FORMS.md, editing.md, pptxgenjs.md) have YAML frontmatter. Only `SKILL.md` has frontmatter. This is the correct pattern — frontmatter is only needed for skill discovery/triggering.

---

## Our Agno Skill Structure

```
agno-skill/
├── SKILL.md (69 lines) — Pure router with reference table
├── CHANGELOG.md
├── VERSION.json
├── scripts/check-updates.py
└── references/ (103 files, ~22,800 lines)
    ├── agents.md (470 lines) — flat
    ├── teams.md (489 lines) — flat
    ├── workflows.md (398 lines) — flat
    ├── database.md (766 lines) — flat ⚠️
    ├── memory.md (667 lines) — flat ⚠️
    ├── input-output.md (700 lines) — flat ⚠️
    ├── workflow-patterns.md (762 lines) — flat ⚠️
    ├── tools.md → tools/ (router + sub-files) ✅
    ├── knowledge.md → knowledge/ (router + sub-files) ✅
    ├── guardrails.md → guardrails/ (router + sub-files) ✅
    ├── hooks.md → hooks/ (router + sub-files) ✅
    ├── agentos.md → agentos/ (router + sub-files) ✅
    ├── ... and 20+ more topics
    └── various sub-directories with sub-reference files
```

---

## What We're Doing Well

### 1. SKILL.md is Exceptionally Lean (69 lines) ✅
The recommended limit is 500 lines. Our SKILL.md is 69 lines — a pure router table with install instructions and version tracking. This is ideal because:
- Minimal context consumed when the skill triggers
- Clear routing guidance: "Read When" column tells the model exactly which file to load
- Zero redundancy — no content is duplicated between SKILL.md and reference files

### 2. Router Pattern Matches Recommended Architecture ✅
The skill-creator recommends a "domain organization" pattern where SKILL.md acts as workflow + selection, pointing to variant-specific references. Our routing table with 34 entries does exactly this.

### 3. Proper Topic Splitting for Complex Areas ✅
Several topics correctly use the router → sub-files pattern:
- `tools.md` → `tools/advanced.md`, `tools/custom-toolkits.md`, `tools/builtin-*.md`
- `guardrails.md` → `guardrails/builtin-guardrails.md`, `guardrails/custom-guardrails.md`, `guardrails/usage-examples.md`
- `hooks.md` → `hooks/agent-hooks.md`, `hooks/team-hooks.md`
- `agentos.md` → `agentos/setup-api.md`, `agentos/config-security.md`

### 4. Reference Files Correctly Lack YAML Frontmatter ✅
None of our 103 reference files have YAML frontmatter, matching the pattern from all exemplary Anthropic skills. Frontmatter is only on SKILL.md.

### 5. Description is Reasonably Trigger-Oriented ✅
Our description includes both what the skill does AND specific trigger contexts (Agno, AI agents, tools/memory/knowledge, multi-agent, RAG, reasoning, AgentOS). The skill-creator warns Claude tends to "undertrigger" skills, so being explicit about triggers is important.

### 6. Excellent Tooling ✅
VERSION.json + check-updates.py + CHANGELOG.md is above and beyond what any exemplary skill has. This is unique to our skill and adds significant maintenance value.

---

## What Needs Improvement

### PRIORITY 1: Add TOCs to 16 Large Files (>300 lines)

The skill-creator explicitly states: "For large reference files (>300 lines), include a table of contents."

**16 files exceed 300 lines with no TOC:**

| File | Lines | Action |
|------|-------|--------|
| `database.md` | 766 | Split into router + sub-files (see P2) |
| `workflow-patterns.md` | 762 | Add TOC |
| `input-output.md` | 700 | Split into router + sub-files (see P2) |
| `memory.md` | 667 | Split into router + sub-files (see P2) |
| `agentos/config-security.md` | 549 | Add TOC |
| `teams.md` | 489 | Add TOC |
| `agents.md` | 470 | Add TOC |
| `guardrails/usage-examples.md` | 402 | Add TOC |
| `workflows.md` | 398 | Add TOC |
| `agentos/setup-api.md` | 394 | Add TOC |
| `guardrails/builtin-guardrails.md` | 350 | Add TOC |
| `hooks/agent-hooks.md` | 324 | Add TOC |
| `context-mgmt/system-message.md` | 313 | Add TOC |
| `context-mgmt/dependency-injection.md` | 311 | Add TOC |
| `tools/advanced.md` | 304 | Add TOC |
| `context-mgmt/chat-history.md` | 303 | Add TOC |

**TOC format** (matches what `workflow-patterns.md` already has):
```markdown
## Contents
- [Section Name](#section-name)
- [Another Section](#another-section)
```

### PRIORITY 2: Split 4 Oversized Flat Files (>500 lines)

These files are too large for a single reference and should be converted to the router + sub-files pattern:

| File | Lines | Suggested Split |
|------|-------|-----------------|
| `database.md` | 766 | `database.md` (router) → `database/postgres.md`, `database/nosql.md`, `database/session-mgmt.md` |
| `workflow-patterns.md` | 762 | `workflow-patterns.md` (router) → `workflow-patterns/sequential-parallel.md`, `workflow-patterns/conditional-loop.md`, `workflow-patterns/router-mixed.md` |
| `input-output.md` | 700 | `input-output.md` (router) → `input-output/structured-io.md`, `input-output/multimodal.md`, `input-output/streaming.md` |
| `memory.md` | 667 | `memory.md` (router) → `memory/automatic.md`, `memory/agentic.md`, `memory/best-practices.md` |

This follows the same pattern we already use successfully for tools, guardrails, hooks, etc.

### PRIORITY 3: Make Description Pushier

The skill-creator explicitly says descriptions should be "pushy" to combat undertriggering. Our current description is good but could be more aggressive:

**Current (good):**
> Build AI agents, multi-agent teams, and agentic workflows using the Agno framework. Use this skill whenever the user mentions Agno, wants to build AI agents with tools/memory/knowledge, create multi-agent systems, or build agentic applications. Also trigger when the user asks about agent orchestration, RAG agents, reasoning agents, or production agent deployment with AgentOS. Even if the user just says 'build me an agent' or 'create an AI assistant', consider using this skill if Agno is in their stack.

**Suggested (pushier):**
> Build AI agents, multi-agent teams, and agentic workflows using the Agno framework. MANDATORY TRIGGERS: Agno, agno-agi, AgentOS, any mention of the Agno framework. Also trigger when the user wants to build AI agents with tools/memory/knowledge, create multi-agent systems, RAG pipelines, reasoning agents, agentic workflows, or deploy agents to production. Trigger even if the user just says 'build me an agent', 'create an AI assistant', or 'make a chatbot' — if Agno is anywhere in their stack or project dependencies. When in doubt about whether to use this skill for agent-building tasks, use it.

### PRIORITY 4: Add `license` Field to Frontmatter (Optional)

All exemplary Anthropic skills include a `license` field:
```yaml
license: Proprietary. LICENSE.txt has complete terms
```

Since our skill is user-created, this is optional. But if distributing, consider:
```yaml
license: MIT
```

---

## YAML Frontmatter Best Practices Summary

| Aspect | Best Practice | Our Status |
|--------|---------------|------------|
| **Location** | Only on SKILL.md, NOT on reference files | ✅ Correct |
| **Required fields** | `name` and `description` | ✅ Present |
| **Optional fields** | `compatibility`, `license` | ⚠️ Missing `license` |
| **Description style** | "Pushy" — include explicit trigger keywords | ⚠️ Good but could be pushier |
| **Description length** | ~100 words (loaded into context always) | ✅ ~85 words |
| **Reference files** | Plain markdown, no frontmatter needed | ✅ Correct |

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **SKILL.md size** | ⭐⭐⭐⭐⭐ | 69 lines — exemplary lean router |
| **Progressive disclosure** | ⭐⭐⭐⭐ | Great router pattern, but 4 oversized flat files |
| **Reference splitting** | ⭐⭐⭐⭐ | Many topics well-split; 4 need splitting |
| **YAML frontmatter** | ⭐⭐⭐⭐⭐ | Correct placement, correct fields |
| **TOC on large files** | ⭐⭐ | 16 of 16 files >300 lines missing TOC |
| **Description triggering** | ⭐⭐⭐⭐ | Good triggers but could be pushier |
| **Tooling & maintenance** | ⭐⭐⭐⭐⭐ | VERSION.json + updater + changelog = best-in-class |
| **Overall** | **⭐⭐⭐⭐** | Excellent foundation, needs TOCs and a few file splits |

---

## Cross-Platform Compatibility Analysis

### The Agent Skills Standard Has Gone Universal

Agent Skills (the `SKILL.md` format) started as a Claude Code feature in October 2025, went open in December 2025, and by February 2026 has become a **universal standard** supported by 25+ platforms. The format is identical across all of them — our skill already works everywhere.

### Platform Compatibility Matrix

| Platform | Type | Skill Path (Project) | Skill Path (Global) | Compatibility |
|----------|------|---------------------|---------------------|---------------|
| **Claude Code** | CLI | `.claude/skills/` | `~/.claude/skills/` | ✅ Full |
| **Antigravity** | IDE | `.agent/skills/` | `~/.gemini/antigravity/skills/` | ✅ Full |
| **Gemini CLI** | CLI | `.gemini/skills/` | `~/.gemini/skills/` | ✅ Full |
| **Cursor** | IDE | `.cursor/skills/` | `~/.cursor/skills/` | ✅ Full |
| **Codex** | CLI | `.codex/skills/` | `~/.codex/skills/` | ✅ Full |
| **Windsurf** | IDE | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` | ✅ Full |
| **GitHub Copilot** | Extension | `.github/skills/` | `~/.copilot/skills/` | ⚠️ Partial |
| **OpenCode** | CLI | `.opencode/skills/` | `~/.config/opencode/skills/` | ✅ Full |
| **Trae** | IDE | `.trae/skills/` | `~/.trae/skills/` | ✅ Full |
| **Amp** | IDE | — | — | ✅ Full |
| **Goose** | CLI | — | — | ✅ Full |

All platforms use the same discovery/activation/execution pattern: scan descriptions → load SKILL.md on match → read references on demand.

### Agno's Native Skills Integration

Agno has **first-class skills support** since January 2026 (v2.5), based directly on the Anthropic Agent Skills specification:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills("/path/to/agno-skill")])
)
# Agent gets: get_skill_instructions(), get_skill_reference(), get_skill_script()
```

Key Agno skills details:
- **`LocalSkills`** loader reads from filesystem (same `SKILL.md` format)
- **`Skills`** class supports multiple loaders — combine shared + project skills
- **Agent tools added automatically**: `get_skill_instructions(name)`, `get_skill_reference(name, path)`, `get_skill_script(name, path, execute, args, timeout)`
- **Lazy loading**: Agent sees name+description in system prompt → loads full instructions on match → references on demand
- **Validation**: `SkillValidationError` on load — enforces name format (lowercase+hyphens, max 64 chars), description max 1024 chars
- **Optional frontmatter fields**: `license` (SPDX identifiers), `metadata` (version, author, tags)
- **`skills.reload()`** for runtime updates
- **Anthropic native skills** also supported: `Claude(skills=[{"type": "anthropic", "skill_id": "pptx"}])`

### Smithery Skills Marketplace

Our skill is already published on **Smithery** (smithery.ai/skills/delorenj/agno), a marketplace for Agent Skills. Smithery provides:
- One-click install via CLI: `smithery install agno`
- Cross-platform deployment (installs to the right path for each platform)
- Discovery and search
- This confirms our format is already compatible with the distribution ecosystem

### How Our Skill Works Across Platforms

**What works out-of-the-box everywhere:**
- SKILL.md with YAML frontmatter → ✅ Universal format
- `references/` directory with markdown files → ✅ All platforms support reference loading
- `scripts/` directory → ✅ All platforms support script execution
- Progressive disclosure (router pattern) → ✅ All platforms use the same lazy-loading model
- No YAML frontmatter on reference files → ✅ Correct — only SKILL.md needs it

**Platform-specific considerations:**
- **Name validation**: Agno enforces lowercase + hyphens only, max 64 chars. Our name `agno` passes ✅
- **Description limit**: Agno caps at 1024 characters. Our description is ~490 characters ✅
- **Antigravity**: Uses `.agent/skills/` (project) or `~/.gemini/antigravity/skills/` (global). Same format, just different path
- **Cursor**: Has a separate "rules" system (`.cursorrules`), but skills use the same SKILL.md format

### What the Research Reveals About Best Architecture

The universal standard confirms the same patterns we discovered from Anthropic's skill-creator:

1. **SKILL.md is the only file that needs frontmatter** — reference files are plain markdown everywhere
2. **Progressive disclosure is the core design principle** — all 25+ platforms implement the same 3-level system
3. **Router pattern scales best** — skills like ours with 103 reference files work because only 1-2 files load per task
4. **Description is the primary trigger mechanism** — it must be "pushy" because semantic matching is the discovery layer
5. **Scripts should be "black boxes"** — Antigravity docs explicitly recommend agents run scripts with `--help` first rather than reading source
6. **Agno's `metadata` field** is a nice addition we should adopt — `version`, `author`, `tags` enable better discovery

### Recommended Frontmatter Update (Cross-Platform Optimized)

```yaml
---
name: agno
description: "Build AI agents, multi-agent teams, and agentic workflows using the Agno framework. MANDATORY TRIGGERS: Agno, agno-agi, AgentOS, any mention of the Agno framework. Also trigger when the user wants to build AI agents with tools/memory/knowledge, create multi-agent systems, RAG pipelines, reasoning agents, agentic workflows, or deploy agents to production. Trigger even if the user just says 'build me an agent', 'create an AI assistant', or 'make a chatbot' — if Agno is anywhere in their stack or project dependencies. When in doubt about whether to use this skill for agent-building tasks, use it."
license: MIT
metadata:
  version: "1.1.0"
  author: 7X Ventures
  tags: ["agno", "ai-agents", "multi-agent", "agentos", "rag", "workflows", "mcp"]
---
```

This frontmatter is compatible with Agno's validation rules, Claude Code, Antigravity, and all other platforms.

---

## Recommended Action Plan

1. **Quick win** — Add TOCs to all 16 files >300 lines (~30 min)
2. **Medium effort** — Split the 4 oversized files into router + sub-files (~2 hrs)
3. **Quick win** — Update SKILL.md frontmatter with pushier description + `license` + `metadata` fields (~5 min)
4. **Quick win** — Verify name validation against Agno rules (already passes ✅)
5. **Optional** — Add install instructions for multiple platforms (Antigravity, Cursor, Codex, etc.)
