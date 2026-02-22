# Security Policy

## Why Security Matters for Agent Skills

Agent Skills are loaded directly into AI coding assistants and can contain executable scripts. A compromised or malicious skill can influence an AI agent's behavior across an entire project. Skills Graph takes this threat seriously.

## Supported Versions

| Version          | Supported |
| ---------------- | --------- |
| Latest on `main` | Yes       |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

### How to Report

1. **Email:** Send a detailed report to **2001abhishek17@gmail.com**
2. **GitHub:** Use [GitHub's private security advisory](https://github.com/AbhishekSharma-17/skills-graph/security/advisories/new) feature

### Include in Your Report

- Description of the vulnerability
- Which skill(s) and file(s) are affected
- Steps to reproduce
- Potential impact (e.g., prompt injection, data exfiltration, malicious code execution)
- Suggested fix (if available)

### Response Timeline

| Stage              | Target                                |
| ------------------ | ------------------------------------- |
| Acknowledgment     | Within 48 hours                       |
| Initial assessment | Within 1 week                         |
| Fix or mitigation  | Within 30 days (complexity dependent) |

## Security Model

### What Skills Graph Skills Contain

- **Markdown files** (`.md`) — Knowledge and instructions for AI agents. No executable code.
- **Python scripts** (`scripts/`) — Maintenance utilities (version checking, link validation). These run locally and make only read-only HTTP requests to public APIs (PyPI, docs sitemaps).
- **JSON metadata** — Version tracking and source mappings. Data only.

### What Skills Graph Skills Do NOT Contain

- Authentication credentials or API keys
- Network requests to private endpoints
- File system modifications outside the skill directory
- Dependencies on external packages (scripts use only Python stdlib)
- Obfuscated or encoded instructions

## Security Guidelines for Contributors

### Reference Files (Markdown)

- Never include instructions that tell the AI agent to bypass security controls
- Never include prompts designed to override system instructions
- Never embed hidden instructions (white text, zero-width characters, HTML comments with directives)
- Never include links to known malicious domains
- All content must be human-readable and auditable

### Scripts

- Use only Python standard library (no `pip install` required)
- Make only read-only HTTP requests to well-known public APIs
- Never write to files outside the skill directory
- Never execute shell commands or subprocess calls
- Never access environment variables containing secrets
- Include clear docstrings explaining what each script does

### SKILL.md Routing Tables

- All referenced files must exist in the skill directory (verified by `check-updates.py --integrity`)
- "Read When" conditions must be honest — no social engineering triggers
- Trigger keywords in the description must accurately reflect the skill's domain

## Automated Security Measures

Every skill built with the Skills Graph methodology includes:

- **Integrity checking** — `scripts/check-updates.py --integrity` verifies all routing table references resolve to actual files
- **Version tracking** — `VERSION.json` records exactly which upstream version each reference was written for, enabling rapid triage when upstream vulnerabilities are disclosed
- **Audit reports** — `AUDIT-REPORT.md` includes a security-relevant quality scorecard

## Known Attack Vectors for Agent Skills

Based on published research (as of Feb 2026):

| Vector                                         | Mitigation in Skills Graph                                                             |
| ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Prompt injection in skill content**          | All reference files are plain Markdown; no dynamic content generation. Review all PRs. |
| **Malicious scripts**                          | Scripts restricted to Python stdlib, read-only HTTP, no subprocess.                    |
| **Dependency confusion**                       | Zero external dependencies. Scripts are self-contained.                                |
| **Stale references leading to wrong behavior** | VERSION.json per-file tracking + automated staleness checks.                           |
| **Hidden instructions**                        | All content is human-readable Markdown. CI can lint for hidden text patterns.          |

## Verification

Before installing any skill from this repository, you can verify it:

```bash
# Check file integrity (all routing references resolve)
python <skill>/scripts/check-updates.py --integrity

# Review the audit report
cat <skill>/AUDIT-REPORT.md

# Check version freshness
python <skill>/scripts/check-updates.py --report
```

## Contact

For security questions that are not vulnerability reports, open a regular [GitHub issue](https://github.com/AbhishekSharma-17/skills-graph/issues).
