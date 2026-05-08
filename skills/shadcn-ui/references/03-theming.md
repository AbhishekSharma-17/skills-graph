# shadcn/ui — Theming

> Source: [ui.shadcn.com/docs/theming](https://ui.shadcn.com/docs/theming) | [ui.shadcn.com/docs/dark-mode](https://ui.shadcn.com/docs/dark-mode)

## Table of Contents
- [Color System](#color-system)
- [OKLCH Color Space](#oklch-color-space)
- [Semantic Token Pairs](#semantic-token-pairs)
- [Dark Mode](#dark-mode)
- [Custom Themes](#custom-themes)
- [Presets](#presets)
- [Chart Colors](#chart-colors)
- [Typography Tokens](#typography-tokens)
- [Common Patterns](#common-patterns)

## Color System

shadcn/ui uses semantic CSS custom properties for all colors. Instead of referencing `blue-500` directly, components use tokens like `primary`, `secondary`, `muted` — allowing the entire color scheme to change by updating a few CSS variables.

Colors are defined in your global CSS file (typically `globals.css` or `index.css`):

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);
  --radius: 0.625rem;
}
```

## OKLCH Color Space

Tailwind v4 and shadcn/ui use OKLCH (Oklab Lightness, Chroma, Hue) instead of HSL:

```
oklch(L C H)
  L = lightness (0 = black, 1 = white)
  C = chroma/saturation (0 = gray, higher = more vivid)
  H = hue angle (0-360 degrees)
```

Benefits over HSL:
- **Perceptually uniform** — same lightness value looks equally bright across hues
- **Wider gamut** — supports P3 displays and modern monitors
- **Better dark mode** — more natural color transitions

Examples:
```css
--primary: oklch(0.205 0 0);          /* Near-black, neutral */
--primary: oklch(0.5 0.2 250);        /* Medium blue */
--destructive: oklch(0.577 0.245 27); /* Vivid red */
--success: oklch(0.6 0.2 145);        /* Green */
```

## Semantic Token Pairs

Every semantic color has a base + foreground pair:

| Token | Surface | Text on surface |
|-------|---------|-----------------|
| `--background` | Page background | `--foreground` |
| `--card` | Card surface | `--card-foreground` |
| `--popover` | Popover surface | `--popover-foreground` |
| `--primary` | Primary buttons | `--primary-foreground` |
| `--secondary` | Secondary buttons | `--secondary-foreground` |
| `--muted` | Muted areas | `--muted-foreground` |
| `--accent` | Hover states | `--accent-foreground` |
| `--destructive` | Delete/error | `--destructive-foreground` |

Usage in Tailwind classes:

```tsx
// Surface color
<div className="bg-primary text-primary-foreground">
  Primary surface with readable text
</div>

// Card with proper tokens
<div className="bg-card text-card-foreground border-border">
  Card content
</div>

// Muted text
<p className="text-muted-foreground">Secondary information</p>
```

## Dark Mode

### CSS Setup

Override the same tokens inside `.dark`:

```css
.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.145 0 0);
  --card-foreground: oklch(0.985 0 0);
  --primary: oklch(0.985 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.269 0 0);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.396 0.141 25.723);
  --border: oklch(0.269 0 0);
  --input: oklch(0.269 0 0);
  --ring: oklch(0.439 0 0);
}
```

### Next.js with next-themes

```bash
npm install next-themes
```

```tsx
// app/providers.tsx
"use client";

import { ThemeProvider } from "next-themes";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      {children}
    </ThemeProvider>
  );
}
```

```tsx
// app/layout.tsx
import { Providers } from "./providers";

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

### Theme Toggle Component

```tsx
"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { setTheme, theme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
```

### Vite / React Router

```tsx
// No next-themes needed — toggle .dark class on <html>
function toggleDark() {
  document.documentElement.classList.toggle("dark");
}
```

## Custom Themes

### Editing Colors

Change the entire palette by editing CSS variables:

```css
:root {
  /* Blue theme */
  --primary: oklch(0.55 0.2 250);
  --primary-foreground: oklch(0.98 0 0);

  /* Warm accent */
  --accent: oklch(0.85 0.12 80);
  --accent-foreground: oklch(0.2 0 0);
}
```

### Custom Border Radius

```css
:root {
  --radius: 0.5rem;   /* Default: 0.625rem */
}
```

Components derive from this:
- `rounded-sm` → `calc(var(--radius) - 4px)`
- `rounded-md` → `calc(var(--radius) - 2px)`
- `rounded-lg` → `var(--radius)`
- `rounded-xl` → `calc(var(--radius) + 4px)`

### Adding Custom Tokens

Extend the token system for your project:

```css
:root {
  --success: oklch(0.6 0.2 145);
  --success-foreground: oklch(0.98 0.01 145);
  --warning: oklch(0.75 0.18 85);
  --warning-foreground: oklch(0.25 0.05 85);
}

@theme inline {
  --color-success: var(--success);
  --color-success-foreground: var(--success-foreground);
  --color-warning: var(--warning);
  --color-warning-foreground: var(--warning-foreground);
}
```

Now use `bg-success text-success-foreground` in Tailwind.

## Presets

Apply a complete design system configuration with a single command:

```bash
npx shadcn@latest apply --preset nova
```

A preset packages: colors, theme tokens, icon library, fonts, and radius into a short code. Preview presets at [shadcn/create](https://ui.shadcn.com/themes).

Presets modify your CSS variables — they don't replace components.

## Chart Colors

Charts use a separate set of color tokens for data series:

```css
:root {
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
}

.dark {
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
}
```

## Typography Tokens

Typography is handled via Tailwind utilities, not custom tokens. However, you can add font family tokens:

```css
@theme inline {
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

## Common Patterns

### Conditional Theming by Section

```tsx
<div className="dark">
  {/* Forces dark mode for this section regardless of global theme */}
  <Card className="bg-card text-card-foreground">
    <CardContent>Always dark</CardContent>
  </Card>
</div>
```

### Theme-Aware Images

```tsx
<img
  src="/logo-light.svg"
  className="block dark:hidden"
  alt="Logo"
/>
<img
  src="/logo-dark.svg"
  className="hidden dark:block"
  alt="Logo"
/>
```

### System Preference Detection

```css
@media (prefers-color-scheme: dark) {
  :root:not(.light) {
    --background: oklch(0.145 0 0);
    /* ... dark tokens */
  }
}
```

### Pitfalls

1. **Don't mix HSL and OKLCH** — pick one format and stick with it across all tokens.
2. **Test dark mode colors for contrast** — WCAG requires 4.5:1 for body text, 3:1 for large text.
3. **CSS variables can't be changed after init** — the `cssVariables: true/false` setting in `components.json` affects how components are generated. Switching requires re-adding all components.
