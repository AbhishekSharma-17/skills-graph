# Remotion Prompt Generator — Architecture Audit Report

**Date:** 2026-02-22
**Skill version:** 1.1.0 | **Source tracked:** Remotion 4.x (capabilities reference)
**Author:** Abhishek Sharma
**Stats:** 8 routing entries, 15 reference files, ~3,200 lines

---

## How the Skills System Works (Progressive Disclosure)

| Level | What | When Loaded | Size Guideline |
|-------|------|-------------|----------------|
| **Metadata** | YAML `name` + `description` | Always in context | ~100 words |
| **SKILL.md body** | Main instructions/router | When skill triggers | <100 lines |
| **Bundled resources** | `references/`, `scripts/` | On demand via `Read` | Unlimited |

---

## Skill Structure

```
remotion-prompt-generator/
|-- SKILL.md (57 lines — router with mandatory load + web search instructions)
|-- references/
|   |-- remotion-capabilities.md (leaf — ~210 lines, comprehensive Remotion reference) [ALWAYS LOADED]
|   |-- intelligent-inference.md (leaf — ~400 lines, vague prompt handling engine) [ALWAYS LOADED]
|   |-- video-types.md (router — ~40 lines, routes to 7 domain sub-files)
|   |-- prompt-engineering.md (leaf — ~420 lines, prompt format + templates)
|   |-- discovery-workflow.md (leaf — ~340 lines, question bank + strategies)
|   |-- asset-styling-guide.md (leaf — ~300 lines, colors/fonts/dimensions)
|   |-- animation-effects.md (leaf — ~400 lines, animations/transitions/timing)
|   |-- video-types/
|   |   |-- marketing-saas.md (leaf — ~260 lines)
|   |   |-- social-media.md (leaf — ~220 lines)
|   |   |-- data-analytics.md (leaf — ~160 lines)
|   |   |-- education-explainer.md (leaf — ~120 lines)
|   |   |-- ecommerce-realestate.md (leaf — ~150 lines)
|   |   |-- entertainment-media.md (leaf — ~130 lines)
|   |   +-- personalized-data.md (leaf — ~130 lines)
|   +-- prompt-engineering/
|       +-- domain-examples.md (leaf — ~250 lines)
```

---

## What We're Doing Well

### 1. Clean Router Architecture
SKILL.md is 46 lines — well under the 100-line limit. It's a pure router with no knowledge content. Every reference file is reachable from the routing table with clear "Read When" conditions.

### 2. Two-Level Routing for Video Types
The `video-types.md` router fans out to 7 domain-specific sub-files, allowing the AI to load only the relevant domain (e.g., marketing vs. data visualization) without reading all 7.

### 3. Comprehensive Discovery Workflow
The discovery-workflow.md file provides a structured approach to gathering user requirements through progressive questioning, preventing incomplete prompts.

### 4. Standardized Prompt Output Format
The prompt-engineering.md file defines a consistent 12-section output format that any Remotion Dev skill can consume, ensuring interoperability.

### 5. Aggressive Description Triggering
The SKILL.md description includes MANDATORY TRIGGERS with specific keywords and broad trigger conditions, maximizing the chance the skill activates when relevant.

### 6. Intelligent Inference Engine
The `intelligent-inference.md` file enables the skill to handle vague prompts by extracting signals, auto-filling smart defaults, and only asking 2-3 critical questions instead of overwhelming the user.

### 7. Mandatory Web Search
SKILL.md mandates web searching about the user's product/industry before generating prompts, ensuring context-rich, relevant output even from minimal input.

---

## What Needs Improvement

### PRIORITY 1: Remotion Capabilities File Approaching Size Limit
`remotion-capabilities.md` is ~480 lines, close to the 500-line split threshold. If expanded, it should be split into a router with sub-files (e.g., capabilities/animation.md, capabilities/assets.md, capabilities/rendering.md).

### PRIORITY 2: Add More Complete Prompt Examples
Currently only the marketing-saas.md file has a full end-to-end prompt example. Each video-type sub-file should ideally have at least one complete prompt example.

### PRIORITY 3: Version Tracking for Remotion Updates
The skill references Remotion 4.x capabilities. As Remotion 5.0 releases, the remotion-capabilities.md and animation-effects.md files will need updates. Consider adding a PyPI/npm check to the maintenance script.

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **SKILL.md size** | 5/5 | 57 lines — well under 100 |
| **Progressive disclosure** | 5/5 | Two-level routing (SKILL.md → video-types.md → domain files) |
| **Reference splitting** | 4/5 | All under 500 lines; remotion-capabilities.md is close |
| **YAML frontmatter** | 5/5 | Only on SKILL.md, with license + metadata |
| **TOC on large files** | 5/5 | All files >300 lines have ## Contents |
| **Description triggering** | 5/5 | Explicit MANDATORY TRIGGERS, broad coverage, "When in doubt" |
| **Tooling & maintenance** | 5/5 | VERSION.json + CHANGELOG + AUDIT + check-updates.py |
| **Overall** | **4.9/5** | Strong v1.1.0, inference engine and web search make it production-ready |

---

## Recommended Action Plan

1. **Quick win** — Add complete prompt examples to remaining video-type sub-files (~30 min each)
2. **Medium effort** — Create `scripts/check-updates.py` adapted for npm package version checking (~1 hour)
3. **Quick win** — Split remotion-capabilities.md if it grows past 500 lines (~15 min)
4. **Future** — Add more industry domain examples (travel, food, gaming, non-profit) as demand emerges
