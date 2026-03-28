# Skills Graph — Download & Install Commands

> Quick reference for downloading and installing skills from this repository.

## Quick Install (Copy-Paste)

### Install All Skills

```bash
npx skills add AbhishekSharma-17/skills-graph
```

### Install All Skills Globally

```bash
npx skills add AbhishekSharma-17/skills-graph -g
```

### List Available Skills

```bash
npx skills add AbhishekSharma-17/skills-graph --list
```

---

## Install Individual Skills

### AI/ML Frameworks

```bash
# Agno — AI agent framework (Python) — 116 files, 23K lines
npx skills add AbhishekSharma-17/skills-graph --skill agno

# MS Agent Framework — Microsoft Agent Framework (Python) — 61 files, 14K lines
npx skills add AbhishekSharma-17/skills-graph --skill ms-agent-framework

# Claude Agent SDK — Build AI agents with Claude (Python + TypeScript) — 16 files, 5.8K lines
npx skills add AbhishekSharma-17/skills-graph --skill claude-agent-sdk
```

### Web & Backend Frameworks

```bash
# Hono — Ultrafast web framework for edge runtimes (TypeScript) — 12 files, 3.4K lines
npx skills add AbhishekSharma-17/skills-graph --skill hono

# Trigger.dev — Background jobs & workflows (TypeScript) — 11 files, 3.5K lines
npx skills add AbhishekSharma-17/skills-graph --skill trigger-dev
```

### ORMs & Databases

```bash
# Drizzle ORM — Type-safe ORM for PostgreSQL, MySQL, SQLite (TypeScript) — 12 files, 3.5K lines
npx skills add AbhishekSharma-17/skills-graph --skill drizzle-orm
```

### TypeScript Tooling

```bash
# Zod — Schema validation with static type inference (TypeScript) — 13 files, 3.7K lines
npx skills add AbhishekSharma-17/skills-graph --skill zod
```

### Web Development

```bash
# Remotion Prompt Generator — Video creation in React — 15 files, 2.7K lines
npx skills add AbhishekSharma-17/skills-graph --skill remotion-prompt-generator
```

---

## Alternative Install Methods

### Via Smithery

```bash
smithery install agno
smithery install ms-agent-framework
smithery install remotion-prompt-generator
smithery install trigger-dev
smithery install drizzle-orm
smithery install hono
smithery install zod
smithery install claude-agent-sdk
```

### Via Install Script

```bash
# Interactive menu
./install/install-skills.sh

# Install all
./install/install-skills.sh --all

# Install specific skill
./install/install-skills.sh --skill claude-agent-sdk

# Install globally
./install/install-skills.sh --global

# List available
./install/install-skills.sh --list
```

### Manual Install

Copy the skill folder to your platform's skill directory:

| Platform | Project Path | Global Path |
|:---------|:-------------|:------------|
| **Claude Code** | `.claude/skills/<skill>/` | `~/.claude/skills/<skill>/` |
| **Gemini CLI** | `.gemini/skills/<skill>/` | `~/.gemini/skills/<skill>/` |
| **Cursor** | `.cursor/skills/<skill>/` | `~/.cursor/skills/<skill>/` |
| **Windsurf** | `.windsurf/skills/<skill>/` | `~/.codeium/windsurf/skills/<skill>/` |
| **Codex** | `.codex/skills/<skill>/` | `~/.codex/skills/<skill>/` |
| **Trae** | `.trae/skills/<skill>/` | `~/.trae/skills/<skill>/` |

Example:

```bash
# Clone the repo
git clone https://github.com/AbhishekSharma-17/skills-graph.git

# Copy a skill to Claude Code (project-level)
cp -r skills-graph/skills/claude-agent-sdk .claude/skills/claude-agent-sdk

# Copy a skill to Claude Code (global)
cp -r skills-graph/skills/claude-agent-sdk ~/.claude/skills/claude-agent-sdk
```

---

## Search the Ecosystem

```bash
# Find skills across all repositories
npx skills find

# Search for specific topics
npx skills find react
npx skills find agent
npx skills find typescript
```

---

## Manage Installed Skills

```bash
# List installed skills
npx skills list

# Update a skill
npx skills update agno

# Remove a skill
npx skills remove agno
```

---

## Skill Summary Table

| # | Skill | Domain | Files | Lines | Install Command |
|:-:|:------|:-------|:-----:|:-----:|:----------------|
| 1 | agno | AI/ML Frameworks | 116 | 23K | `npx skills add AbhishekSharma-17/skills-graph --skill agno` |
| 2 | ms-agent-framework | AI/ML Frameworks | 61 | 14K | `npx skills add AbhishekSharma-17/skills-graph --skill ms-agent-framework` |
| 3 | remotion-prompt-generator | Web Development | 15 | 2.7K | `npx skills add AbhishekSharma-17/skills-graph --skill remotion-prompt-generator` |
| 4 | trigger-dev | Background Jobs | 11 | 3.5K | `npx skills add AbhishekSharma-17/skills-graph --skill trigger-dev` |
| 5 | drizzle-orm | ORMs & Databases | 12 | 3.5K | `npx skills add AbhishekSharma-17/skills-graph --skill drizzle-orm` |
| 6 | hono | Web Frameworks | 12 | 3.4K | `npx skills add AbhishekSharma-17/skills-graph --skill hono` |
| 7 | zod | TypeScript Tooling | 13 | 3.7K | `npx skills add AbhishekSharma-17/skills-graph --skill zod` |
| 8 | claude-agent-sdk | AI/ML Frameworks | 16 | 5.8K | `npx skills add AbhishekSharma-17/skills-graph --skill claude-agent-sdk` |
