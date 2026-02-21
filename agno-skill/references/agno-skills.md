# Agno Skills & Tools

Agno has two complementary systems for extending agent capabilities:

- **Skills** — Self-contained knowledge packages (instructions + scripts + references) that agents discover and load on demand. Based on Anthropic's Agent Skills spec.
- **Tools** — Python functions or Toolkits that agents call to perform actions. 120+ pre-built toolkits available.

## Skills — Quick Start

A skill is a directory with a `SKILL.md` file containing instructions, plus optional scripts and references.

```
my-skill/
├── SKILL.md              # Required: YAML frontmatter + instructions
├── scripts/              # Optional: executable code
│   └── check_style.py
└── references/           # Optional: documentation
    └── style-guide.md
```

### Loading Skills into an Agent

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

The agent automatically gets these tools:
- `get_skill_instructions(skill_name)` — Load full instructions
- `get_skill_reference(skill_name, reference_path)` — Load a reference doc
- `get_skill_script(skill_name, script_path, execute, args, timeout)` — Read or execute a script

### Progressive Discovery

Skills use lazy loading — the agent sees summaries in its system prompt and loads full details only when the task matches:

1. **Browse**: Agent sees skill names + descriptions
2. **Load**: Agent calls `get_skill_instructions()` when task matches
3. **Reference**: Agent loads detailed docs via `get_skill_reference()`
4. **Execute**: Agent runs scripts via `get_skill_script()`

---

## Tools — Quick Start

Tools are Python functions agents call to interact with external systems.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

def get_weather(city: str) -> str:
    """Get the weather for the given city.

    Args:
        city (str): The city to get the weather for.
    """
    return f"The weather in {city} is sunny."

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[get_weather],
)
agent.print_response("What is the weather in San Francisco?")
```

### Tool Decorator

```python
from agno.tools import tool

@tool(
    name="fetch_stories",
    description="Get top stories from Hacker News",
    stop_after_tool_call=True,
    requires_confirmation=True,
    cache_results=True,
    cache_ttl=3600,
)
def get_top_stories(num_stories: int = 5) -> str:
    """Fetch the top stories."""
    ...
```

### Built-in Tool Parameters (auto-injected)

These parameters are automatically injected when declared in a tool function signature:

- `run_context: RunContext` — Session state, dependencies, metadata
- `agent: Agent` — The agent instance
- `team: Team` — The team instance (if in a team)
- `images`, `videos`, `audio`, `files` — Media from user input

```python
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    """Add item to shopping list."""
    run_context.session_state["shopping_list"].append(item)
    return f"Added: {item}"

agent = Agent(
    session_state={"shopping_list": []},
    tools=[add_item],
)
```

---

## Sub-References

Read only what the task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Creating Skills** | `references/agno-skills/creating-skills.md` | Building SKILL.md files, directory structure, scripts, references, validation rules |
| **Tools & Toolkits** | `references/agno-skills/tools-and-toolkits.md` | Creating custom tools, @tool decorator options, Toolkits, async tools, ToolResult, 120+ built-in toolkits |
| **Examples** | `references/agno-skills/examples.md` | Complete skill + tool examples, Claude Agent Skills (Anthropic-provided), integration patterns |
