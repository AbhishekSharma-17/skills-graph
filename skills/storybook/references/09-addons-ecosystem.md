# Storybook — Addons & Ecosystem

> Source: https://storybook.js.org/docs/addons | https://storybook.js.org/docs/essentials | v10.5.3

## Table of Contents

- [Essentials Overview](#essentials-overview)
- [Actions Addon](#actions-addon)
- [Backgrounds Addon](#backgrounds-addon)
- [Viewport Addon](#viewport-addon)
- [Toolbars & Globals](#toolbars--globals)
- [Highlight Addon](#highlight-addon)
- [Measure & Outline](#measure--outline)
- [Installing Addons](#installing-addons)
- [Addon Catalog](#addon-catalog)
- [Disabling Features](#disabling-features)

## Essentials Overview

Storybook Essentials is a zero-config addon bundle included by default. It provides the most commonly needed features for component development.

### Included Features

| Feature | Purpose |
|---------|---------|
| Actions | Log and inspect event handler calls |
| Backgrounds | Switch background colors for contrast testing |
| Controls | Interactive arg manipulation (covered in 03-args-controls.md) |
| Highlight | Highlight DOM elements programmatically |
| Measure & Outline | Display layout dimensions and borders |
| Toolbars & Globals | Add custom toolbar items for global settings |
| Viewport | Test responsive layouts at different screen sizes |

## Actions Addon

The Actions addon captures event handler calls and displays their arguments in the Actions panel.

### Recommended: fn() Spies

```typescript
import type { Meta } from '@storybook/react';
import { fn } from 'storybook/test';
import { Button } from './Button';

const meta = {
  component: Button,
  args: {
    onClick: fn(),
    onMouseEnter: fn(),
  },
} satisfies Meta<typeof Button>;
```

Functions created with `fn()` are both logged to the Actions panel and usable as test spies.

### Auto-Actions via Regex

Match callback prop names automatically:

```typescript
// .storybook/preview.ts
const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on.*' },
  },
};
```

Auto-detected actions are **not** available as spies in play functions.

### Legacy action() Function

```typescript
import { action } from 'storybook/actions';

const meta = {
  component: Button,
  args: {
    onClick: action('clicked'),
  },
};
```

### Configuration

```typescript
import { configureActions } from 'storybook/actions';

configureActions({
  limit: 20,              // Max action entries (default: 50)
  clearOnStoryChange: true, // Reset on navigation (default: true)
  depth: 10,               // Serialization depth (default: 10)
});
```

## Backgrounds Addon

Switch background colors to test component appearance on different surfaces.

### Configuration

```typescript
// .storybook/preview.ts
const preview: Preview = {
  parameters: {
    backgrounds: {
      default: 'light',
      options: {
        light: { name: 'Light', value: '#ffffff' },
        dark: { name: 'Dark', value: '#1a1a2e' },
        brand: { name: 'Brand Blue', value: '#1ea7fd' },
      },
    },
  },
};
```

### Per-Story Override

```typescript
export const OnDark: Story = {
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
};
```

## Viewport Addon

Test responsive layouts by adjusting the preview iframe dimensions.

### Built-in Presets

**Minimal (Default):**

| Viewport | Dimensions |
|----------|-----------|
| `mobile1` | 320 x 568 |
| `mobile2` | 414 x 896 |
| `tablet` | 834 x 1112 |
| `desktop` | 1024 x 1280 |

**Detailed (`INITIAL_VIEWPORTS`):** iPhone 5-14 Pro Max, Galaxy S5/S9, iPad variants, and more.

### Using Detailed Viewports

```typescript
import { INITIAL_VIEWPORTS } from 'storybook/viewport';

const preview: Preview = {
  parameters: {
    viewport: {
      options: INITIAL_VIEWPORTS,
    },
  },
};
```

### Custom Viewports

```typescript
import { MINIMAL_VIEWPORTS } from 'storybook/viewport';

const customViewports = {
  kindleFire: {
    name: 'Kindle Fire 2',
    styles: { width: '600px', height: '963px' },
  },
  pixel5: {
    name: 'Pixel 5',
    styles: { width: '393px', height: '851px' },
  },
};

const preview: Preview = {
  parameters: {
    viewport: {
      options: { ...MINIMAL_VIEWPORTS, ...customViewports },
    },
  },
};
```

### Per-Story Default Viewport

```typescript
export const MobileView: Story = {
  globals: {
    viewport: { value: 'mobile1', isRotated: false },
  },
};
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Alt + V | Next viewport |
| Alt + Shift + V | Previous viewport |
| Alt + Control + V | Reset viewport |

## Toolbars & Globals

Add custom toolbar items that set global values across all stories.

### Define Global Types

```typescript
// .storybook/preview.ts
const preview: Preview = {
  globalTypes: {
    theme: {
      description: 'Global theme',
      toolbar: {
        title: 'Theme',
        icon: 'paintbrush',
        items: [
          { value: 'light', title: 'Light', icon: 'sun' },
          { value: 'dark', title: 'Dark', icon: 'moon' },
        ],
        dynamicTitle: true,
      },
    },
    locale: {
      description: 'Locale',
      toolbar: {
        title: 'Locale',
        icon: 'globe',
        items: ['en', 'fr', 'de', 'ja'],
      },
    },
  },
  initialGlobals: {
    theme: 'light',
    locale: 'en',
  },
};
```

### Consuming Globals in Decorators

```typescript
const preview: Preview = {
  decorators: [
    (Story, { globals }) => {
      const theme = globals.theme || 'light';
      return (
        <ThemeProvider theme={theme}>
          <Story />
        </ThemeProvider>
      );
    },
  ],
};
```

## Highlight Addon

Programmatically highlight DOM elements in the preview:

```typescript
import { useEffect } from 'react';
import { useChannel } from 'storybook/preview-api';
import { HIGHLIGHT } from 'storybook/highlight';

const meta = {
  component: MyComponent,
  decorators: [
    (Story) => {
      const emit = useChannel({});
      useEffect(() => {
        emit(HIGHLIGHT, {
          elements: ['.highlight-me', '#important-element'],
        });
      }, []);
      return <Story />;
    },
  ],
} satisfies Meta<typeof MyComponent>;
```

## Measure & Outline

- **Measure**: Shows spacing, padding, and margin overlays on hover
- **Outline**: Adds borders to all elements for layout debugging

Both are toggled via toolbar buttons. No configuration needed.

## Installing Addons

### From npm

```bash
npm install @storybook/addon-links --save-dev
```

Register in `.storybook/main.ts`:

```typescript
const config: StorybookConfig = {
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-a11y',
    '@storybook/addon-vitest',
  ],
};
```

### Using the CLI

```bash
npx storybook add @storybook/addon-a11y
```

This installs the package and updates `main.ts` automatically.

## Addon Catalog

The Storybook addon catalog at [storybook.js.org/addons](https://storybook.js.org/addons) lists 400+ community and official addons organized by category:

- **Essentials** — Built-in core features
- **Code** — Source code display, Storybook composition
- **Data & State** — Mock APIs, state management
- **Design** — Figma, design tokens, color palettes
- **Test** — Accessibility, visual regression, performance
- **Appearance** — Themes, dark mode, CSS utilities

### Popular Community Addons

| Addon | Purpose |
|-------|---------|
| `@storybook/addon-links` | Navigate between stories |
| `storybook-addon-designs` | Embed Figma/Sketch designs |
| `storybook-dark-mode` | Toggle dark/light mode |
| `@storybook/addon-storysource` | Show story source code |
| `msw-storybook-addon` | Mock API requests with MSW |

## Disabling Features

Disable individual Essentials features in `.storybook/main.ts`:

```typescript
const config: StorybookConfig = {
  features: {
    actions: true,
    backgrounds: false,    // Disable backgrounds
    controls: true,
    highlight: true,
    measure: true,
    outline: true,
    toolbars: true,
    viewport: true,
  },
};
```

## Common Pitfalls

1. **Addon order matters** — Addons load in the order listed in `main.ts`
2. **Missing addon registration** — Install AND register in `main.ts`
3. **Auto-actions not spyable** — Use `fn()` instead of `argTypesRegex` for testable callbacks
4. **Global toolbar not showing** — Ensure `globalTypes` is configured in `preview.ts`

## Related Topics

- [Args & Controls](03-args-controls.md) — Controls addon deep dive
- [Configuration](10-configuration.md) — Main and preview configuration
- [Visual & A11y Testing](07-visual-a11y-testing.md) — Testing addons
