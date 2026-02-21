# ms-agent-framework Changelog

## [1.0.0] — 2026-02-21

**Source tracked: 1.0.0b260130** | **Author: Abhishek Sharma**

### Added
- **`VERSION.json`** — Added version tracking metadata.
- **`CHANGELOG.md`** — Added release history.
- **`AUDIT-REPORT.md`** — Added architectural self-assessment.
- **`00-framework-overview.md`** — Extracted overview content from `SKILL.md`.

### Changed
- **`SKILL.md`** — Restructured to meet the <100 lines requirement. Grouped routing entries and added YAML frontmatter.

### Split (Large Files -> Routers + Sub-files)
- **`SKILL.md`** (231 lines) -> `SKILL.md` (66 lines) + `references/00-framework-overview.md` (102 lines).

### Stats
- 22 routing entries in SKILL.md
- 62 reference files
- ~10000 total lines
