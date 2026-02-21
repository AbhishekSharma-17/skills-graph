# Skills Graph — Starter Template

This is a **copy-paste-and-rename** starter for creating a new skill using the Skills Graph methodology.

## Quick Start

```bash
# 1. Copy the template
cp -r _template/ my-new-skill/

# 2. Rename and customize
cd my-new-skill/
# Edit SKILL.md — set name, description, triggers, routing table
# Edit VERSION.json — set source version, URLs, reference metadata
# Replace template reference files with your actual content
# Fill in CHANGELOG.md and AUDIT-REPORT.md

# 3. Verify integrity
python scripts/check-updates.py --integrity
```

## What's Included

| File | Purpose | First Action |
|------|---------|-------------|
| `SKILL.md` | Router with routing table | Set name, description, triggers, add your references |
| `VERSION.json` | Version + per-file tracking | Set your source version, URLs, file metadata |
| `CHANGELOG.md` | Release history | Fill in your v1.0.0 entry |
| `AUDIT-REPORT.md` | Quality scorecard | Score yourself honestly after writing content |
| `scripts/check-updates.py` | Maintenance automation | Set `UPSTREAM_VERSION_URL` for your source |
| `references/00-overview.md` | Leaf node template | Replace with your overview content |
| `references/01-topic-a.md` | Leaf node template | Replace with your first topic |
| `references/02-topic-b.md` | Leaf node template | Replace with your second topic |
| `references/03-topic-c.md` | **Router node** template | Replace with a complex topic that needs sub-files |
| `references/topic-c/c1-detail.md` | Sub-file template | Replace with detail content |

## Template Types

- **Leaf Node** (01-topic-a.md, 02-topic-b.md) — Contains actual content. Use for focused topics.
- **Router Node** (03-topic-c.md) — Links to sub-files. Use for complex topics with 3+ sub-aspects.

## Rules Reminder

- SKILL.md: under 100 lines, pure router
- Leaf files: under 500 lines (split if exceeded)
- Router files: under 80 lines
- Only SKILL.md gets YAML frontmatter
- Run `check-updates.py --integrity` before submitting

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full standard.
