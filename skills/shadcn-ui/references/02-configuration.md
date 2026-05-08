# shadcn/ui — Configuration

> Source: [ui.shadcn.com/docs/components-json](https://ui.shadcn.com/docs/components-json) | [ui.shadcn.com/docs/tailwind-v4](https://ui.shadcn.com/docs/tailwind-v4)

## Table of Contents
- [components.json](#componentsjson)
- [Configuration Options](#configuration-options)
- [Tailwind v4 Setup](#tailwind-v4-setup)
- [Tailwind v3 Setup (Legacy)](#tailwind-v3-setup-legacy)
- [Path Aliases](#path-aliases)
- [CSS Variables Setup](#css-variables-setup)
- [Framework-Specific Config](#framework-specific-config)
- [Monorepo Configuration](#monorepo-configuration)

## components.json

The `components.json` file is the configuration file for your project. It tells the CLI where to install components, how to resolve paths, and which style/theme to use.

Created automatically by `npx shadcn@latest init`. Located at the project root.

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "tailwind": {
    "config": "",
    "css": "src/app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "rsc": true,
  "tsx": true,
  "aliases": {
    "utils": "@/lib/utils",
    "components": "@/components",
    "ui": "@/components/ui",
    "hooks": "@/hooks",
    "lib": "@/lib"
  },
  "registries": {}
}
```

## Configuration Options

### style

The component style variant. Currently available:

- `"new-york"` — uses the unified `radix-ui` package (recommended)
- `"default"` — legacy style with individual Radix packages

### tailwind.config

Path to your Tailwind config file. **For Tailwind v4, leave this as an empty string** — v4 uses CSS-based configuration via `@theme` instead of a JS config file.

```json
{
  "tailwind": {
    "config": ""
  }
}
```

For Tailwind v3:

```json
{
  "tailwind": {
    "config": "tailwind.config.ts"
  }
}
```

### tailwind.css

Path to your global CSS file where Tailwind is imported and CSS variables are defined.

```json
{
  "tailwind": {
    "css": "src/app/globals.css"
  }
}
```

### tailwind.baseColor

Base color palette for generating theme tokens. Options: `neutral`, `stone`, `zinc`, `mauve`, `olive`, `mist`, `taupe`.

### tailwind.cssVariables

When `true` (default), components use semantic CSS variable tokens like `bg-background`, `text-foreground`, `border-border`.

When `false`, components use inline Tailwind color utilities like `bg-white`, `text-zinc-950`.

**This cannot be changed after initialization.** Switching requires removing and re-adding all components.

### tailwind.prefix

Optional prefix for Tailwind utility classes. Useful when integrating with existing CSS.

```json
{
  "tailwind": {
    "prefix": "tw-"
  }
}
```

Components would use `tw-bg-background` instead of `bg-background`.

### rsc

Set to `true` for React Server Components support (Next.js App Router). When enabled, the CLI adds `"use client"` directives to client-side components automatically.

### tsx

Set to `true` for TypeScript (`.tsx`). Set to `false` for JavaScript (`.jsx`).

### aliases

Path aliases for resolving imports. Must match your `tsconfig.json` paths.

```json
{
  "aliases": {
    "utils": "@/lib/utils",
    "components": "@/components",
    "ui": "@/components/ui",
    "hooks": "@/hooks",
    "lib": "@/lib"
  }
}
```

### registries

Custom registries for third-party component sources.

```json
{
  "registries": {
    "acme": {
      "url": "https://acme.com/r"
    }
  }
}
```

## Tailwind v4 Setup

Tailwind v4 uses CSS-based configuration with `@theme` directives instead of `tailwind.config.js`.

### Global CSS (globals.css)

```css
@import "tailwindcss";

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}

:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --radius: 0.625rem;
  /* ... more tokens */
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.985 0 0);
  --primary-foreground: oklch(0.205 0 0);
  /* ... more tokens */
}
```

### Key Changes from v3

- **No `tailwind.config.js`** — configuration lives in CSS via `@theme`
- **OKLCH colors** — replaces HSL for wider gamut and perceptual uniformity
- **`@theme inline`** — maps CSS variables to Tailwind utilities
- **No `@layer base`** — color definitions go in `:root` and `.dark` selectors

## Tailwind v3 Setup (Legacy)

```javascript
// tailwind.config.ts
const config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... more semantic colors
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
};
```

## Path Aliases

### tsconfig.json

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Vite (vite.config.ts)

```typescript
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

### package.json (for non-TS projects)

```json
{
  "imports": {
    "#*": "./src/*"
  }
}
```

## CSS Variables Setup

Components use semantic background/foreground pairs. The base token controls the surface color; the `-foreground` token controls text/icons on that surface.

| Token | Purpose |
|-------|---------|
| `--background` / `--foreground` | Page background and body text |
| `--card` / `--card-foreground` | Card surfaces |
| `--popover` / `--popover-foreground` | Popover/dropdown surfaces |
| `--primary` / `--primary-foreground` | Primary buttons and actions |
| `--secondary` / `--secondary-foreground` | Secondary elements |
| `--muted` / `--muted-foreground` | Muted/disabled states |
| `--accent` / `--accent-foreground` | Hover highlights |
| `--destructive` / `--destructive-foreground` | Destructive actions |
| `--border` | Default border color |
| `--input` | Input field borders |
| `--ring` | Focus ring color |
| `--radius` | Base border radius |

## Framework-Specific Config

### Next.js App Router

```json
{
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/app/globals.css"
  }
}
```

### Vite + React

```json
{
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css"
  }
}
```

### Astro

```json
{
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/styles/globals.css"
  }
}
```

## Monorepo Configuration

For monorepo setups, specify the working directory:

```bash
npx shadcn@latest init -c packages/ui
npx shadcn@latest add button -c packages/ui
```

Or create a `components.json` in each package with appropriate paths:

```json
{
  "aliases": {
    "utils": "@repo/ui/lib/utils",
    "components": "@repo/ui/components",
    "ui": "@repo/ui/components/ui"
  }
}
```
