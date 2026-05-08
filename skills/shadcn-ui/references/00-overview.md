# shadcn/ui — Overview & Setup

> Source: [ui.shadcn.com/docs](https://ui.shadcn.com/docs) | Package: `shadcn` v4.7.x

## Table of Contents
- [What is shadcn/ui](#what-is-shadcnui)
- [Core Philosophy](#core-philosophy)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation by Framework](#installation-by-framework)
- [Project Structure](#project-structure)
- [Adding Components](#adding-components)
- [The cn Utility](#the-cn-utility)
- [When to Use shadcn/ui](#when-to-use-shadcnui)
- [Comparison with Other Libraries](#comparison-with-other-libraries)

## What is shadcn/ui

shadcn/ui is a code distribution system — not a traditional component library. Instead of installing a package and importing from `node_modules`, you copy component source code directly into your project. This gives you full ownership and control over every component.

It provides beautifully-designed, accessible components built on Radix UI (or Base UI) primitives styled with Tailwind CSS. Components are production-ready with proper ARIA attributes, keyboard navigation, and focus management built in.

Key facts:
- 113K+ GitHub stars
- Used by Vercel, Linear, and thousands of production apps
- Supports React, Next.js, Vite, Remix, Astro, Laravel, TanStack Start
- CLI v4 with AI agent skills support
- Cross-framework registry system

## Core Philosophy

**Open Code:** Components live in your codebase as editable source files. No black-box abstractions — you can read, modify, and extend every line.

**Composition over Configuration:** Build complex UIs by composing small, focused primitives. A Dialog is a Dialog.Trigger + Dialog.Content + Dialog.Header — each piece is independently customizable.

**Copy-Paste Model:** Zero runtime dependency on shadcn/ui itself. Your components have direct dependencies on Radix UI and Tailwind — nothing proprietary sits in between.

**Design Tokens:** Theming via CSS custom properties (OKLCH color space). Change your entire color palette by editing a few CSS variables.

## How It Works

```
1. Run `npx shadcn@latest init` → creates components.json + CSS setup
2. Run `npx shadcn@latest add button` → copies Button component to your project
3. Import from your own codebase: `import { Button } from "@/components/ui/button"`
4. Customize freely — it's your code now
```

The CLI resolves dependencies automatically. Adding `dialog` also installs `@radix-ui/react-dialog` and copies the required CSS.

## Prerequisites

- **React 18+** (React 19 fully supported)
- **Tailwind CSS v4** (v3 also supported with legacy config)
- **TypeScript** (recommended but not required)
- **Node.js 18+**

## Installation by Framework

### Next.js (App Router)

```bash
npx shadcn@latest init -d
```

Or step-by-step:

```bash
# Create Next.js project
npx create-next-app@latest my-app --typescript --tailwind --eslint
cd my-app

# Initialize shadcn/ui
npx shadcn@latest init
```

The CLI asks for:
- Component library: **Radix** or **Base UI**
- Base color: neutral, stone, zinc, etc.
- CSS variables: yes (recommended)

### Vite

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app
npx shadcn@latest init
```

### Remix / React Router

```bash
npx create-remix@latest my-app
cd my-app
npx shadcn@latest init
```

### Astro

```bash
npm create astro@latest my-app
cd my-app
npx shadcn@latest init -d
```

### Manual Installation

If the CLI doesn't support your setup:

1. Install Tailwind CSS
2. Add path aliases (`@/` → `./src/`)
3. Create `components.json` manually
4. Copy the `cn` utility
5. Add CSS variables to your global stylesheet

## Project Structure

After initialization:

```
src/
├── components/
│   └── ui/           # shadcn/ui components live here
│       ├── button.tsx
│       ├── card.tsx
│       └── dialog.tsx
├── lib/
│   └── utils.ts      # cn() utility
├── app/
│   └── globals.css   # CSS variables, Tailwind imports
└── components.json   # shadcn/ui configuration
```

## Adding Components

```bash
# Single component
npx shadcn@latest add button

# Multiple components
npx shadcn@latest add button card dialog input

# All components
npx shadcn@latest add --all

# From URL
npx shadcn@latest add https://example.com/r/custom-component.json

# View before installing
npx shadcn@latest view button
```

Each component is a standalone `.tsx` file with its own imports. No barrel exports, no index files.

## The cn Utility

Every component uses the `cn()` helper for conditional class merging:

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

Usage in components:

```tsx
import { cn } from "@/lib/utils";

function Button({ className, variant, ...props }) {
  return (
    <button
      className={cn(
        "inline-flex items-center rounded-md px-4 py-2 text-sm font-medium",
        variant === "destructive" && "bg-destructive text-destructive-foreground",
        className
      )}
      {...props}
    />
  );
}
```

`cn()` merges Tailwind classes intelligently — later classes override earlier ones. `cn("px-4", "px-6")` → `"px-6"`.

## When to Use shadcn/ui

**Use shadcn/ui when:**
- You want full control over component source code
- You need accessible components without building from scratch
- You're using Tailwind CSS and want consistent styling
- You're building a design system and need a foundation
- You want to distribute components via a registry

**Consider alternatives when:**
- You need a zero-config drop-in library (use Chakra UI or Ant Design)
- You don't use Tailwind CSS
- You want automatic updates without manual migration
- You need components for non-React frameworks (though registry supports others)

## Comparison with Other Libraries

| Feature | shadcn/ui | Material UI | Chakra UI | Ant Design |
|---------|-----------|-------------|-----------|------------|
| Code ownership | Full (copy) | Package | Package | Package |
| Styling | Tailwind CSS | Emotion/CSS | Emotion | CSS-in-JS |
| Bundle impact | Only what you use | Tree-shakeable | Tree-shakeable | Large |
| Customization | Edit source | Theme API | Theme API | Less vars |
| Accessibility | Radix UI | Built-in | Built-in | Partial |
| Updates | Manual | npm update | npm update | npm update |
| Learning curve | Low | Medium | Medium | High |

## Common Pitfalls

1. **Don't `npm install shadcn-ui`** — the npm package is just the CLI tooling. Components are copied into your project via `npx shadcn@latest add`.

2. **Path aliases required** — components import from `@/lib/utils` and `@/components/ui/*`. Ensure your `tsconfig.json` has the `@/*` alias configured.

3. **Tailwind v4 vs v3** — if using Tailwind v4, leave `tailwind.config` blank in `components.json`. The `@theme` directive replaces the old config file.

4. **Don't override Radix internals** — components like Dialog and Dropdown have carefully managed focus and ARIA. Wrapping them in extra divs or changing the DOM structure breaks accessibility.

5. **CSS variables must be defined** — components reference tokens like `--background`, `--foreground`, `--primary`. If these aren't in your CSS, components render without colors.
