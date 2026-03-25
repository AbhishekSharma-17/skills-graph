#!/bin/bash
# skills-commands.sh — Quick reference for skills-graph repo commands
# Repository: AbhishekSharma-17/skills-graph
# Remote: git@github-personal:AbhishekSharma-17/skills-graph.git

REPO_DIR="/Users/abhisheksharma/Documents/Genaiprotos/Developer/skills-graph"

# ═══════════════════════════════════════════════════════════════
# NPX SKILLS COMMANDS (for users installing skills)
# ═══════════════════════════════════════════════════════════════

# Install skills from the repo
# npx skills install AbhishekSharma-17/skills-graph/skills/agno
# npx skills install AbhishekSharma-17/skills-graph/skills/ms-agent-framework
# npx skills install AbhishekSharma-17/skills-graph/skills/remotion-prompt-generator

# List installed skills
# npx skills list

# Find skills in the ecosystem
# npx skills find <query>

# Update an installed skill
# npx skills update <skill-name>

# Remove a skill
# npx skills remove <skill-name>

# ═══════════════════════════════════════════════════════════════
# SKILL MAINTENANCE COMMANDS (per-skill)
# ═══════════════════════════════════════════════════════════════

# Full update report
# python skills/<skill-name>/scripts/check-updates.py --report

# Check PyPI/npm version only
# python skills/<skill-name>/scripts/check-updates.py --version

# Check docs sitemap for changes
# python skills/<skill-name>/scripts/check-updates.py --sitemap

# Find stale reference files (>N days)
# python skills/<skill-name>/scripts/check-updates.py --stale 30

# Verify routing table integrity (all refs exist on disk)
# python skills/<skill-name>/scripts/check-updates.py --integrity

# ═══════════════════════════════════════════════════════════════
# GIT COMMANDS
# ═══════════════════════════════════════════════════════════════

# Pull latest
# cd $REPO_DIR && git pull origin main

# Add and commit a new skill
# git add skills/<skill-name>/ SKILLS_REGISTRY.json README.md
# git commit -m "feat: Add \`<skill-name>\` skill — <description>"
# git push origin main

# Check status
# git status && git log --oneline -5

# ═══════════════════════════════════════════════════════════════
# VALIDATION COMMANDS
# ═══════════════════════════════════════════════════════════════

# Count lines in a skill
# find skills/<skill-name>/references -name "*.md" | xargs wc -l

# Check for files over 500 lines (violation)
# find skills/<skill-name>/references -name "*.md" -exec sh -c 'lines=$(wc -l < "$1"); [ "$lines" -gt 500 ] && echo "VIOLATION: $1 ($lines lines)"' _ {} \;

# Verify SKILL.md name matches folder
# grep "^name:" skills/<skill-name>/SKILL.md

# List all skills
# ls -d skills/*/

# Count total reference files across all skills
# find skills/ -name "*.md" -path "*/references/*" | wc -l

# Count total lines across all skills
# find skills/ -name "*.md" -path "*/references/*" -exec cat {} + | wc -l

# ═══════════════════════════════════════════════════════════════
# BATCH OPERATIONS (run across all skills)
# ═══════════════════════════════════════════════════════════════

# Integrity check all skills
# for skill in skills/*/; do echo "=== $(basename $skill) ==="; python "${skill}scripts/check-updates.py" --integrity 2>/dev/null || echo "No check script"; done

# Find all violations (files >500 lines) across all skills
# find skills/ -name "*.md" -path "*/references/*" -exec sh -c 'lines=$(wc -l < "$1"); [ "$lines" -gt 500 ] && echo "VIOLATION: $1 ($lines lines)"' _ {} \;

# Show skill summary
# for skill in skills/*/; do name=$(basename $skill); files=$(find "$skill/references" -name "*.md" 2>/dev/null | wc -l); lines=$(find "$skill/references" -name "*.md" -exec cat {} + 2>/dev/null | wc -l); echo "$name: $files files, $lines lines"; done
