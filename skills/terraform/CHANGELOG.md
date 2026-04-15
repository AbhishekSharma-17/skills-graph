# Changelog — Terraform Skill

All notable changes to this skill are documented here.

Format: `[Skill Version] - YYYY-MM-DD (Source vX.Y.Z)`

---

## [1.0.0] - 2026-04-16 (Source v1.14.8)

### Added
- Initial skill creation tracking Terraform v1.14.8 (covers features through 1.10+ ephemeral resources, 1.9+ cross-variable validation, 1.7+ test mocks, 1.5+ import/check blocks).
- 13 reference files covering the full Terraform surface:
  - `00-overview.md` — what Terraform is, installation, core CLI, OpenTofu comparison
  - `01-configuration-language.md` — HCL syntax, types, expressions, template directives
  - `02-providers.md` — provider config, version constraints, aliases, lock file
  - `03-resources.md` — resource blocks, addresses, imports, provisioners, replacements
  - `04-variables-and-outputs.md` — inputs, outputs, locals, validation, ephemeral values
  - `05-state.md` — backends, S3/GCS/Azure/HCP, locking, workspaces, drift, recovery
  - `06-modules.md` — structure, sources, versioning, composition, registry, authoring
  - `07-data-sources.md` — queries, IAM policy docs, secrets, remote state, ephemeral data
  - `08-lifecycle-and-meta-arguments.md` — count, for_each, depends_on, lifecycle, dynamic
  - `09-functions-and-expressions.md` — 100+ functions, for/splat expressions, console
  - `10-testing-and-validation.md` — validation blocks, preconditions, `terraform test`, checkov, sentinel, opa, tflint
  - `11-cicd-patterns.md` — GitHub Actions, GitLab, Atlantis, HCP Terraform, OIDC, drift detection
  - `12-best-practices.md` — project structure, secrets, security defaults, review checklist
- `VERSION.json` with per-file source tracking.
- `CHANGELOG.md` with initial release notes.
- `AUDIT-REPORT.md` with self-assessed quality scorecard.
- `scripts/check-updates.py` with Terraform version checking via GitHub Releases API.

### Reference Files

| File | Lines | Type |
|------|-------|------|
| `00-overview.md` | ~165 | Leaf |
| `01-configuration-language.md` | ~245 | Leaf |
| `02-providers.md` | ~235 | Leaf |
| `03-resources.md` | ~260 | Leaf |
| `04-variables-and-outputs.md` | ~265 | Leaf |
| `05-state.md` | ~265 | Leaf |
| `06-modules.md` | ~305 | Leaf (with TOC) |
| `07-data-sources.md` | ~275 | Leaf |
| `08-lifecycle-and-meta-arguments.md` | ~300 | Leaf (with TOC) |
| `09-functions-and-expressions.md` | ~345 | Leaf (with TOC) |
| `10-testing-and-validation.md` | ~340 | Leaf (with TOC) |
| `11-cicd-patterns.md` | ~355 | Leaf (with TOC) |
| `12-best-practices.md` | ~325 | Leaf (with TOC) |

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~3,680

---

<!--
Add new entries above this line. Format for subsequent releases:

## [1.1.0] - YYYY-MM-DD (Source vX.Y.Z)

### Added
- New reference files

### Changed
- Updated files for new source version

### Fixed
- Broken references, incorrect content

### Removed
- Deprecated content
-->
