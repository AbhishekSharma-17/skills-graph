# Contributing — Skills Graph Standard

> The complete guide to building a Skills Graph skill from scratch.
> A skill can be about **anything** — a framework, a library, an API, a design methodology, a workflow pattern, internal company standards, or any knowledge domain you want an AI to master.
> Follow this standard exactly. Every section includes copy-paste templates and rules derived from our production skills.

**Author:** Abhishek Sharma &middot; **License:** MIT

---

## Table of Contents

- [Quick Start Checklist](#quick-start-checklist)
- [Directory Structure](#directory-structure)
- [Step 1: SKILL.md — The Router](#step-1-skillmd--the-router)
- [Step 2: Reference Files — The Knowledge Graph](#step-2-reference-files--the-knowledge-graph)
- [Step 3: VERSION.json — Version Tracking](#step-3-versionjson--version-tracking)
- [Step 4: CHANGELOG.md — Release History](#step-4-changelogmd--release-history)
- [Step 5: AUDIT-REPORT.md — Self-Assessment](#step-5-audit-reportmd--self-assessment)
- [Step 6: scripts/ — Maintenance Automation](#step-6-scripts--maintenance-automation)
- [Step 7: metadata/ — Source Tracking (Optional)](#step-7-metadata--source-tracking-optional)
- [Reference File Patterns](#reference-file-patterns)
- [Naming Conventions](#naming-conventions)
- [Size Rules](#size-rules)
- [Quality Checklist](#quality-checklist)
- [Common Mistakes](#common-mistakes)
- [Examples from Production](#examples-from-production)

---

## Quick Start Checklist

Use this as your master checklist when building a new skill:

```
[ ] 1. Create directory: <skill-name>/
[ ] 2. Write SKILL.md with YAML frontmatter + routing table (name MUST match folder name)
[ ] 3. Create references/ with knowledge files
[ ] 4. Add VERSION.json with version tracking
[ ] 5. Add CHANGELOG.md with initial release
[ ] 6. Add scripts/check-updates.py (adapt template)
[ ] 7. Write AUDIT-REPORT.md scoring your skill
[ ] 8. Verify: SKILL.md under 100 lines
[ ] 9. Verify: All references reachable from routing table
[ ] 10. Verify: No YAML frontmatter on any reference file
[ ] 11. Verify: Files >300 lines have TOC
[ ] 12. Verify: Files >500 lines split into router + sub-files
[ ] 13. Run integrity check: python scripts/check-updates.py --integrity
[ ] 14. Update root README.md: skills count, lines count, catalog table, repo structure, install commands
```

---

## Directory Structure

Every Skills Graph skill follows this structure:

```
<skill-name>/
|-- SKILL.md                    # REQUIRED — The router (only file with YAML frontmatter)
|-- VERSION.json                # REQUIRED — Version tracking
|-- CHANGELOG.md                # REQUIRED — Release history
|-- AUDIT-REPORT.md             # REQUIRED — Architecture self-assessment
|-- scripts/                    # REQUIRED — Maintenance automation
|   +-- check-updates.py       #   Version checking, integrity validation
|-- metadata/                   # OPTIONAL — Source tracking
|   |-- sources.json            #   Maps references to upstream docs
|   +-- version-tracking.json   #   Alternative/supplementary version tracking
+-- references/                 # REQUIRED — The knowledge graph
    |-- topic-a.md              #   Leaf node (200-500 lines)
    |-- topic-b.md              #   Leaf node
    |-- topic-c.md              #   Router node (under 100 lines)
    +-- topic-c/                #   Sub-directory for router
        |-- subtopic-1.md       #   Leaf node
        +-- subtopic-2.md       #   Leaf node
```

### What Goes Where

| Component | Purpose | Required |
|:----------|:--------|:--------:|
| `SKILL.md` | Entry point. YAML frontmatter + routing table. Under 100 lines. | Yes |
| `references/` | Knowledge graph. Router and leaf nodes. No frontmatter. | Yes |
| `VERSION.json` | Skill version, source version (if applicable), per-file metadata. | Yes |
| `CHANGELOG.md` | Release history with stats per version. | Yes |
| `AUDIT-REPORT.md` | Quality scorecard, architecture analysis. | Yes |
| `scripts/` | Automated maintenance (version check, integrity, staleness). | Yes |
| `metadata/` | Source URLs, supplementary tracking. | No |

---

## Step 1: SKILL.md — The Router

SKILL.md is the **only file with YAML frontmatter**. It's a pure router — no knowledge content, just navigation.

### Template

```markdown
---
name: <skill-name>          # MUST exactly match the folder name (most common mistake)
description: "<1-2 sentence overview>. MANDATORY TRIGGERS: <keyword1>, <keyword2>, <keyword3>. Also trigger when <broader contexts>. When in doubt about whether to use this skill, use it."
license: MIT
metadata:
  version: "<skill-version>"
  author: <your-name>
  tags: ["<tag1>", "<tag2>", "<tag3>"]
---

# <Skill Title> — Skill Router

<1-2 line summary of what this skill covers.>

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **<Topic A>** | `references/<topic-a>.md` | <When the AI should load this file — describe user intent, keywords, scenarios> |
| **<Topic B>** | `references/<topic-b>.md` | <Intent description> |
| **<Topic C>** | `references/<topic-c>.md` | <Intent description> |

## Setup (if applicable)

\`\`\`bash
<install command, prerequisites, or configuration steps>
\`\`\`

## Install This Skill

\`\`\`bash
# Via Smithery (any platform)
smithery install <skill-name>

# Manual — copy this folder to your platform's skill directory:
# Claude Code:   .claude/skills/<skill-name>/    or ~/.claude/skills/<skill-name>/
# Gemini CLI:    .gemini/skills/<skill-name>/    or ~/.gemini/skills/<skill-name>/
# Cursor:        .cursor/skills/<skill-name>/    or ~/.cursor/skills/<skill-name>/
# Windsurf:      .windsurf/skills/<skill-name>/  or ~/.codeium/windsurf/skills/<skill-name>/
# Codex:         .codex/skills/<skill-name>/     or ~/.codex/skills/<skill-name>/
# Trae:          .trae/skills/<skill-name>/      or ~/.trae/skills/<skill-name>/
# Antigravity:   .agent/skills/<skill-name>/     or ~/.gemini/antigravity/skills/<skill-name>/
\`\`\`

## Version Tracking

- **Skill version:** <version> | **Snapshot:** <date>
- Version metadata: `VERSION.json`
- Update checker: `python scripts/check-updates.py`
- Changelog: `CHANGELOG.md`
```

> **Note:** The "Setup" section is optional. Framework skills include install commands here. Non-framework skills (design patterns, coding standards, workflow guides) may skip this entirely or point to relevant prerequisites.

### SKILL.md Rules

| Rule | Detail |
|:-----|:-------|
| **Max lines** | 100 (ideally 60-80) |
| **Content** | Routing table + install instructions + version info. Zero knowledge content. |
| **YAML frontmatter** | Required. Must have `name` and `description`. Add `license`, `metadata`. |
| **Name format** | Lowercase, hyphens only. Max 64 characters. **Must exactly match the folder name.** This is the most common mistake. (e.g., folder `agno/` → `name: agno`, folder `api-design-patterns/` → `name: api-design-patterns`) |
| **Description** | Under 1024 characters. Must include MANDATORY TRIGGERS. Be "pushy" — tell the AI when to trigger. |
| **Routing table** | Every row maps a topic to a file with a "Read When" condition. |
| **"Read When" column** | Describe **user intent**, not file contents. Keywords the AI can match against the user's question. |

### Description Pattern

The description is the single most important field — it's always in the AI's context and determines whether the skill triggers. Be explicit and aggressive:

```
Bad:  "A skill for the Agno framework."
Good: "Build AI agents, multi-agent teams, and agentic workflows using the Agno
       framework. MANDATORY TRIGGERS: Agno, agno-agi, AgentOS. Also trigger when
       the user wants to build AI agents with tools/memory/knowledge. When in doubt,
       use it."

Bad:  "API design patterns."
Good: "Design REST, GraphQL, and gRPC APIs with production-grade patterns.
       MANDATORY TRIGGERS: API design, endpoint design, REST best practices,
       GraphQL schema, pagination, versioning, rate limiting. Also trigger when
       the user is building any backend API or reviewing API architecture.
       When in doubt, use it."
```

**Pattern:** `<What it does>. MANDATORY TRIGGERS: <keywords>. Also trigger when <broader contexts>. When in doubt, use it.`

This pattern works for any skill type — frameworks, libraries, design patterns, coding standards, internal documentation, etc.

---

## Step 2: Reference Files — The Knowledge Graph

References are the actual knowledge. They come in two types: **router nodes** and **leaf nodes**.

### Leaf Node Template

Leaf nodes contain actual knowledge. This is the most common type.

```markdown
# <Topic Title>

<1-2 line summary of what this file covers.>

## Contents

(Required if file >300 lines)

- [Section A](#section-a)
- [Section B](#section-b)
- [Section C](#section-c)

## Section A

<Knowledge content — examples, tables, explanations, diagrams.>

## Section B

<More knowledge content.>

## Quick Reference

<Cheat sheet, key imports, common commands, or summary table — whatever makes
 sense for your domain.>
```

### Router Node Template

Router nodes exist when a topic is too large for a single file (>500 lines). The router fans out to sub-files.

```markdown
# <Topic Title>

<1-2 line summary.>

## Sub-References

Read only what the current task requires:

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **<Subtopic A>** | `<topic>/<subtopic-a>.md` | <Intent description> |
| **<Subtopic B>** | `<topic>/<subtopic-b>.md` | <Intent description> |
| **<Subtopic C>** | `<topic>/<subtopic-c>.md` | <Intent description> |

## Quick Start

<Minimal example — enough for simple cases without loading sub-references.
 This could be a code snippet, a decision table, a checklist, or whatever
 fits your domain.>

## Quick Reference

<Summary table, key terms, or cheat sheet for this topic.>
```

### Reference File Rules

| Rule | Detail |
|:-----|:-------|
| **No YAML frontmatter** | Only SKILL.md has frontmatter. Reference files are plain markdown. |
| **No `---` dividers at top** | Don't start with `---`. Start with `# Title`. |
| **Leaf nodes** | 200-500 lines. Focused on one topic. |
| **Router nodes** | Under 100 lines. Sub-References table + Quick Start + Key Imports. |
| **TOC required** | On any file >300 lines. Use `## Contents` with anchor links. |
| **Must split** | Any file >500 lines must become a router + sub-files. |
| **Actionable examples** | Every reference should include at least one actionable example (code, config, template, decision tree — whatever fits the domain). |
| **Structured data** | Use markdown tables for parameters, comparisons, decision matrices, checklists. |
| **Cross-references** | Reference other files when topics connect (e.g., "See `memory.md` for persistence" or "See `naming-conventions.md` for details"). |

### The Router vs. Leaf Decision

```
Is the topic >500 lines of content?
  |
  +-- YES --> Create a ROUTER node
  |           - router file: <topic>.md (under 100 lines)
  |           - sub-files:   <topic>/<subtopic>.md (200-500 lines each)
  |           - directory:   references/<topic>/
  |
  +-- NO  --> Create a LEAF node
              - single file: references/<topic>.md (200-500 lines)
              - if >300 lines, add ## Contents TOC
```

---

## Step 3: VERSION.json — Version Tracking

VERSION.json is the machine-readable metadata file that tracks versions at multiple levels: the skill itself, the upstream source it documents (if any), and individual reference files.

### Template

```json
{
  "skill_name": "<skill-name>",
  "skill_version": "1.0.0",
  "source_version_tracked": "<upstream-version-if-applicable>",
  "source_release_date": "<YYYY-MM-DD>",
  "content_snapshot_date": "<YYYY-MM-DD>",
  "last_checked": "<YYYY-MM-DD>",
  "stats": {
    "routing_entries": 0,
    "reference_files": 0,
    "total_lines": 0
  },
  "urls": {
    "docs": "<docs-url>",
    "github": "<github-url>",
    "changelog": "<upstream-changelog-url>"
  },
  "references": {
    "<filename>.md": {
      "written_for": "<source-version-or-date>",
      "last_updated": "<YYYY-MM-DD>"
    }
  },
  "excluded_sections": [
    "<section> (<reason>)"
  ]
}
```

> **Adapting for your domain:**
> - **Framework/library skills**: Use `"<fw>_version_tracked"` (e.g., `"agno_version_tracked": "2.5.3"`), add `"pypi"` and `"pypi_json"` to urls, add `"docs_sitemap"` array for page diffing.
> - **API skills**: Track API version (e.g., `"stripe_api_version": "2025-02-01"`).
> - **Standards/patterns skills**: Use `"content_snapshot_date"` as the primary freshness indicator. `"source_version_tracked"` can be omitted or set to the spec version.
> - **Internal/proprietary skills**: Track the internal doc revision or confluence page version.

### VERSION.json Rules

| Field | Purpose | Required |
|:------|:--------|:--------:|
| `skill_name` | Matches SKILL.md `name` field | Yes |
| `skill_version` | Semantic version of the skill | Yes |
| `source_version_tracked` | Upstream version being documented (framework, API, spec) | If applicable |
| `content_snapshot_date` | When content was last written/reviewed | Yes |
| `last_checked` | When the automated checker last ran | Yes |
| `stats` | Routing entries, reference files, total lines | Yes |
| `urls` | Links to docs, GitHub, changelog, or other sources | Yes |
| `references` | Per-file `written_for` and `last_updated` | Yes |
| `docs_sitemap` | Known documentation pages (for diff detection) | Recommended for frameworks |
| `excluded_sections` | What was intentionally left out, with reason | Recommended |

### Versioning Rules

- **Skill version** follows semver: `MAJOR.MINOR.PATCH`
  - **MAJOR**: Restructure (routes change, files renamed/removed)
  - **MINOR**: New reference files added, files split, significant content updates
  - **PATCH**: Content fixes, typo corrections, TOC additions
- **Source version** (if tracking an upstream project) is stored as-is
- **Per-file `written_for`** tracks which source version (or date) each file targets
  - When the upstream source updates, you know exactly which files might be stale
  - For non-versioned sources (blog posts, specs, internal docs), use dates instead

---

## Step 4: CHANGELOG.md — Release History

CHANGELOG.md documents every release with structured categories.

### Template

```markdown
# <Skill Name> Changelog

## [<version>] — <YYYY-MM-DD>

**Source tracked: <upstream-version-or-date>** | **Author: <name>**

### Added
- **<Feature>** — <Description>

### Changed
- **<Component>** — <What changed>

### Split (Large Files -> Routers + Sub-files)
- **<filename>.md** (<line count>) -> router + `<dir>/<sub1>.md`, `<dir>/<sub2>.md`

### Fixed
- **<Issue>** — <What was wrong and how it was fixed>

### Stats
- <N> routing entries in SKILL.md
- <N> reference files
- ~<N> total lines

---

## [<previous-version>] — <YYYY-MM-DD>

...
```

### CHANGELOG.md Rules

| Rule | Detail |
|:-----|:-------|
| **Newest first** | Most recent version at the top |
| **Categories** | Use: Added, Changed, Split, Fixed, Removed, Deprecated |
| **Split category** | Dedicated category for file decomposition (unique to Skills Graph) |
| **Stats per version** | Always include routing entries, reference files, total lines |
| **Source version** | Note which upstream version/date is tracked in each release (if applicable) |
| **Author** | Include author name on each release |
| **Horizontal rule** | Separate versions with `---` |

### Changelog Categories Explained

| Category | When to Use |
|:---------|:------------|
| **Added** | New reference files, new topics, new scripts, new metadata |
| **Changed** | Updated content, modified routing table, enhanced descriptions |
| **Split** | When a large file (>500 lines) is decomposed into router + sub-files |
| **Fixed** | Broken references, incorrect code examples, stale content |
| **Removed** | Files deleted, topics removed |
| **Deprecated** | Features that will be removed in a future version |

---

## Step 5: AUDIT-REPORT.md — Self-Assessment

Every skill audits itself against the Skills Graph quality standards.

### Template

```markdown
# <Skill Name> — Architecture Audit Report

**Date:** <YYYY-MM-DD>
**Skill version:** <version> | **Source tracked:** <upstream-version-or-date>
**Stats:** <N> routing entries, <N> reference files, ~<N> lines

---

## How the Skills System Works (Progressive Disclosure)

| Level | What | When Loaded | Size Guideline |
|-------|------|-------------|----------------|
| **Metadata** | YAML `name` + `description` | Always in context | ~100 words |
| **SKILL.md body** | Main instructions/router | When skill triggers | <500 lines |
| **Bundled resources** | `references/`, `scripts/` | On demand via `Read` | Unlimited |

---

## Skill Structure

\`\`\`
<skill-name>/
|-- SKILL.md (<N> lines)
|-- references/ (<N> files, ~<N> lines)
    |-- <list key files with line counts>
    |-- <flag files >500 lines with warning>
    |-- <flag files using router pattern with checkmark>
\`\`\`

---

## What We're Doing Well

### 1. <Strength Title>
<Explanation of why this is good.>

### 2. <Strength Title>
<Explanation.>

---

## What Needs Improvement

### PRIORITY 1: <Issue>
<Description and action items.>

### PRIORITY 2: <Issue>
<Description and action items.>

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **SKILL.md size** | /5 | <Assessment> |
| **Progressive disclosure** | /5 | <Assessment> |
| **Reference splitting** | /5 | <Assessment> |
| **YAML frontmatter** | /5 | <Assessment> |
| **TOC on large files** | /5 | <Assessment> |
| **Description triggering** | /5 | <Assessment> |
| **Tooling & maintenance** | /5 | <Assessment> |
| **Overall** | **<stars>/5** | <Summary> |

---

## Recommended Action Plan

1. **Quick win** — <Action> (~time estimate)
2. **Medium effort** — <Action> (~time estimate)
3. **Quick win** — <Action> (~time estimate)
```

### Scorecard Criteria

| Category | 5/5 | 4/5 | 3/5 | 2/5 | 1/5 |
|:---------|:----|:----|:----|:----|:----|
| **SKILL.md size** | Under 80 lines | Under 100 lines | Under 200 lines | Under 500 lines | Over 500 lines |
| **Progressive disclosure** | All topics use routers correctly | Most topics routed, 1-2 flat | Half routed | Few routers | No routing |
| **Reference splitting** | All files under 500 lines | 1-2 oversized | 3-4 oversized | Many oversized | No splitting |
| **YAML frontmatter** | Correct on SKILL.md only, with license + metadata | Correct on SKILL.md only | Missing license or metadata | Frontmatter on reference files | No frontmatter |
| **TOC on large files** | All files >300 lines have TOC | 1-2 missing | Half missing | Most missing | No TOCs |
| **Description triggering** | Pushy, explicit triggers, broad coverage | Good triggers | Basic description | Vague | Missing |
| **Tooling & maintenance** | VERSION.json + script + changelog + audit | Missing one | Missing two | Only VERSION.json | None |

---

## Step 6: scripts/ — Maintenance Automation

Every skill needs an automated checker script. Adapt this template for your skill's domain.

### Template: check-updates.py

```python
#!/usr/bin/env python3
"""
<Skill Name> Update Checker
============================
Checks for upstream updates and validates skill integrity.

Usage:
    python scripts/check-updates.py              # Full report
    python scripts/check-updates.py --version    # Check upstream version (if applicable)
    python scripts/check-updates.py --stale      # Show stale files
    python scripts/check-updates.py --stale 60   # Custom threshold (days)
    python scripts/check-updates.py --integrity  # Verify routing table
    python scripts/check-updates.py --report     # Full report
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# --- Config (CHANGE THESE) ---
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
VERSION_FILE = SKILL_DIR / "VERSION.json"
REFERENCES_DIR = SKILL_DIR / "references"
SKILL_MD = SKILL_DIR / "SKILL.md"

PYPI_PACKAGE = "<package-name>"                    # <-- CHANGE
PYPI_JSON_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE}/json"
SOURCE_VERSION_KEY = "source_version_tracked"      # <-- CHANGE (e.g., "agno_version_tracked")
STALE_THRESHOLD_DAYS = 30


def load_version():
    with open(VERSION_FILE) as f:
        return json.load(f)


def check_version():
    """Compare tracked version against PyPI latest."""
    ver = load_version()
    tracked = ver[SOURCE_VERSION_KEY]
    print(f"\n{'='*60}")
    print(f"  VERSION CHECK")
    print(f"{'='*60}")
    print(f"  Skill version:     {ver['skill_version']}")
    print(f"  Tracked version:   {tracked}")

    try:
        req = Request(PYPI_JSON_URL, headers={"User-Agent": "skill-checker/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            latest = data["info"]["version"]
            print(f"  Latest on PyPI:    {latest}")
            if tracked == latest:
                print(f"\n  UP TO DATE")
                return True
            else:
                print(f"\n  UPDATE AVAILABLE: {tracked} -> {latest}")
                return False
    except (URLError, KeyError) as e:
        print(f"\n  Could not reach PyPI: {e}")
        return None


def check_stale(threshold_days=STALE_THRESHOLD_DAYS):
    """Find reference files not updated recently."""
    ver = load_version()
    refs = ver.get("references", {})
    cutoff = (datetime.now() - timedelta(days=threshold_days)).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  STALE REFERENCE CHECK (>{threshold_days} days)")
    print(f"{'='*60}")

    stale = []
    for ref, info in sorted(refs.items()):
        updated = info.get("last_updated", "unknown")
        if updated < cutoff:
            stale.append((ref, info.get("written_for", "?"), updated))

    if stale:
        print(f"\n  {len(stale)} reference(s) may need review:\n")
        for ref, wf, up in stale:
            print(f"  {ref:<40} written_for={wf}  updated={up}")
    else:
        print(f"\n  All references updated within {threshold_days} days")
    return len(stale) == 0


def check_integrity():
    """Verify all SKILL.md references exist on disk."""
    print(f"\n{'='*60}")
    print(f"  FILE INTEGRITY CHECK")
    print(f"{'='*60}")

    missing = []
    total = 0
    with open(SKILL_MD) as f:
        for line in f:
            if "references/" in line and ".md" in line:
                start = line.find("references/")
                if start >= 0:
                    end = line.find(".md", start) + 3
                    ref_path = line[start:end]
                    full_path = SKILL_DIR / ref_path
                    total += 1
                    if not full_path.exists():
                        missing.append(ref_path)

    if missing:
        print(f"\n  {len(missing)} BROKEN reference(s):")
        for m in missing:
            print(f"    MISSING: {m}")
    else:
        print(f"\n  All {total} references verified on disk")

    actual = list(REFERENCES_DIR.rglob("*.md"))
    print(f"  Total .md files in references/: {len(actual)}")
    return len(missing) == 0


def generate_report():
    print(f"\n{'#'*60}")
    print(f"  SKILL UPDATE REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#'*60}")

    v_ok = check_version()
    st_ok = check_stale()
    f_ok = check_integrity()

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Version:    {'Up to date' if v_ok else 'Update available'}")
    print(f"  Freshness:  {'All recent' if st_ok else 'Stale files found'}")
    print(f"  Integrity:  {'All valid' if f_ok else 'Broken refs'}")


def main():
    if not VERSION_FILE.exists():
        print("ERROR: VERSION.json not found.")
        sys.exit(1)

    args = sys.argv[1:]
    if not args or "--report" in args:
        generate_report()
    elif "--version" in args:
        check_version()
    elif "--stale" in args:
        days = STALE_THRESHOLD_DAYS
        for i, a in enumerate(args):
            if a == "--stale" and i + 1 < len(args):
                try:
                    days = int(args[i + 1])
                except ValueError:
                    pass
        check_stale(days)
    elif "--integrity" in args:
        check_integrity()
    else:
        print(f"Usage: python {sys.argv[0]} [--version|--stale [days]|--integrity|--report]")


if __name__ == "__main__":
    main()
```

### What the Script Checks

| Check | What It Does |
|:------|:-------------|
| `--version` | Compares `VERSION.json` tracked version against upstream latest (PyPI, GitHub, etc.) |
| `--stale [days]` | Finds reference files older than N days (default 30) |
| `--integrity` | Verifies every file referenced in SKILL.md routing table exists on disk |
| `--report` | Runs all checks and prints a summary |

### Extending for Your Domain

- **PyPI-based projects** (frameworks, libraries): Use the PyPI JSON API as shown in the template
- **GitHub-only projects**: Replace PyPI check with GitHub Releases API
- **API-versioned services** (Stripe, Twilio): Check the API changelog endpoint
- **Docs sitemap checking**: If the upstream has a sitemap, add sitemap diffing (see Agno skill for example)
- **Non-versioned knowledge** (design patterns, standards): Skip `--version`, rely on `--stale` and `--integrity`
- **Custom checks**: Add domain-specific validation (e.g., import verification, link checking, schema validation)

---

## Step 7: metadata/ — Source Tracking (Optional)

The `metadata/` directory tracks where reference content came from. Useful for auditing and updates.

### sources.json Template

```json
{
  "primary_sources": [
    {
      "name": "<Source Official Docs>",
      "url": "<docs-url>",
      "type": "official_docs",
      "topics": ["all"]
    },
    {
      "name": "<Source GitHub/Repository>",
      "url": "<github-url>",
      "type": "source_code",
      "topics": ["api", "examples"]
    }
  ],
  "reference_sources": {
    "<filename>.md": [
      "<source-url-1>",
      "<source-url-2>"
    ]
  },
  "last_updated": "<YYYY-MM-DD>"
}
```

### version-tracking.json Template (Alternative to VERSION.json)

Some skills use `metadata/version-tracking.json` instead of a root `VERSION.json`. Both are valid. The root `VERSION.json` is preferred because it's immediately visible and scripts expect it there.

If you use `metadata/version-tracking.json`, include the same fields as `VERSION.json` plus optional extras:

```json
{
  "skill_version": "1.0.0",
  "source_version": "<upstream-version>",
  "source_package": "<package-name-if-applicable>",
  "last_checked": "<ISO-8601>",
  "last_updated": "<ISO-8601>",
  "created": "<ISO-8601>",
  "update_history": [
    {
      "date": "<YYYY-MM-DD>",
      "version": "<version>",
      "changes": "<description>"
    }
  ],
  "reference_counts": {
    "<category>": 0
  },
  "total_reference_files": 0,
  "staleness_threshold_days": 30
}
```

---

## Reference File Patterns

### Pattern 1: Leaf Node (Simple Topic)

For topics that fit in 200-500 lines.

```
references/
+-- reasoning.md              # Single file, 200-400 lines
```

Structure inside:
```markdown
# Topic Title

<Summary paragraph>

## Quick Start
<Minimal code example>

## Section A
<Detailed content>

## Section B
<More content>

## Key Imports
<Common imports for this topic>
```

### Pattern 2: Router + Sub-Files (Complex Topic)

For topics that would exceed 500 lines.

```
references/
|-- tools.md                  # Router node (~50-80 lines)
+-- tools/                    # Sub-directory
    |-- creating-tools.md     # Leaf (~300 lines)
    |-- custom-toolkits.md    # Leaf (~250 lines)
    |-- advanced.md           # Leaf (~300 lines)
    |-- mcp-tools.md          # Leaf (~200 lines)
    +-- builtin-search.md     # Leaf (~200 lines)
```

The router file (`tools.md`) contains:
1. One-paragraph summary
2. Sub-References table with "Read When" conditions
3. Quick Start code (enough for simple cases)
4. Key Imports

### Pattern 3: Numbered Sequence (Linear Learning Path)

For domains where topics build on each other sequentially.

```
references/
|-- 01-getting-started.md
|-- 02-core-concepts.md
|-- 03-basic-patterns.md
|-- 04-advanced-patterns.md
|-- 05-production-guide.md
+-- ...
```

Best for: tutorials, step-by-step guides, progressive learning paths.
The SKILL.md routing table still uses intent-based routing, not sequential order.

### Pattern 4: Category Groups

For large skills, group related references:

```
references/
|-- core/
|   |-- agents.md
|   |-- teams.md
|   +-- workflows.md
|-- tools/
|   |-- creating-tools.md
|   +-- builtin-search.md
|-- storage/
|   |-- database.md
|   +-- memory.md
+-- deploy/
    |-- docker.md
    +-- cloud.md
```

The router in SKILL.md still points to the full relative path: `references/core/agents.md`.

---

## Naming Conventions

| Element | Convention | Examples |
|:--------|:-----------|:---------|
| **Skill directory** | lowercase, hyphens | `agno/`, `api-design-patterns/`, `react-performance/` |
| **SKILL.md `name`** | lowercase, hyphens, max 64 chars. **Must exactly match folder name.** | `agno`, `api-design-patterns`, `react-performance` |
| **Reference files** | lowercase, hyphens | `tools.md`, `getting-started.md` |
| **Sub-directories** | Match parent router name | `tools/`, `memory/`, `database/` |
| **Numbered files** | `NN-topic.md` or `NNa-subtopic.md` | `11-workflows.md`, `11a-executors.md` |
| **Scripts** | `check-updates.py`, `check-freshness.py` | Descriptive, hyphenated |
| **Tags in metadata** | lowercase, hyphens | `"ai-agents"`, `"multi-agent"` |

---

## Size Rules

These are hard rules, not guidelines.

| What | Limit | Action When Exceeded |
|:-----|:------|:---------------------|
| **SKILL.md** | 100 lines max | Move content to references |
| **Router node** | 100 lines max | Only routing table + quick start |
| **Leaf node** | 500 lines max | Split into router + sub-files |
| **Leaf node >300 lines** | Must have TOC | Add `## Contents` section |
| **Description** | 1024 characters max | Condense trigger keywords |

### TOC Format

When a file exceeds 300 lines, add a TOC immediately after the title:

```markdown
# Topic Title

<Summary paragraph>

## Contents

- [Section A](#section-a)
- [Section B](#section-b)
- [Section C](#section-c)
- [Section D](#section-d)

---

## Section A
...
```

---

## Quality Checklist

Run through this before publishing your skill:

### Structure
- [ ] `SKILL.md` exists with YAML frontmatter
- [ ] `SKILL.md` `name` field exactly matches the folder name (most common mistake)
- [ ] `SKILL.md` is under 100 lines
- [ ] `SKILL.md` has `name`, `description`, `license`, `metadata` in frontmatter
- [ ] `SKILL.md` description includes MANDATORY TRIGGERS
- [ ] `references/` directory exists with knowledge files
- [ ] No reference file has YAML frontmatter
- [ ] All files referenced in SKILL.md routing table exist on disk

### Size Compliance
- [ ] No reference file exceeds 500 lines without being split
- [ ] All files >300 lines have `## Contents` TOC
- [ ] Router nodes are under 100 lines
- [ ] Leaf nodes are 200-500 lines

### Knowledge Quality
- [ ] Every reference file has at least one actionable example (code, config, template, checklist, decision tree)
- [ ] Examples are complete and usable (not fragments)
- [ ] Structured data uses consistent markdown table format
- [ ] Cross-references link to related files where appropriate

### Version Tracking
- [ ] `VERSION.json` exists with all required fields
- [ ] Per-file `written_for` metadata is populated
- [ ] `CHANGELOG.md` exists with at least one release
- [ ] `scripts/check-updates.py` exists and runs without errors

### Architecture
- [ ] `AUDIT-REPORT.md` exists with scorecard
- [ ] All scorecard categories are honestly assessed
- [ ] Improvement priorities are listed

---

## Common Mistakes

### 1. `name` field doesn't match the folder name
**Wrong:** Folder is `agno-skill/` but frontmatter says `name: agno`.
**Right:** Folder is `agno/` and frontmatter says `name: agno`. They must be identical.

### 2. Putting knowledge in SKILL.md
**Wrong:** SKILL.md has 300 lines of code examples and explanations.
**Right:** SKILL.md has 69 lines — just the routing table and install info.

### 3. YAML frontmatter on reference files
**Wrong:** Every .md file starts with `---\nname: ...\n---`
**Right:** Only SKILL.md has frontmatter. References start with `# Title`.

### 4. Flat dumps without routing guidance
**Wrong:** 40 reference files with no routing table. AI guesses which to load.
**Right:** Every reference file is reachable from the SKILL.md routing table with "Read When" conditions.

### 5. Vague descriptions
**Wrong:** `"A skill for building AI agents."`
**Right:** `"Build AI agents... MANDATORY TRIGGERS: Agno, agno-agi... When in doubt, use it."`

### 6. No version tracking
**Wrong:** No VERSION.json. No way to know if content is stale.
**Right:** VERSION.json with per-file `written_for` metadata. Automated staleness detection.

### 7. Monolithic reference files
**Wrong:** `database.md` is 1,200 lines covering 18 backends.
**Right:** `database.md` is a 50-line router pointing to `database/backends.md`, `database/chat-history.md`, `database/session-memory.md`.

### 8. Missing TOCs on large files
**Wrong:** 450-line file with no table of contents. AI reads the whole thing.
**Right:** `## Contents` section with anchor links at the top.

### 9. No maintenance automation
**Wrong:** Manually checking if the upstream source has changed.
**Right:** `python scripts/check-updates.py --report` tells you what's stale.

---

## Example from Production

### Agno Skill (v1.2.0) — Framework Skill

| Metric | Value |
|:-------|:------|
| SKILL.md lines | 69 (pure router) |
| Routing entries | 34 |
| Reference files | 116 |
| Total lines | 23,431 |
| Router nodes | 12 |
| Leaf nodes | 104 |
| Source tracked | Agno framework v2.5.3 |

**Key patterns used:**
- Intent-based routing with "Read When" column
- Router + sub-files for tools (11 sub-files), memory (3), database (3), guardrails (3), context-mgmt (5), agentos (2), evals (4), hooks (2), workflow-patterns (3), input-output (3)
- Aggressive description with MANDATORY TRIGGERS
- VERSION.json with per-file `written_for` metadata
- Automated PyPI + sitemap + staleness + integrity checking
- Self-audit with 7-category scorecard

This is a large skill (23k+ lines, 116 files) that demonstrates the full power of the router + sub-files pattern. Every technique described in this guide is used in production here.

The standard is flexible — the core requirements (SKILL.md router, reference graph, version tracking, maintenance automation) can be implemented in different ways depending on your skill's scope, domain, and complexity. A 10-file skill about API design patterns and a 116-file skill about a framework both follow the same structure.

---

## Creating a Skill — Step-by-Step Instructions

> **For AI agents:** Follow these steps sequentially. Each step must be completed before moving to the next. The output of this process is a complete, production-ready Skills Graph skill.

### 1. Research Phase
- Study the source material thoroughly (official docs, API references, specs, guides, or domain knowledge)
- Identify the major topics — aim for 10-30 routing entries
- Decide which topics need router + sub-files (>500 lines of content) vs. single leaf files
- Note the source version, docs URL, and any upstream changelog

### 2. Scaffold the Directory

```bash
mkdir -p <skill-name>/references <skill-name>/scripts
touch <skill-name>/SKILL.md
touch <skill-name>/VERSION.json
touch <skill-name>/CHANGELOG.md
touch <skill-name>/AUDIT-REPORT.md
```

### 3. Write SKILL.md First
- Start with YAML frontmatter: `name` (**must exactly match folder name**), `description` (with MANDATORY TRIGGERS), `license`, `metadata`
- Write the routing table mapping every topic to a reference file with "Read When" conditions
- Add setup/install instructions if applicable
- Add skill install instructions (Smithery + manual paths)
- **Keep it under 100 lines**

### 4. Write Reference Files
- Start with the most important/foundational topics
- Write **leaf nodes** for simple topics (200-500 lines each)
- Write **router nodes** for complex topics (under 100 lines), then their sub-files
- Include actionable examples in every file (code, configs, templates, decision trees)
- Add `## Contents` TOC to any file >300 lines
- Split any file >500 lines into a router + sub-files

### 5. Create VERSION.json
- Fill in `skill_name`, `skill_version`, stats, urls
- If tracking an upstream project: add `source_version_tracked` and `content_snapshot_date`
- Populate per-file `references` with `written_for` and `last_updated` for every reference file

### 6. Create CHANGELOG.md
- Document the initial release with Added category
- Include stats: routing entries, reference files, total lines

### 7. Create check-updates.py
- Copy the script template from Step 6 of this guide
- Update the config section for your skill's domain
- Run it to verify: `python scripts/check-updates.py --report`

### 8. Create AUDIT-REPORT.md
- Assess your skill honestly across the 7 scorecard categories
- List strengths and areas for improvement
- Include the skill's directory structure diagram

### 9. Validate

```bash
python scripts/check-updates.py --integrity   # All references exist on disk
python scripts/check-updates.py --stale       # No stale files
```

Manually verify:
- SKILL.md is under 100 lines
- No reference file has YAML frontmatter
- All files >300 lines have TOC
- No file >500 lines without being split

### 10. Update the Root README.md (MANDATORY)

**Every new skill MUST update the root `README.md`.** This is not optional — the README is the single source of truth for the repository.

Update these specific sections:

**a) Badge counts in the header:**
```html
<!-- Update the skills count badge -->
<a href="#-skills-catalog"><img src="https://img.shields.io/badge/Skills-N%20Production%20Ready-orange.svg" alt="Skills"></a>
<!-- Update the knowledge lines badge -->
<a href="#-the-technique-progressive-reference-architecture"><img src="https://img.shields.io/badge/Knowledge-N%2C000%2B%20Lines-red.svg" alt="Lines"></a>
```

**b) Overview table:**
```html
<tr><td><strong>Skills</strong></td><td>N production-ready (list all skill names)</td></tr>
<tr><td><strong>Total Knowledge</strong></td><td>N+ lines across N reference files</td></tr>
```

**c) Skills Catalog table — add a new row:**
```markdown
| N | **[Your Skill](skill-folder/)** | [Source](url) vX.Y.Z | `1.0.0` | N | N,NNN | Production |
```
Update the **totals row** at the bottom of the table with new sums for files and lines.

**d) Repository Structure — add the new skill directory listing** in the `skills/` section.

**e) Installation section — add install command** for the new skill:
```bash
npx skills add AbhishekSharma-17/skills-graph --skill your-skill-name
```

**f) Maintenance section — add the check command** for the new skill:
```bash
python skills/your-skill-name/scripts/check-updates.py --report
```

**How to calculate totals:**
- Count all `.md` files in all `references/` directories across all skills
- Sum line counts from all reference files across all skills
- Count total routing entries from all SKILL.md files

### 11. Publish
- Push to the repository
- Optionally publish to Smithery: `smithery publish`
- Verify the root README.md is up to date with your new skill

---

## What Can Be a Skill?

Skills Graph is not limited to frameworks or libraries. You can create a skill for **any knowledge domain**:

| Domain | Example Skills | Key Difference |
|:-------|:---------------|:---------------|
| **Frameworks** | Agno, LangGraph, CrewAI, Next.js | Track upstream version via PyPI/npm. Code-heavy references. |
| **Libraries** | Pandas, Pydantic, SQLAlchemy | Track upstream version. API-focused references. |
| **APIs** | Stripe, Twilio, GitHub API | Track API version. Endpoint-focused references. |
| **Design Patterns** | API design, system design, microservices | No upstream version. Concept-focused. Use dates for freshness. |
| **Coding Standards** | Python style guide, TypeScript patterns | No upstream version. Rule-focused references. |
| **Internal Knowledge** | Company architecture, team conventions | Track internal doc revision. |
| **Workflow Guides** | CI/CD pipelines, deployment procedures | Process-focused. Checklist-heavy references. |
| **Domain Knowledge** | ML/AI concepts, security practices, DevOps | Mix of concepts and practical references. |

The structure is identical for all — only the content and version tracking strategy change.

---

*Built with the Skills Graph methodology. MIT License.*
