# Dagger LLM Integration

> Source: https://docs.dagger.io/features/llm | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Creating LLM Instances](#creating-llm-instances)
- [Tool Use with Dagger Functions](#tool-use-with-dagger-functions)
- [Agent Environments](#agent-environments)
- [MCP Support](#mcp-support)
- [Model Providers](#model-providers)
- [Prompt Mode](#prompt-mode)
- [Practical Examples](#practical-examples)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger provides native LLM integration, allowing AI agents to operate within the Dagger runtime. LLMs can discover and use Dagger Functions as tools, interact with containers and directories, and execute complex workflows in sandboxed environments.

Key capabilities:
- **Tool use**: LLMs automatically discover and invoke Dagger Functions
- **Environments**: Configure what resources an LLM can access
- **Agent loop**: Iterative execution where LLMs refine work across multiple turns
- **MCP support**: Bidirectional Model Context Protocol integration
- **Multi-provider**: OpenAI, Anthropic, Google, Ollama, Docker Model Runner

## Core Concepts

### LLM Type

The `LLM` type represents a language model instance with its context and configuration:

```python
@dagger.function
async def ask(self, prompt: str) -> str:
    """Ask an LLM a question."""
    return await (
        dag.llm("openai/gpt-4o")
        .with_prompt(prompt)
        .ask()
    )
```

### Environments

An environment defines what an LLM can access — containers, directories, modules, and variables:

```python
@dagger.function
async def code_review(self, source: dagger.Directory) -> str:
    """AI-powered code review."""
    return await (
        dag.llm("anthropic/claude-sonnet-4-20250514")
        .with_directory("source", source)
        .with_prompt("Review the code in the source directory for bugs and security issues.")
        .ask()
    )
```

## Creating LLM Instances

### Basic Usage

```python
# With a specific model
llm = dag.llm("openai/gpt-4o")

# With system prompt
llm = dag.llm("anthropic/claude-sonnet-4-20250514").with_system_prompt(
    "You are a senior code reviewer. Focus on security and performance."
)

# With temperature
llm = dag.llm("openai/gpt-4o").with_temperature(0.2)
```

### Model String Format

```
provider/model-name
```

Examples:
- `openai/gpt-4o`
- `anthropic/claude-sonnet-4-20250514`
- `google/gemini-2.0-flash`
- `ollama/llama3.2`

## Tool Use with Dagger Functions

LLMs can automatically discover and use any available Dagger Functions as tools:

```python
@dagger.object_type
class CiAgent:
    @dagger.function
    async def analyze_tests(self, source: dagger.Directory) -> str:
        """Let an LLM run tests and analyze failures."""
        return await (
            dag.llm("openai/gpt-4o")
            .with_container(
                dag.container()
                .from_("python:3.12")
                .with_directory("/app", source)
                .with_workdir("/app")
            )
            .with_prompt(
                "Run the test suite with pytest -v. If any tests fail, "
                "analyze the failures and suggest fixes."
            )
            .ask()
        )
```

The LLM receives documentation from your Dagger Functions via inline docstrings, allowing it to understand what tools are available and how to use them.

## Agent Environments

### Adding Containers

```python
llm = (
    dag.llm("openai/gpt-4o")
    .with_container(
        dag.container()
        .from_("python:3.12")
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
    )
)
```

### Adding Directories

```python
llm = (
    dag.llm("anthropic/claude-sonnet-4-20250514")
    .with_directory("project", source)
    .with_directory("docs", docs_dir)
)
```

### Adding Variables

```python
llm = (
    dag.llm("openai/gpt-4o")
    .with_variable("PROJECT_NAME", "my-app")
    .with_variable("VERSION", "1.0.0")
)
```

### Adding Modules as Tools

```python
llm = (
    dag.llm("openai/gpt-4o")
    .with_module(dag.golang())  # Go toolchain as LLM tool
    .with_module(dag.helm())     # Helm operations as LLM tool
)
```

## MCP Support

### Exposing Dagger Modules as MCP Servers

Make any Dagger module available to external MCP clients (Claude Desktop, Cursor, etc.):

```bash
# Expose the current module as an MCP server
dagger mcp
```

### Connecting External MCP Servers

Attach external MCP servers to an LLM instance:

```python
@dagger.function
async def smart_deploy(self, source: dagger.Directory) -> str:
    """Deploy using external MCP tools."""
    return await (
        dag.llm("openai/gpt-4o")
        .with_mcp_server("github", "npx", ["-y", "@modelcontextprotocol/server-github"])
        .with_directory("source", source)
        .with_prompt("Create a PR with the changes in the source directory")
        .ask()
    )
```

## Model Providers

| Provider | Env Variable | Example Models |
|----------|-------------|----------------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4-20250514, claude-haiku-4-5-20251001 |
| Google | `GOOGLE_API_KEY` | gemini-2.0-flash |
| Ollama | (local) | llama3.2, mistral |
| Docker Model Runner | (local) | ai/llama3.2 |

### Local Model Setup

```bash
# With Ollama
ollama serve
ollama pull llama3.2

# Use in Dagger
dagger call ask --prompt="Explain Docker" --model=ollama/llama3.2
```

## Prompt Mode

Interactive natural-language shell:

```bash
# Enter prompt mode
dagger prompt

# Ask questions in natural language
> Build my Python app and run the tests
> Fix any test failures you find
> Publish the image to ttl.sh
```

In prompt mode, the LLM translates natural language into Dagger API calls.

## Practical Examples

### AI Code Review Pipeline

```python
@dagger.function
async def review(self, source: dagger.Directory) -> str:
    """Automated code review with AI."""
    diff = await (
        dag.container()
        .from_("alpine/git")
        .with_directory("/repo", source)
        .with_workdir("/repo")
        .with_exec(["git", "diff", "HEAD~1"])
        .stdout()
    )

    return await (
        dag.llm("anthropic/claude-sonnet-4-20250514")
        .with_system_prompt(
            "You are a senior code reviewer. Review the git diff "
            "for bugs, security issues, and code quality problems."
        )
        .with_prompt(f"Review this diff:\n\n{diff}")
        .ask()
    )
```

### AI-Powered Documentation Generator

```python
@dagger.function
async def generate_docs(self, source: dagger.Directory) -> dagger.Directory:
    """Generate documentation from source code."""
    docs = await (
        dag.llm("openai/gpt-4o")
        .with_directory("source", source)
        .with_prompt(
            "Read the source code and generate comprehensive API documentation "
            "in Markdown format. Create one file per module."
        )
        .directory("output")
    )
    return docs
```

## Common Pitfalls

1. **Missing API keys**: Set provider API keys as environment variables
2. **Model availability**: Ensure the specified model is available (local models need to be pulled)
3. **Cost awareness**: LLM calls in CI can accumulate costs — use smaller models for simple tasks
4. **Token limits**: Large codebases may exceed context windows — pass specific files, not entire repos
5. **Nondeterminism**: LLM outputs vary between runs — don't rely on exact output in assertions
6. **Sandboxing**: LLMs operate within Dagger's sandbox — they can't access the host directly
