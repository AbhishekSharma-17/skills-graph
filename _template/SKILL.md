---
name: your-skill-name
description: "MANDATORY TRIGGERS: keyword1, keyword2, keyword3. Describe what this skill does and when to use it. Be specific about trigger conditions."
license: MIT
metadata:
  version: "1.0.0"
  author: Your Name
  tags: ["tag1", "tag2", "tag3"]
---

# Your Skill Title

> **Version:** X.Y.Z | **Source:** https://source-url.com

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview** | `references/00-overview.md` | "what is this", "getting started", "introduction" |
| **Topic A** | `references/01-topic-a.md` | "keyword for topic A", "when to load topic A" |
| **Topic B** | `references/02-topic-b.md` | "keyword for topic B", "when to load topic B" |
| **Topic C (Router)** | `references/03-topic-c.md` | "keyword for topic C" — routes to sub-files |

<!--
INSTRUCTIONS (delete this comment block when done):

1. Keep this file UNDER 100 lines — it's a pure router
2. Every reference file listed here MUST exist in references/
3. "Read When" conditions should be natural language triggers
4. For complex topics with 3+ sub-aspects, create a ROUTER file
   that links to sub-files (see references/03-topic-c.md template)
5. Run: python scripts/check-updates.py --integrity to verify
-->

## Installation

```bash
# Copy to your platform's skill directory
cp -r . ~/.claude/skills/your-skill-name/
```

## Quick Reference

- **Source docs:** https://source-url.com
- **Package:** `pip install your-package` (if applicable)
