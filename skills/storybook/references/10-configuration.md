# Storybook — Configuration

> Source: https://storybook.js.org/docs/configure | v10.5.3

## Table of Contents

- [Configuration Files](#configuration-files)
- [Main Configuration](#main-configuration)
- [Preview Configuration](#preview-configuration)
- [Manager Configuration](#manager-configuration)
- [Builder Configuration](#builder-configuration)
- [Styling and CSS](#styling-and-css)
- [TypeScript Configuration](#typescript-configuration)
- [Environment Variables](#environment-variables)
- [Story Rendering](#story-rendering)
- [UI Customization](#ui-customization)

## Configuration Files

```
.storybook/
├── main.ts          # Build: framework, addons, story globs, builders
├── preview.ts       # Runtime: decorators, parameters, globals, tags
├── manager.ts       # UI: theme, sidebar, toolbar customization
├── preview-head.html  # Custom <head> content for preview iframe
└── manager-head.html  # Custom <head> content for manager UI
```

## Main Configuration

`.storybook/main.ts` controls how Storybook builds. It is the primary configuration file.

```typescript
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  // Required
  framework: '@storybook/react-vite',
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],

  // Addons
  addons: [
    '@storybook/addon-docs',
    '@storybook/addon-a11y',
    '@storybook/addon-vitest',
  ],

  // Static files
  staticDirs: ['../public'],

  // TypeScript
  typescript: {
    reactDocgen: 'react-docgen-typescript',
    check: false,
  },

  // Documentation
  docs: {
    defaultName: 'Docs',
    docsMode: false,
  },

  // Core settings
  core: {
    disableTelemetry: true,
  },

  // Feature flags
  features: {
    backgrounds: true,
    measure: true,
  },

  // Build optimization
  build: {
    test: {
      disableBlocks: false,
      disableMDXEntries: false,
      disableAutoDocs: false,
      disableDocgen: false,
    },
  },
};

export default config;
```

### Main Configuration Options

| Option | Type | Purpose |
|--------|------|---------|
| `framework` | string | Framework package |
| `stories` | (string \| object)[] | Story file patterns |
| `addons` | (string \| object)[] | Addon packages |
| `staticDirs` | string[] | Static asset directories |
| `typescript` | object | TS processing options |
| `docs` | object | Documentation settings |
| `core` | object | Internal feature config |
| `features` | object | Enable/disable features |
| `build` | object | Production build optimization |
| `refs` | object | Storybook composition |
| `logLevel` | string | Browser logging level |
| `env` | function | Custom environment variables |
| `viteFinal` | function | Vite config customization |
| `webpackFinal` | function | Webpack config customization |

### Story Glob Patterns

```typescript
// Simple glob
stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)']

// With title prefix
stories: [{
  directory: '../packages/ui',
  files: '**/*.stories.@(js|jsx|ts|tsx)',
  titlePrefix: 'UI Library',
}]

// Multiple sources
stories: [
  '../src/**/*.stories.@(js|jsx|ts|tsx)',
  '../packages/**/*.stories.@(js|jsx|ts|tsx)',
  '../docs/**/*.mdx',
]
```

## Preview Configuration

`.storybook/preview.ts` controls story rendering defaults.

```typescript
import type { Preview } from '@storybook/react';
import '../src/styles/globals.css';

const preview: Preview = {
  // Global decorators
  decorators: [
    (Story) => (
      <div style={{ padding: '1rem' }}>
        <Story />
      </div>
    ),
  ],

  // Global parameters
  parameters: {
    layout: 'centered',
    controls: {
      expanded: true,
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      default: 'light',
      options: {
        light: { name: 'Light', value: '#fff' },
        dark: { name: 'Dark', value: '#333' },
      },
    },
  },

  // Global tags
  tags: ['autodocs'],

  // Global toolbar items
  globalTypes: {
    theme: {
      description: 'Theme selector',
      toolbar: {
        title: 'Theme',
        icon: 'paintbrush',
        items: ['light', 'dark'],
        dynamicTitle: true,
      },
    },
  },

  // Initial global values
  initialGlobals: {
    theme: 'light',
  },

  // Lifecycle hooks
  async beforeAll() {
    // One-time setup
  },
  async beforeEach() {
    // Per-story setup
  },
};

export default preview;
```

### Layout Options

```typescript
parameters: {
  layout: 'centered',    // Center component in viewport
  layout: 'fullscreen',  // No padding, fills viewport
  layout: 'padded',      // Default padding around component
}
```

## Manager Configuration

`.storybook/manager.ts` customizes the Storybook UI shell:

```typescript
import { addons } from 'storybook/manager-api';
import { create } from 'storybook/theming';

const customTheme = create({
  base: 'light',
  brandTitle: 'My Design System',
  brandUrl: 'https://mycompany.com',
  brandImage: '/logo.svg',
  brandTarget: '_self',

  // Colors
  colorPrimary: '#1ea7fd',
  colorSecondary: '#ff4785',

  // UI
  appBg: '#f6f9fc',
  appContentBg: '#ffffff',
  appBorderColor: '#e0e0e0',
  appBorderRadius: 4,

  // Text
  textColor: '#333333',
  textInverseColor: '#ffffff',

  // Toolbar
  barTextColor: '#999999',
  barSelectedColor: '#1ea7fd',
  barBg: '#ffffff',
});

addons.setConfig({
  theme: customTheme,
  sidebar: {
    showRoots: true,
    collapsedRoots: ['other'],
  },
  toolbar: {
    zoom: { hidden: false },
    backgrounds: { hidden: false },
    viewport: { hidden: false },
  },
});
```

## Builder Configuration

### Vite Builder

```typescript
// .storybook/main.ts
const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  async viteFinal(config) {
    const { mergeConfig } = await import('vite');
    return mergeConfig(config, {
      resolve: {
        alias: {
          '@': '/src',
          '@components': '/src/components',
        },
      },
      css: {
        modules: {
          localsConvention: 'camelCase',
        },
      },
    });
  },
};
```

### Webpack Builder

```typescript
const config: StorybookConfig = {
  framework: '@storybook/react-webpack5',
  webpackFinal: async (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, '../src'),
    };

    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    return config;
  },
};
```

## Styling and CSS

### Global Styles

Import in `.storybook/preview.ts`:

```typescript
import '../src/styles/globals.css';
import '../src/styles/tailwind.css';
```

### CSS Modules

Supported by default with Vite. Webpack requires configuration.

### PostCSS

Works with Vite out of the box if `postcss.config.js` exists in your project root.

### Tailwind CSS

```typescript
// .storybook/preview.ts
import '../src/styles/tailwind.css';
```

Ensure your `tailwind.config.js` content paths include `.storybook/`:

```javascript
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './.storybook/**/*.{js,jsx,ts,tsx}',
  ],
};
```

### Custom Head HTML

```html
<!-- .storybook/preview-head.html -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Inter" />
<style>
  body { font-family: 'Inter', sans-serif; }
</style>
```

## TypeScript Configuration

```typescript
// .storybook/main.ts
const config: StorybookConfig = {
  typescript: {
    // Prop table generation
    reactDocgen: 'react-docgen-typescript',  // or 'react-docgen'

    // react-docgen-typescript options
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      shouldRemoveUndefinedFromOptional: true,
      propFilter: (prop) =>
        prop.parent ? !/node_modules/.test(prop.parent.fileName) : true,
    },

    // Type checking (slows build)
    check: false,
  },
};
```

### DocGen Comparison

| Feature | react-docgen | react-docgen-typescript |
|---------|-------------|----------------------|
| Speed | Faster | Slower |
| Accuracy | Good | Better |
| Enum values | Limited | Full |
| Interface merging | No | Yes |
| Recommended | Small projects | Design systems |

## Environment Variables

### In main.ts

```typescript
const config: StorybookConfig = {
  env: (config) => ({
    ...config,
    API_URL: 'https://api.example.com',
    FEATURE_FLAG: 'true',
  }),
};
```

### Accessing in Stories

Environment variables prefixed with `STORYBOOK_` are available automatically:

```bash
STORYBOOK_API_URL=https://api.example.com npm run storybook
```

Access in code via `process.env.STORYBOOK_API_URL`.

## Story Rendering

### Default Parameters

```typescript
// .storybook/preview.ts
const preview: Preview = {
  parameters: {
    layout: 'centered',
    backgrounds: { default: 'light' },
  },
};
```

### Story Sorting

```typescript
const preview: Preview = {
  parameters: {
    options: {
      storySort: {
        order: ['Introduction', 'Design System', ['Colors', 'Typography'], 'Components'],
        method: 'alphabetical',
      },
    },
  },
};
```

## UI Customization

### Sidebar Configuration

```typescript
// .storybook/manager.ts
addons.setConfig({
  sidebar: {
    showRoots: true,
    collapsedRoots: ['archived'],
    renderLabel: (item) => item.name.toUpperCase(),
  },
});
```

### SEO for Published Storybooks

```html
<!-- .storybook/manager-head.html -->
<meta name="description" content="Component library docs" />
<meta name="robots" content="noindex" />
```

## Common Pitfalls

1. **Import order in preview.ts** — CSS imports must come before export
2. **viteFinal vs webpackFinal** — Use the one matching your builder
3. **Telemetry opt-out** — Set `core.disableTelemetry: true` in main.ts
4. **Static files not loading** — Check `staticDirs` paths are relative to `.storybook/`
5. **TypeScript docgen slow** — Switch to `react-docgen` for faster builds

## Related Topics

- [Installation & Setup](01-installation-setup.md) — Initial project configuration
- [Addons Ecosystem](09-addons-ecosystem.md) — Addon registration
- [Documentation](08-documentation.md) — Docs configuration
