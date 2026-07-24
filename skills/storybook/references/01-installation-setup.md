# Storybook — Installation & Setup

> Source: https://storybook.js.org/docs/get-started/install | v10.5.3

## Table of Contents

- [Installation](#installation)
- [Framework Detection](#framework-detection)
- [Installation Options](#installation-options)
- [System Requirements](#system-requirements)
- [Project Configuration](#project-configuration)
- [Main Configuration](#main-configuration)
- [Preview Configuration](#preview-configuration)
- [Manager Configuration](#manager-configuration)
- [Running Storybook](#running-storybook)
- [Troubleshooting](#troubleshooting)

## Installation

The primary installation command auto-detects your project and configures Storybook:

```bash
npm create storybook@latest
```

For a specific version:

```bash
# Version 10.5
npm create storybook@10.5

# Exact version
npm create storybook@10.5.3

# For versions before 8.3
npx storybook@8.2 init
```

## Framework Detection

Storybook auto-detects your framework from `package.json` dependencies. If detection fails, specify explicitly:

```bash
npm create storybook@latest --type react
npm create storybook@latest --type nextjs
npm create storybook@latest --type vue3
npm create storybook@latest --type angular
npm create storybook@latest --type svelte
npm create storybook@latest --type solid
npm create storybook@latest --type html
```

## Installation Options

### Feature Selection

Choose between recommended and minimal setups:

```bash
# Recommended: docs, testing, a11y
npm create storybook@latest

# Minimal: just component development
npm create storybook@latest --features minimal

# Custom feature selection
npm create storybook@latest --features docs test a11y
```

### Package Manager

```bash
npm create storybook@latest --package-manager=npm
npm create storybook@latest --package-manager=pnpm
npm create storybook@latest --package-manager=yarn
```

### What Installation Does

1. Installs required dependencies
2. Creates `.storybook/` configuration directory
3. Adds `storybook` and `build-storybook` scripts to `package.json`
4. Generates example stories in `src/stories/`
5. Enables anonymous telemetry (opt-out available)

## System Requirements

| Dependency | Minimum Version |
|-----------|----------------|
| Node.js | 20+ |
| npm | 10+ |
| pnpm | 9+ |
| Yarn | 4+ |
| TypeScript | 4.9+ |
| Vite | 5+ |
| Webpack | 5+ |
| React | 18+ |
| Vue | 3+ |
| Angular | 18+ |
| Svelte | 5+ |
| Next.js | 14+ |

## Project Configuration

After installation, three key configuration files exist in `.storybook/`:

```
.storybook/
├── main.ts       # Build & addon configuration
├── preview.ts    # Story rendering defaults
└── manager.ts    # UI customization (optional)
```

## Main Configuration

`.storybook/main.ts` controls how Storybook builds and loads stories:

```typescript
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-docs',
    '@storybook/addon-a11y',
    '@storybook/addon-vitest',
  ],
  staticDirs: ['../public'],
  typescript: {
    reactDocgen: 'react-docgen-typescript',
    check: false,
  },
  docs: {
    defaultName: 'Docs',
  },
  core: {
    disableTelemetry: true,
  },
};

export default config;
```

### Key Main Options

| Option | Type | Purpose |
|--------|------|---------|
| `framework` | string | Framework package (e.g., `@storybook/react-vite`) |
| `stories` | string[] | Glob patterns for story files |
| `addons` | string[] | Addon packages to load |
| `staticDirs` | string[] | Static asset directories |
| `typescript` | object | TypeScript processing options |
| `docs` | object | Documentation settings |
| `core` | object | Internal feature toggles |
| `viteFinal` | function | Customize Vite config |
| `webpackFinal` | function | Customize Webpack config |
| `refs` | object | Storybook composition config |
| `features` | object | Enable/disable built-in features |

### Story Loading Patterns

```typescript
// Glob pattern
stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)']

// Configuration object with title prefix
stories: [{
  directory: '../packages/components',
  files: '*.stories.*',
  titlePrefix: 'Design System'
}]

// Multiple directories
stories: [
  '../src/**/*.stories.@(js|jsx|ts|tsx)',
  '../packages/**/*.stories.@(js|jsx|ts|tsx)',
]
```

### Customizing Vite

```typescript
const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  async viteFinal(config) {
    const { mergeConfig } = await import('vite');
    return mergeConfig(config, {
      resolve: {
        alias: { '@': '/src' },
      },
    });
  },
};
```

### Customizing Webpack

```typescript
const config: StorybookConfig = {
  framework: '@storybook/react-webpack5',
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  webpackFinal: async (config) => {
    config.resolve = {
      ...config.resolve,
      alias: { ...config.resolve?.alias, '@': path.resolve(__dirname, '../src') },
    };
    return config;
  },
};
```

## Preview Configuration

`.storybook/preview.ts` controls how stories render — global decorators, parameters, and defaults:

```typescript
import type { Preview } from '@storybook/react';
import '../src/styles/globals.css';

const preview: Preview = {
  decorators: [
    (Story) => (
      <div style={{ padding: '1rem' }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    layout: 'centered',
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      options: {
        light: { name: 'Light', value: '#ffffff' },
        dark: { name: 'Dark', value: '#333333' },
      },
    },
  },
  tags: ['autodocs'],
};

export default preview;
```

### Preview Options

| Option | Purpose |
|--------|---------|
| `decorators` | Global wrappers (theme providers, layout) |
| `parameters` | Static addon configuration |
| `args` | Global default args |
| `argTypes` | Global arg metadata |
| `tags` | Tags applied to all stories (e.g., `autodocs`) |
| `initialGlobals` | Default global values (viewport, locale) |
| `loaders` | Async data loading before all stories |
| `beforeAll` | One-time setup before any story runs |
| `beforeEach` | Setup before each story renders |

### Importing Global Styles

Import CSS, SCSS, or other styles at the top of `preview.ts`:

```typescript
import '../src/styles/globals.css';
import '../src/styles/tailwind.css';
```

## Manager Configuration

`.storybook/manager.ts` customizes the Storybook UI shell:

```typescript
import { addons } from 'storybook/manager-api';
import { themes } from 'storybook/theming';

addons.setConfig({
  theme: themes.dark,
  sidebar: {
    showRoots: true,
  },
  toolbar: {
    zoom: { hidden: true },
  },
});
```

## Running Storybook

```bash
# Start dev server (default: http://localhost:6006)
npm run storybook

# Build static output
npm run build-storybook

# Custom port
npm run storybook -- --port 9009

# Specify config directory
npm run storybook -- --config-dir .storybook
```

## Troubleshooting

### Webpack 4 Projects

Upgrade to Webpack 5 first:

```bash
npx storybook@latest automigrate
```

### Yarn PnP

Generated `node_modules` folders can be safely added to `.gitignore`.

### Vite Projects Without Vite Installed

Manually install Vite before initializing Storybook:

```bash
npm install vite --save-dev
npm create storybook@latest
```

### Monorepo Setup

If Storybook can't resolve components, use explicit paths in story imports:

```typescript
import { Button } from '@my-org/components/src/Button';
```

### Resetting Configuration

```bash
npx storybook@latest automigrate
```

## Related Topics

- [Writing Stories](02-writing-stories.md) — CSF format and story patterns
- [Configuration](10-configuration.md) — Advanced configuration options
- [Addons](09-addons-ecosystem.md) — Installing and configuring addons
