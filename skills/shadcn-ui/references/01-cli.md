# shadcn/ui — CLI Commands

> Source: [ui.shadcn.com/docs/cli](https://ui.shadcn.com/docs/cli) | CLI v4.7.x

## Table of Contents
- [Installation](#installation)
- [init](#init)
- [add](#add)
- [search / list](#search--list)
- [view](#view)
- [info](#info)
- [docs](#docs)
- [build](#build)
- [registry](#registry)
- [diff](#diff)
- [Global Flags](#global-flags)
- [Common Workflows](#common-workflows)

## Installation

The CLI is distributed as the `shadcn` npm package. Use via `npx` (no global install needed):

```bash
npx shadcn@latest <command>
```

Or install globally:

```bash
npm install -g shadcn
shadcn <command>
```

## init

Initializes configuration and dependencies for a new or existing project.

```bash
npx shadcn@latest init [options]
```

**Options:**

| Flag | Description |
|------|-------------|
| `-d, --defaults` | Use default configuration (skip prompts) |
| `-y, --yes` | Skip confirmation prompt |
| `-c, --cwd <path>` | Working directory (default: current) |
| `--name <name>` | Create a new project with the given name |
| `--pm <manager>` | Package manager: npm, yarn, pnpm, bun |

**Interactive prompts:**

1. **Component library:** Radix or Base UI
2. **Base color:** neutral, stone, zinc, mauve, olive, mist, taupe
3. **CSS variables:** yes/no (yes recommended)

**What it does:**

- Creates `components.json` configuration
- Installs required dependencies (`tailwind-merge`, `clsx`, `class-variance-authority`)
- Adds the `cn()` utility to `lib/utils.ts`
- Configures CSS variables in your global stylesheet
- Sets up Tailwind CSS integration

```bash
# Quick start with defaults
npx shadcn@latest init -d

# Create new Next.js project
npx shadcn@latest init --name my-app

# Specify framework template
npx shadcn@latest init --name my-app -d
```

## add

Adds components, hooks, blocks, or other registry items to your project.

```bash
npx shadcn@latest add [items...] [options]
```

**Arguments:** Component names, URLs, or local file paths.

**Options:**

| Flag | Description |
|------|-------------|
| `-y, --yes` | Skip confirmation |
| `-o, --overwrite` | Overwrite existing files |
| `-c, --cwd <path>` | Working directory |
| `-a, --all` | Add all available components |
| `-p, --path <path>` | Custom install path |
| `--silent` | Suppress output |
| `--src-dir <dir>` | Source directory for components |

**Examples:**

```bash
# Single component
npx shadcn@latest add button

# Multiple components
npx shadcn@latest add button card dialog input label

# All components at once
npx shadcn@latest add --all

# From a URL (custom registry)
npx shadcn@latest add https://myregistry.com/r/fancy-button.json

# From local path
npx shadcn@latest add ./my-components/custom-input.json

# Overwrite existing
npx shadcn@latest add button --overwrite

# Custom output path
npx shadcn@latest add button --path src/components/custom
```

The CLI automatically:
- Resolves and installs npm dependencies
- Copies component source files
- Installs peer dependencies (e.g., `@radix-ui/react-dialog` for Dialog)
- Respects `components.json` paths and aliases

## search / list

Search for components and registry items.

```bash
npx shadcn@latest search [query]
npx shadcn@latest list [query]    # alias
```

```bash
# Search for form-related components
npx shadcn@latest search form

# List all available items
npx shadcn@latest list
```

## view

Preview a component's source code before installing.

```bash
npx shadcn@latest view <item>
```

```bash
# View button source
npx shadcn@latest view button

# View dialog source
npx shadcn@latest view dialog
```

## info

Shows project configuration, installed components, and framework details.

```bash
npx shadcn@latest info [options]
```

Displays:
- Framework and version detected
- CSS variables configuration
- List of installed components
- Documentation and example links for each component

## docs

Get documentation, code examples, and usage patterns for any component directly in the terminal.

```bash
npx shadcn@latest docs <component>
```

```bash
# Get docs for dialog
npx shadcn@latest docs dialog

# Get docs for data table
npx shadcn@latest docs data-table
```

This is especially useful for AI coding agents — provides complete context about component APIs and patterns.

## build

Generates registry JSON files for distributing custom components.

```bash
npx shadcn@latest build [options]
```

**Options:**

| Flag | Description |
|------|-------------|
| `-c, --cwd <path>` | Working directory |
| `-o, --output <dir>` | Output directory (default: `public/r`) |

Reads `registry.json` from your project root and generates JSON files in `public/r/` that other projects can install from.

```bash
# Build registry
npx shadcn@latest build

# Custom output
npx shadcn@latest build --output dist/registry
```

## registry

Manage custom registries in your project configuration.

```bash
npx shadcn@latest registry add <url>    # Add a registry
npx shadcn@latest registry list         # List active registries
npx shadcn@latest registry remove <url> # Remove a registry
```

When you add a registry, components from that registry become available via `shadcn add`.

```bash
# Add a team's internal registry
npx shadcn@latest registry add https://design.mycompany.com/r

# List configured registries
npx shadcn@latest registry list
```

## diff

Show changes between your local component and the upstream version.

```bash
npx shadcn@latest diff [component]
```

```bash
# Diff all components
npx shadcn@latest diff

# Diff specific component
npx shadcn@latest diff button
```

Useful for reviewing what's changed upstream before updating.

## Global Flags

These flags work with any command:

| Flag | Description |
|------|-------------|
| `-c, --cwd <path>` | Set working directory |
| `--help` | Show help for command |
| `--version` | Show CLI version |

## Common Workflows

### Starting a New Project

```bash
npx shadcn@latest init --name my-app -d
cd my-app
npx shadcn@latest add button card input label
npm run dev
```

### Adding Components to Existing Project

```bash
cd existing-project
npx shadcn@latest init
npx shadcn@latest add dialog form input label select textarea
```

### Updating a Component

```bash
# Check for changes
npx shadcn@latest diff button

# Re-add with overwrite
npx shadcn@latest add button --overwrite
```

### Building a Custom Registry

```bash
# Create registry.json
# Build JSON files
npx shadcn@latest build

# Others can now install
npx shadcn@latest add https://yoursite.com/r/your-component.json
```

### AI Agent Context

```bash
# Give an AI agent full component context
npx shadcn@latest docs dialog
npx shadcn@latest info
```

CLI v4 includes `shadcn/skills` — structured documentation that coding agents can consume to understand component APIs, patterns, and registry workflows.
