# Skills & Tools — Complete Examples

## 1. Basic Skills Agent

```python
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills

skills_dir = Path(__file__).parent / "sample_skills"

agent = Agent(
    name="Code Review Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills(str(skills_dir))]),
    instructions=["You are a helpful assistant with access to specialized skills."],
    markdown=True,
)

agent.print_response(
    "Review this Python code and provide feedback:\n\n"
    "```python\n"
    "def calculate_total(items):\n"
    "    total = 0\n"
    "    for i in range(len(items)):\n"
    "        total = total + items[i]['price'] * items[i]['quantity']\n"
    "    return total\n"
    "```"
)
```

## 2. Creating a Complete Skill

**Directory structure:**
```
code-review/
├── SKILL.md
├── scripts/
│   └── check_style.py
└── references/
    └── style-guide.md
```

**SKILL.md:**
```yaml
---
name: code-review
description: Code review assistance with style checking and best practices. Use when asked to review code, check for issues, or suggest improvements.
---

# Code Review Skill

## When to Use
Use this skill when the user asks you to review, audit, or improve code.

## Workflow
1. Run `scripts/check_style.py` on the code for automated checks
2. Reference `references/style-guide.md` for naming conventions
3. Provide structured feedback with severity levels

## Feedback Format
- **Critical**: Bugs, security issues
- **Warning**: Performance, maintainability
- **Suggestion**: Style, readability improvements
```

**scripts/check_style.py:**
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

## 3. Multiple Skills + Multiple Loaders

```python
from agno.skills import Skills, LocalSkills

skills = Skills(loaders=[
    LocalSkills("/shared/team-skills"),     # Shared across team
    LocalSkills("/project/custom-skills"),  # Project-specific
])

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=skills,
)
```

## 4. Claude Agent Skills (Anthropic-Provided)

Anthropic provides built-in skills for Claude models: `pptx`, `xlsx`, `docx`, `pdf`.

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

agent = Agent(
    model=Claude(
        id="claude-sonnet-4-5-20250929",
        skills=[
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"},
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "anthropic", "skill_id": "docx", "version": "latest"},
        ]
    ),
    instructions=["You are a document specialist."],
    markdown=True,
)
```

**Supported models**: `claude-sonnet-4-5-20250929`, `claude-3-5-sonnet-20241022`

## 5. Agent with Custom Tools + Session State

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run import RunContext

def add_to_cart(run_context: RunContext, item: str, price: float) -> str:
    """Add an item to the shopping cart."""
    cart = run_context.session_state["cart"]
    cart.append({"item": item, "price": price})
    total = sum(i["price"] for i in cart)
    return f"Added {item} (${price}). Cart total: ${total:.2f}"

def view_cart(run_context: RunContext) -> str:
    """View the current shopping cart."""
    cart = run_context.session_state["cart"]
    if not cart:
        return "Cart is empty."
    items = [f"- {i['item']}: ${i['price']:.2f}" for i in cart]
    total = sum(i["price"] for i in cart)
    return "\n".join(items) + f"\n\nTotal: ${total:.2f}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    session_state={"cart": []},
    tools=[add_to_cart, view_cart],
    instructions="You are a shopping assistant. Current cart: {cart}",
)
```

## 6. Custom Toolkit Example

```python
from typing import List, Dict, Any
from agno.tools import Toolkit

class DatabaseTools(Toolkit):
    def __init__(self, connection_string: str, **kwargs):
        self.connection_string = connection_string
        tools = [self.query, self.list_tables]
        super().__init__(name="database_tools", tools=tools, **kwargs)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        # Your DB logic here
        ...

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        ...

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DatabaseTools(connection_string="postgresql://...")],
)
```

## 7. Tool with Caching + Hooks

```python
from agno.tools import tool
from agno.utils.log import logger

def log_tool_call(tool_name, args, kwargs):
    logger.info(f"Tool called: {tool_name} with args={args}")

@tool(
    name="search_docs",
    description="Search documentation for answers",
    cache_results=True,
    cache_ttl=1800,
    tool_hooks=[log_tool_call],
)
def search_documentation(query: str, max_results: int = 5) -> list:
    """Search the documentation database."""
    # Your search logic
    ...
```

## 8. Skills + Tools Together

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills("/path/to/skills")]),
    tools=[HackerNewsTools()],
    instructions=[
        "Use skills for domain knowledge and tools for actions.",
        "Load skill instructions before applying them.",
    ],
)
```

## Import Reference

```python
# Skills
from agno.skills import Skills, LocalSkills, SkillValidationError

# Tools
from agno.tools import tool, Toolkit
from agno.tools.function import ToolResult
from agno.media import Image

# Auto-injected parameters
from agno.run import RunContext
from agno.agent import Agent
from agno.team import Team

# Pre-built toolkits (examples)
from agno.tools.hackernews import HackerNewsTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.shell import ShellTools
from agno.tools.python import PythonTools
from agno.tools.mcp import MCPTools
```
