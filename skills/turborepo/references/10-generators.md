# Turborepo — Code Generation

> Source: [turborepo.dev/docs/guides/generating-code](https://turborepo.dev/docs/guides/generating-code)

## Overview

Turborepo Generators automate the creation of new packages, workspaces, and code within your monorepo. Instead of manually creating directories, copying boilerplate, and wiring up configuration, generators handle it all in a single command.

## Built-in Generators

### Create a New Workspace

```bash
npx turbo gen workspace
```

Interactive prompts let you:
- Choose a name for the new workspace
- Select a location (`apps/` or `packages/`)
- Copy from an existing workspace (template) or start blank
- Auto-install dependencies

### Copy an Existing Workspace

```bash
npx turbo gen workspace --copy
```

Creates a new workspace based on an existing one, updating the package name and resetting the version.

### CLI Options

```bash
# Create with specific options (skip prompts)
npx turbo gen workspace \
  --name @repo/new-api \
  --destination apps/new-api \
  --copy apps/api

# Blank workspace (no copy)
npx turbo gen workspace \
  --name @repo/shared-types \
  --destination packages/shared-types
```

## Custom Generators

For more control, create custom generators using Plop templates. Turborepo's generator system is built on top of Plop but doesn't require installing Plop separately.

### Setup

1. Create the generator config at the monorepo root:

```
turbo/
└── generators/
    ├── config.ts          # Generator definitions
    └── templates/         # Handlebars templates
        └── component.hbs
```

2. Install the types package:

```bash
pnpm add -Dw @turbo/gen
```

### Generator Config

```typescript
// turbo/generators/config.ts
import type { PlopTypes } from "@turbo/gen";

export default function generator(plop: PlopTypes.NodePlopAPI): void {
  plop.setGenerator("component", {
    description: "Create a new React component",
    prompts: [
      {
        type: "input",
        name: "name",
        message: "Component name:",
      },
      {
        type: "list",
        name: "package",
        message: "Which package?",
        choices: ["ui", "web"],
      },
    ],
    actions: [
      {
        type: "add",
        path: "packages/{{package}}/src/components/{{pascalCase name}}/{{pascalCase name}}.tsx",
        templateFile: "templates/component.hbs",
      },
      {
        type: "add",
        path: "packages/{{package}}/src/components/{{pascalCase name}}/index.ts",
        template: 'export { {{pascalCase name}} } from "./{{pascalCase name}}";\n',
      },
    ],
  });
}
```

### Template File

```handlebars
{{!-- turbo/generators/templates/component.hbs --}}
import type { FC, ReactNode } from "react";

interface {{pascalCase name}}Props {
  children?: ReactNode;
}

export const {{pascalCase name}}: FC<{{pascalCase name}}Props> = ({ children }) => {
  return <div>{children}</div>;
};
```

### Running Custom Generators

```bash
# Interactive mode (shows all available generators)
npx turbo gen

# Run a specific generator
npx turbo gen component
```

## Advanced Generator Patterns

### Append to Existing Files

```typescript
actions: [
  {
    type: "append",
    path: "packages/ui/src/index.ts",
    template: 'export { {{pascalCase name}} } from "./components/{{pascalCase name}}";\n',
  },
];
```

### Modify Files

```typescript
actions: [
  {
    type: "modify",
    path: "packages/ui/src/index.ts",
    pattern: /(\/\/ GENERATOR_EXPORTS)/,
    template: 'export { {{pascalCase name}} } from "./components/{{pascalCase name}}";\n$1',
  },
];
```

### Multiple Actions

```typescript
actions: [
  // Create component file
  { type: "add", path: "...", templateFile: "templates/component.hbs" },
  // Create test file
  { type: "add", path: "...", templateFile: "templates/component.test.hbs" },
  // Create story file
  { type: "add", path: "...", templateFile: "templates/component.stories.hbs" },
  // Update barrel export
  { type: "append", path: "...", template: "..." },
];
```

## Package-Level Generators

Generators can also live inside individual packages for package-specific scaffolding:

```
packages/ui/
├── turbo/
│   └── generators/
│       ├── config.ts
│       └── templates/
└── src/
```

Run with:

```bash
npx turbo gen --config packages/ui/turbo/generators/config.ts
```

## Plop Helpers Available

Turborepo generators include all Plop built-in helpers:

| Helper | Example | Output |
|--------|---------|--------|
| `camelCase` | `{{camelCase "my component"}}` | `myComponent` |
| `pascalCase` | `{{pascalCase "my component"}}` | `MyComponent` |
| `snakeCase` | `{{snakeCase "my component"}}` | `my_component` |
| `kebabCase` | `{{kebabCase "my component"}}` | `my-component` |
| `upperCase` | `{{upperCase "hello"}}` | `HELLO` |
| `lowerCase` | `{{lowerCase "HELLO"}}` | `hello` |

## Common Pitfalls

1. **Missing @turbo/gen** — Custom generators need `@turbo/gen` as a dev dependency for TypeScript types. Without it, the config file won't type-check.

2. **Generator path** — Generators must be in `turbo/generators/` at the repo root (or package root for package-level generators).

3. **Template syntax** — Templates use Handlebars syntax (`{{name}}`). Don't confuse with JavaScript template literals.

4. **Running install after generation** — After creating a new workspace, run your package manager's install command to update the lockfile.

## Related

- [Workspace Structure](04-workspace-structure.md) — Package organization
- [CLI Reference](12-cli-reference.md) — turbo gen command
