## Summary

<!-- Briefly describe what this PR does -->

## Type

- [ ] New skill
- [ ] Skill improvement (new/updated reference files)
- [ ] Bug fix (broken reference, routing error)
- [ ] Infrastructure (CI, templates, scripts)
- [ ] Documentation

## Skill Checklist

<!-- For new skills or skill modifications, verify all items -->

### Required
- [ ] `SKILL.md` exists and is under 100 lines (pure router)
- [ ] `SKILL.md` has valid YAML frontmatter (`name`, `description`)
- [ ] Description includes explicit trigger keywords
- [ ] Every file in the routing table exists on disk
- [ ] `VERSION.json` present with `skill_version` and source tracking
- [ ] `CHANGELOG.md` present with at least one entry
- [ ] `AUDIT-REPORT.md` present with quality scorecard

### Quality
- [ ] Reference files follow leaf node or router node patterns
- [ ] No file exceeds 500 lines (split into router + sub-files if needed)
- [ ] Files over 300 lines have a table of contents
- [ ] Router files have "Sub-References" tables
- [ ] No duplicate content across files
- [ ] Naming follows conventions (`XX-topic-name.md`)

### Maintenance
- [ ] `scripts/check-updates.py` (or equivalent) present and working
- [ ] Ran `check-updates.py --integrity` — all references valid
- [ ] Ran `check-updates.py --report` — no critical issues

### Security
- [ ] No credentials, API keys, or secrets in any file
- [ ] Scripts use only Python standard library
- [ ] No hidden instructions or prompt injection patterns
- [ ] All content is human-readable Markdown

## Testing

<!-- How did you verify this works? -->

```bash
# Example: ran integrity check
python <skill>/scripts/check-updates.py --integrity
```

## Notes

<!-- Anything else reviewers should know -->
