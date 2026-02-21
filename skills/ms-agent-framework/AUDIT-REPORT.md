# ms-agent-framework — Architecture Audit Report

**Date:** 2026-02-21
**Skill version:** 1.0.0 | **Source tracked:** 1.0.0b260130
**Stats:** 22 routing entries, 62 reference files, ~10000 lines

---

## How the Skills System Works (Progressive Disclosure)

| Level | What | When Loaded | Size Guideline |
|-------|------|-------------|----------------|
| **Metadata** | YAML `name` + `description` | Always in context | ~100 words |
| **SKILL.md body** | Main instructions/router | When skill triggers | <500 lines |
| **Bundled resources** | `references/`, `scripts/` | On demand via `Read` | Unlimited |

---

## Skill Structure

```
ms-agent-framework/
|-- SKILL.md (66 lines)
|-- references/ (62 files)
    |-- 22-design-patterns-core.md
    |-- 23-design-patterns-advanced.md
    |-- 13a-azure-functions.md
    |-- <Many other comprehensive knowledge files>
```

---

## What We're Doing Well

### 1. Comprehensive Coverage
The skill covers all the aspects of the Microsoft Agent Framework, including core concepts, multi-agent patterns, observability, security, and deployment guides.

### 2. Standardized Router
The `SKILL.md` file has been restructured to act as a proper router, directing questions immediately to the correct internal reference based on the user's requirements.

---

## What Needs Improvement

### PRIORITY 1: Reference Size
Several reference files, such as `22-design-patterns-core.md` and `23-design-patterns-advanced.md`, are exceptionally large. These files should be split into routers and sub-files (e.g., `22-design-patterns-core/reflection.md`, etc.).

### PRIORITY 2: Missing Router Sub-files
Ensure files larger than 500 lines are migrated to the router and sub-files pattern.

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **SKILL.md size** | 5/5 | 66 lines, well under 80 lines |
| **Progressive disclosure** | 3/5 | Basic routing works well, but leaf nodes are too big |
| **Reference splitting** | 2/5 | Several oversized files need splitting |
| **YAML frontmatter** | 5/5 | Correct on SKILL.md with tags, version, and author |
| **TOC on large files** | 3/5 | Some older large files need clear TOC |
| **Description triggering** | 5/5 | Pushy description with clear intent logic |
| **Tooling & maintenance** | 5/5 | All standard scripts and documentation tracking |
| **Overall** | **4/5** | Strong core content, structural cleanup underway |

---

## Recommended Action Plan

1. **Medium effort** — Split `22-design-patterns-core.md` into router and individual pattern sub-files (~2 hours)
2. **Medium effort** — Split `23-design-patterns-advanced.md` into router and individual pattern sub-files (~2 hours)
3. **Quick win** — Evaluate remaining oversized reference documents and create a sub-directory map for them (~1 hour)
