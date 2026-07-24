# Storybook — Overview

> Source: https://storybook.js.org/docs | v10.5.3

## What Is Storybook?

Storybook is a frontend workshop for building UI components and pages in isolation. It runs alongside your application in a separate process, letting you develop hard-to-reach component states and edge cases without needing the full app running. It is open source, framework-agnostic, and used by thousands of teams for component development, testing, and documentation.

## Core Philosophy

Storybook treats components as the unit of UI development. Each component gets one or more **stories** — isolated renderings that capture a specific visual state. This approach offers:

- **Isolation**: Develop one component at a time without backend dependencies
- **Reproducibility**: Every state is a story you can revisit and share
- **Durability**: Stories serve as both development views and test cases
- **Documentation**: Stories auto-generate living component docs

## When to Use Storybook

- Building a component library or design system
- Developing UI components before backend APIs are ready
- Testing visual states, edge cases, and responsive behavior
- Creating living documentation for a component catalog
- Running interaction tests, visual regression tests, and accessibility audits
- Sharing component specifications with designers and stakeholders

## When NOT to Use Storybook

- Pure backend/API projects with no UI
- Extremely simple pages with no reusable components
- Projects where the overhead of maintaining stories outweighs benefits

## Supported Frameworks

### Official Support
| Framework | Builder |
|-----------|---------|
| React | Vite, Webpack |
| Next.js | Vite, Webpack |
| Vue 3 | Vite |
| Angular | Webpack |
| SvelteKit | Vite |
| Svelte | Vite |
| Preact | Vite |
| Web Components | Vite |
| React Native | Metro |

### Community-Maintained
Analog (Angular), Nuxt, SolidJS, Qwik, and frameworks using Rspack/Rsbuild builds.

## Architecture

Storybook runs as two separate processes:

1. **Manager** — The UI shell handling navigation, search, toolbars, and addon panels
2. **Preview** — An iframe where components render with their stories

These communicate through a channel API. Addons can extend either the Manager (panels, toolbars) or the Preview (decorators, parameters).

## Key Concepts

### Stories
A story is a function or object that returns a rendered component in a specific state. Stories use the **Component Story Format (CSF)**, an ES module standard:

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta = {
  component: Button,
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    primary: true,
    label: 'Click me',
  },
};
```

### Args
Framework-agnostic term for component inputs (React props, Vue props, Angular @Input). Args are dynamically editable via the Controls panel.

### Decorators
Functions that wrap stories with additional rendering context — layout wrappers, theme providers, mocked context.

### Parameters
Static metadata attached to stories that configure addon behavior (backgrounds, viewport, docs).

### Play Functions
Code that runs after a story renders, simulating user interactions for testing:

```typescript
export const FilledForm: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.type(canvas.getByTestId('email'), 'test@example.com');
    await userEvent.click(canvas.getByRole('button'));
  },
};
```

### Addons
Extensions that add features like Controls, Actions, Viewport, Accessibility testing, and Visual testing. The Essentials package includes the most common ones.

## Project Structure

```
your-project/
├── .storybook/
│   ├── main.ts          # Storybook configuration (framework, addons, stories glob)
│   ├── preview.ts       # Story rendering config (decorators, parameters, globals)
│   └── manager.ts       # UI customization (theme, layout)
├── src/
│   └── components/
│       ├── Button/
│       │   ├── Button.tsx
│       │   └── Button.stories.tsx
│       └── Card/
│           ├── Card.tsx
│           └── Card.stories.tsx
```

## Testing Strategy

Storybook supports multiple testing approaches, all built on stories:

| Test Type | What It Catches | Tool |
|-----------|----------------|------|
| **Render tests** | Crashes, import errors | Story renders without errors |
| **Interaction tests** | Behavior bugs | Play functions + assertions |
| **Visual tests** | UI regressions | Chromatic pixel comparison |
| **Accessibility tests** | WCAG violations | a11y addon (axe-core) |
| **Snapshot tests** | Markup changes | Vitest/Jest serializers |

## Version History

| Version | Release | Highlights |
|---------|---------|------------|
| v10.x | 2026 | Current major version |
| v8.x | 2024 | Vitest integration, RSC support, Vite-first |
| v7.x | 2023 | CSF 3, framework API, Vite support |
| v6.x | 2021 | Args, Controls, CSF 2 |

## System Requirements

- Node.js 20+
- npm 10+ / pnpm 9+ / Yarn 4+
- TypeScript 4.9+
- Vite 5+ or Webpack 5+
- Modern browsers (Chrome 131+, Firefox 136+, Safari 18.3+)

## Common Workflows

### Design System Development

1. Create component stories with all visual variants
2. Enable autodocs for living documentation
3. Configure Chromatic for visual regression testing
4. Publish Storybook as a shared reference for designers and developers
5. Use Storybook composition to unify multiple team Storybooks

### Test-Driven UI Development

1. Write stories that define expected component states
2. Add play functions to simulate user interactions
3. Assert on expected outcomes using `expect`
4. Run tests in watch mode during development
5. Integrate into CI for continuous validation

### Component Library Publishing

1. Build stories for every exported component
2. Generate documentation with autodocs
3. Set up accessibility checks globally
4. Publish static Storybook alongside npm package
5. Embed stories in README or documentation site

## Comparison with Alternatives

| Feature | Storybook | Ladle | Histoire | Docz |
|---------|-----------|-------|----------|------|
| Framework support | 10+ | React only | Vue only | React only |
| Addon ecosystem | 400+ | Minimal | Small | Small |
| Testing built-in | Yes | No | Limited | No |
| Visual testing | Chromatic | No | No | No |
| Community size | 90K+ stars | 4K stars | 3K stars | 23K stars |
| Active development | Very active | Moderate | Moderate | Archived |

## Glossary

| Term | Definition |
|------|-----------|
| **CSF** | Component Story Format — ES module standard for writing stories |
| **Story** | A rendered state of a component with specific args |
| **Meta** | Default export in a story file containing component metadata |
| **Args** | Component inputs (props/inputs) managed by Storybook |
| **ArgTypes** | Metadata about args — controls, descriptions, categories |
| **Decorator** | Function wrapping a story with extra rendering context |
| **Parameter** | Static metadata configuring addon behavior |
| **Play Function** | Code executing after story render for interaction testing |
| **Addon** | Extension adding features to Storybook |
| **Chromatic** | Official visual testing cloud service |
| **Autodocs** | Automatic documentation generation from stories |
| **Canvas** | Scoped DOM query object for testing within story root |

## Related Topics

- [Installation & Setup](01-installation-setup.md) — Getting started with your framework
- [Writing Stories](02-writing-stories.md) — CSF format and story patterns
- [Testing](06-interaction-testing.md) — Component testing strategies
