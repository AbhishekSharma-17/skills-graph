# shadcn/ui — Registry & Blocks

> Source: [ui.shadcn.com/docs/registry](https://ui.shadcn.com/docs/registry) | [ui.shadcn.com/blocks](https://ui.shadcn.com/blocks)

## Table of Contents
- [Registry Overview](#registry-overview)
- [Building a Custom Registry](#building-a-custom-registry)
- [Registry Item Schema](#registry-item-schema)
- [Registry Types](#registry-types)
- [Building and Publishing](#building-and-publishing)
- [Consuming Registries](#consuming-registries)
- [Blocks](#blocks)
- [Design System Presets](#design-system-presets)
- [Common Patterns](#common-patterns)

## Registry Overview

The shadcn/ui registry is a code distribution system. It defines a schema for components, hooks, utilities, and entire design systems, then uses the CLI to distribute them across projects.

Key concepts:
- **Registry items** are JSON files conforming to the `registry-item` schema
- **Components, hooks, pages, config, CSS, and fonts** can all be registry items
- The CLI resolves dependencies, copies files, and installs packages automatically
- **Cross-framework** — not limited to React (works with any project type)
- A registry can be hosted anywhere that serves JSON (Vercel, Netlify, static files)

## Building a Custom Registry

### 1. Create registry.json

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry.json",
  "name": "acme-ui",
  "homepage": "https://acme.com",
  "items": [
    {
      "name": "fancy-button",
      "type": "registry:ui",
      "title": "Fancy Button",
      "description": "An animated button with shimmer effect.",
      "dependencies": ["framer-motion"],
      "files": [
        {
          "path": "registry/fancy-button.tsx",
          "type": "registry:ui",
          "target": "components/ui/fancy-button.tsx"
        }
      ]
    },
    {
      "name": "use-debounce",
      "type": "registry:hook",
      "title": "useDebounce",
      "description": "A debounce hook for input values.",
      "files": [
        {
          "path": "registry/use-debounce.ts",
          "type": "registry:hook",
          "target": "hooks/use-debounce.ts"
        }
      ]
    }
  ]
}
```

### 2. Create the component files

```tsx
// registry/fancy-button.tsx
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface FancyButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  shimmer?: boolean;
}

export function FancyButton({ className, shimmer = true, children, ...props }: FancyButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "relative inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground overflow-hidden",
        className
      )}
      {...props}
    >
      {shimmer && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          animate={{ x: ["-100%", "100%"] }}
          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        />
      )}
      {children}
    </motion.button>
  );
}
```

### 3. Build the registry

```bash
npx shadcn@latest build
```

This generates JSON files in `public/r/`:
```
public/r/
├── fancy-button.json
├── use-debounce.json
└── index.json
```

### 4. Deploy

Deploy your project. Registry files are served as static JSON from `/r/`.

## Registry Item Schema

Required fields for every registry item:

```typescript
interface RegistryItem {
  name: string;           // Unique identifier (kebab-case)
  type: RegistryType;     // See Registry Types
  title?: string;         // Human-readable title
  description?: string;   // What it does
  dependencies?: string[];    // npm packages needed
  devDependencies?: string[]; // Dev npm packages
  registryDependencies?: string[]; // Other registry items needed
  files: RegistryFile[];  // Source files
  cssVars?: {
    light?: Record<string, string>;
    dark?: Record<string, string>;
  };
  css?: string;           // Additional CSS to inject
  meta?: Record<string, unknown>;
}

interface RegistryFile {
  path: string;   // Source path in your registry project
  type: string;   // File type (registry:ui, registry:hook, etc.)
  target?: string; // Where to install in consuming project
}
```

## Registry Types

| Type | Purpose | Install Location |
|------|---------|-----------------|
| `registry:ui` | UI components | `components/ui/` |
| `registry:hook` | React hooks | `hooks/` |
| `registry:lib` | Utility functions | `lib/` |
| `registry:page` | Full pages | `app/` or `pages/` |
| `registry:block` | Multi-file blocks | Various |
| `registry:component` | Non-UI components | `components/` |
| `registry:theme` | Theme configuration | CSS file |
| `registry:base` | Full design system | Multiple locations |
| `registry:font` | Font configuration | CSS + config |

### registry:base — Design System Distribution

A `registry:base` item packages your entire design system into one installable payload:

```json
{
  "name": "acme-design-system",
  "type": "registry:base",
  "description": "ACME Corp design system",
  "cssVars": {
    "light": {
      "--primary": "oklch(0.55 0.2 250)",
      "--primary-foreground": "oklch(0.98 0 0)"
    },
    "dark": {
      "--primary": "oklch(0.7 0.2 250)",
      "--primary-foreground": "oklch(0.15 0 0)"
    }
  },
  "dependencies": ["lucide-react"],
  "files": [
    { "path": "registry/globals.css", "type": "registry:theme" },
    { "path": "registry/cn.ts", "type": "registry:lib" }
  ]
}
```

## Building and Publishing

### Build Command

```bash
# Build all registry items
npx shadcn@latest build

# Custom output directory
npx shadcn@latest build --output dist/registry
```

The build process:
1. Reads `registry.json`
2. Resolves all file references
3. Inlines file contents into JSON
4. Outputs individual `.json` files + `index.json`

### Hosting Options

- **Vercel/Netlify** — deploy as static files in `public/r/`
- **GitHub Pages** — serve from repository
- **npm** — publish JSON files as a package
- **CDN** — host JSON files on any CDN
- **Internal server** — serve from company infrastructure

### Versioning

Include version in your registry URL for breaking changes:

```
https://acme.com/r/v2/fancy-button.json
```

## Consuming Registries

### Add Registry to Project

```bash
# Add registry source
npx shadcn@latest registry add https://acme.com/r

# Install items from it
npx shadcn@latest add fancy-button
```

### Add via Direct URL

```bash
npx shadcn@latest add https://acme.com/r/fancy-button.json
```

### Configure in components.json

```json
{
  "registries": {
    "acme": {
      "url": "https://acme.com/r"
    }
  }
}
```

Then reference with prefix:

```bash
npx shadcn@latest add acme/fancy-button
```

## Blocks

Blocks are pre-built, multi-file UI sections available from the official registry.

### Available Block Categories

- **Dashboard** — admin dashboards with charts, tables, KPIs
- **Authentication** — login, signup, forgot password
- **Sidebar** — application sidebars with navigation
- **Forms** — multi-step forms, settings pages
- **Cards** — product cards, pricing cards, profile cards
- **Landing** — hero sections, feature grids, testimonials

### Using Blocks

```bash
# Browse blocks at ui.shadcn.com/blocks
# Install a specific block
npx shadcn@latest add dashboard-01

# Available in both Radix and Base UI variants
```

### Block Structure

A block can include multiple files:

```json
{
  "name": "dashboard-01",
  "type": "registry:block",
  "files": [
    { "path": "blocks/dashboard-01/page.tsx", "target": "app/dashboard/page.tsx" },
    { "path": "blocks/dashboard-01/components/chart.tsx", "target": "components/dashboard/chart.tsx" },
    { "path": "blocks/dashboard-01/components/recent-sales.tsx", "target": "components/dashboard/recent-sales.tsx" }
  ],
  "registryDependencies": ["card", "chart", "table", "avatar"]
}
```

## Design System Presets

Presets bundle colors, fonts, icons, and radius into a single config:

```bash
# Apply a preset
npx shadcn@latest apply --preset nova

# Preview at shadcn/create
```

A preset modifies:
- CSS variables (colors, radius)
- Font family
- Icon library preference
- Any other theme token

Presets don't modify component source code — they only affect the design token layer.

## Common Patterns

### Internal Component Library

```
packages/ui/
├── registry.json
├── registry/
│   ├── fancy-button.tsx
│   ├── data-grid.tsx
│   └── user-card.tsx
├── public/r/
│   ├── fancy-button.json
│   ├── data-grid.json
│   └── index.json
└── package.json
```

Teams install from the internal registry URL.

### Monorepo Component Sharing

```bash
# In packages/ui
npx shadcn@latest build

# In apps/web
npx shadcn@latest add https://localhost:3001/r/fancy-button.json
```

### Registry with Dependencies

If your component depends on other shadcn/ui components:

```json
{
  "name": "user-profile-card",
  "registryDependencies": ["card", "avatar", "badge", "button"],
  "dependencies": ["date-fns"],
  "files": [...]
}
```

The CLI installs both npm and registry dependencies automatically.
