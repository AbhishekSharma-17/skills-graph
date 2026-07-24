# Storybook — AI Integration

> Source: https://storybook.js.org/docs/ai | v10.5.3

## Table of Contents

- [Overview](#overview)
- [Agentic Setup](#agentic-setup)
- [MCP Server](#mcp-server)
- [Agent Instructions](#agent-instructions)
- [Manifests](#manifests)
- [Best Practices](#best-practices)

## Overview

Storybook provides AI integration features (currently in preview, React projects only) that enable AI agents to interact with component documentation, generate stories, and run tests. The integration works through two mechanisms:

1. **Agentic Setup** — AI-guided Storybook installation and story writing
2. **MCP Server** — Model Context Protocol server for agent tool access

## Agentic Setup

The agentic setup feature analyzes your project and generates step-by-step instructions for AI agents. It handles:

- Installing and configuring Storybook
- Setting up the preview configuration
- Writing initial component stories
- Verifying the implementation

### Getting Started

Tell your AI agent:

```
Set up Storybook for me with npm create storybook@latest and follow its instructions precisely
```

The agent analyzes your project structure, determines the framework, and configures Storybook automatically.

## MCP Server

The Model Context Protocol (MCP) server connects AI agents to Storybook's component knowledge. It provides tools for querying component documentation, generating stories, and running tests.

### Installation

```bash
npx storybook add @storybook/addon-mcp
```

After installation, the MCP server is accessible at `http://localhost:6006/mcp` (port matches your Storybook dev server).

### Configuration

Register the MCP server with your AI agent:

```bash
npx mcp-add --type http --url "http://localhost:6006/mcp" --scope project
```

This command prompts for a server name and integrates it with your agent's tool registry.

### For Claude Code

Add to your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "storybook": {
      "type": "http",
      "url": "http://localhost:6006/mcp"
    }
  }
}
```

### Available MCP Tools

The MCP server exposes tools for:

| Tool | Purpose |
|------|---------|
| `list-all-documentation` | List all documented components |
| `get-documentation` | Get specific component documentation |
| `run-story-tests` | Execute tests for stories |
| `get-component-info` | Retrieve component props and metadata |

## Agent Instructions

Add instructions to your `AGENTS.md` or `CLAUDE.md` file to guide AI agents:

```markdown
## Storybook Guidelines

When working on UI components:

1. Always use the MCP tools to access Storybook's component and documentation
   knowledge before answering or taking any action
2. Never assume undocumented component properties exist
3. Query `list-all-documentation` to discover available components
4. Use `get-documentation` to verify specific properties before suggesting changes
5. Run `run-story-tests` to validate changes after modifications
6. Create stories for new components following existing patterns
```

### Story Writing Guidelines for Agents

```markdown
## Writing Stories

When creating new stories:

- Use CSF format with TypeScript
- Include at least: Default, WithProps, Interactive states
- Add play functions for testable interactions
- Set appropriate args for each variant
- Tag with 'autodocs' for documentation generation
- Follow existing naming conventions in the project
```

## Manifests

Storybook automatically generates JSON manifests containing metadata about components, stories, and documentation. These manifests:

- Stay current as you modify your Storybook
- Provide structured data about component props, stories, and their states
- Enable agents to access up-to-date component information
- Include story arg values, decorator configurations, and parameter settings

### Manifest Contents

The manifests include:

- Component names and file paths
- Story names and their args
- ArgTypes with control configurations
- Parameter values
- Tags and metadata

## Best Practices

### For Agent-Driven Development

1. **Keep stories simple** — Agents work best with clear, minimal story examples
2. **Use descriptive args** — Name args clearly so agents understand their purpose
3. **Document edge cases** — Include stories for error states, loading, and empty states
4. **Run tests after changes** — Always have the agent run story tests post-modification
5. **Maintain consistency** — Follow the same patterns across all story files

### For Story Generation

When asking an AI to generate stories:

```
Create stories for the UserProfile component that cover:
- Default state with sample data
- Loading state
- Error state
- Empty state (no user data)
- With long text content (overflow testing)
- Interactive: form submission flow with play function
```

### For Component Documentation

```
Generate documentation for the DataTable component. Include:
- Usage examples for common configurations
- Props documentation with descriptions
- Interactive playground story
- Accessibility notes
```

### Workflow: Agent Creates a New Component

```
1. Agent reads existing stories to learn project patterns
2. Agent creates the component file
3. Agent generates stories covering key states (default, error, loading, empty)
4. Agent adds play functions for interaction testing
5. Agent runs `run-story-tests` to validate
6. Agent tags with 'autodocs' for documentation
```

### Workflow: Agent Fixes a Visual Bug

```
1. Agent queries `get-documentation` for the affected component
2. Agent reviews current stories and their args
3. Agent makes the code fix
4. Agent creates a new story reproducing the original bug
5. Agent runs tests to verify the fix
6. Agent updates existing stories if args changed
```

### Limitations

- Currently limited to React projects (preview feature)
- MCP server requires Storybook dev server running
- Agent quality depends on the underlying model's React knowledge
- Complex component hierarchies may require manual guidance
- MCP tools may not reflect unsaved changes until Storybook hot-reloads

## Common Pitfalls

1. **MCP server not connecting** — Ensure Storybook is running on the expected port
2. **Stale manifests** — Restart Storybook after major structural changes
3. **Agent hallucinating props** — Always validate against `get-documentation` output
4. **Ignoring test results** — Always check `run-story-tests` output after changes
5. **Port mismatch** — Update MCP URL if Storybook runs on a non-default port

## Related Topics

- [Configuration](10-configuration.md) — Main and preview configuration
- [Interaction Testing](06-interaction-testing.md) — Test automation
- [Documentation](08-documentation.md) — Autodocs and MDX
