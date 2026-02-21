# Creating Agno Skills

## Directory Structure

```
my-skill/
├── SKILL.md              # Required: YAML frontmatter + markdown instructions
├── scripts/              # Optional: executable code the agent can run
│   ├── check_style.py
│   └── lint.sh
└── references/           # Optional: documentation loaded into context as needed
    └── style-guide.md
```

For organizing multiple skills:
```
skills/
├── code-review/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
├── git-workflow/
│   ├── SKILL.md
│   └── references/
└── testing/
    ├── SKILL.md
    └── references/
```

## SKILL.md Format

### Required YAML Frontmatter

```yaml
---
name: code-review
description: Code review assistance with style checking and best practices
---
```

### Optional YAML Fields

```yaml
---
name: code-review
description: Code review assistance with style checking and best practices
license: Apache-2.0
metadata:
  version: "1.0.0"
  author: your-name
  tags: ["python", "code-quality"]
---
```

### Validation Rules

| Field | Max Length | Requirements |
|-------|-----------|--------------|
| `name` | 64 chars | Lowercase alphanumeric + hyphens. No start/end hyphen. No consecutive hyphens. Must match directory name. |
| `description` | 1024 chars | Brief summary shown in agent's system prompt |
| `license` | — | SPDX identifier: `MIT`, `Apache-2.0`, `GPL-3.0`, `BSD-3-Clause`, etc. |

### Body Content

After the frontmatter, write markdown instructions that guide the agent on when and how to apply the skill. Include decision trees, examples, templates, code patterns — whatever the agent needs.

```yaml
---
name: code-review
description: Code review assistance with style checking and best practices
---

# Code Review

## When to Use
Use this skill when asked to review Python code for best practices.

## Review Checklist
1. Check naming conventions
2. Verify error handling
3. Look for performance issues

## Scripts
- Run `scripts/check_style.py` on the code to get style feedback
- Use `references/style-guide.md` for detailed naming rules
```

## Scripts

Scripts are executable code (Python, Bash, etc.) that the agent can run. They execute with the skill directory as the working directory.

### Python Script

`scripts/check_style.py`:
```python
#!/usr/bin/env python3
"""Check code style and return results."""

import sys

def check_style(code: str) -> dict:
    issues = []
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append(f"Line {i}: exceeds 100 characters")
        if line.endswith(' '):
            issues.append(f"Line {i}: trailing whitespace")
    return {"issues": issues, "count": len(issues)}

if __name__ == "__main__":
    code = sys.stdin.read() if not sys.argv[1:] else sys.argv[1]
    result = check_style(code)
    print(result)
```

### Shell Script

`scripts/lint.sh`:
```bash
#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: lint.sh <file>"
    exit 1
fi
ruff check "$1" 2>&1
```

Scripts can be read or executed by the agent via `get_skill_script()`.

## References

Reference files are documentation the agent loads into context when it needs deeper information. Good for style guides, API docs, checklists, etc.

`references/style-guide.md`:
```markdown
# Python Style Guide

## Naming Conventions
- Variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

## Line Length
- Maximum 100 characters per line
```

## Loading Skills

```python
from agno.skills import Skills, LocalSkills

# Load all skills from a directory
skills = Skills(loaders=[LocalSkills("/path/to/skills")])

# Load a single skill
skills = Skills(loaders=[LocalSkills("/path/to/skills/code-review")])

# Multiple loader paths
skills = Skills(loaders=[
    LocalSkills("/path/to/shared-skills"),
    LocalSkills("/path/to/project-skills"),
])
```

If skills from different loaders have the same name, the later loader's skill overwrites the earlier one.

### Reloading at Runtime

```python
skills = Skills(loaders=[LocalSkills("/path/to/skills")])
# ... skills modified on disk ...
skills.reload()  # Pick up changes
```

### Error Handling

```python
from agno.skills import Skills, LocalSkills, SkillValidationError

try:
    skills = Skills(loaders=[LocalSkills("/path/to/skills")])
except SkillValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Errors: {e.errors}")
```

## Agent Integration

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills("/path/to/skills")]),
    instructions=["You have access to specialized skills."],
)
```

The agent automatically receives three tools:
- `get_skill_instructions(skill_name)` — Load full SKILL.md body
- `get_skill_reference(skill_name, reference_path)` — Load a reference file
- `get_skill_script(skill_name, script_path, execute, args, timeout)` — Read or run a script

Skill metadata (names + descriptions) is injected into the system prompt so the agent can discover skills without loading everything upfront.
