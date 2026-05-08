---
name: shadcn-ui
description: "shadcn/ui component system with CLI, Radix/Base UI primitives, Tailwind v4, theming, forms, data tables, charts, blocks, and custom registries. MANDATORY TRIGGERS: shadcn, shadcn/ui, shadcn-ui, shadcn ui, radix ui components. Also trigger when user wants to add accessible React components with Tailwind styling, build design systems with copy-paste components, create dashboards with charts and data tables, set up form validation with React Hook Form and Zod, or distribute components via custom registries. When in doubt about whether to use this skill for React UI component tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["shadcn-ui", "react", "components", "tailwind", "radix-ui", "design-system", "forms", "charts", "accessibility"]
---

# shadcn/ui — Skill Router

> Beautifully-designed, accessible components and a code distribution platform. Open source. Open code.

**Source:** [ui.shadcn.com](https://ui.shadcn.com) | **Package:** `shadcn` v4.7.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, philosophy, quickstart |
| **CLI Commands** | `references/01-cli.md` | init, add, build, search, view, info, docs, registry commands |
| **Configuration** | `references/02-configuration.md` | components.json, Tailwind v4, project settings |
| **Theming** | `references/03-theming.md` | CSS variables, OKLCH colors, dark mode, presets |
| **Layout Components** | `references/04-layout-components.md` | Card, Sidebar, Scroll Area, Resizable, Separator |
| **Form Components** | `references/05-form-components.md` | Input, Select, Checkbox, Radio, Switch, Textarea, OTP |
| **Form Validation** | `references/06-form-validation.md` | React Hook Form + Zod, FormField, error handling |
| **Feedback & Overlays** | `references/07-feedback-overlays.md` | Dialog, Sheet, Drawer, Toast, Sonner, Popover, Tooltip |
| **Navigation** | `references/08-navigation-components.md` | Tabs, Accordion, Nav Menu, Breadcrumb, Command, Pagination |
| **Data Display** | `references/09-data-display.md` | Table, Data Table, Badge, Avatar, Skeleton, Progress |
| **Charts** | `references/10-charts.md` | Recharts v3, area, bar, line, pie, radar, tooltips |
| **Registry & Blocks** | `references/11-registry.md` | Custom registries, blocks, distribution, design systems |
| **Accessibility** | `references/12-accessibility.md` | ARIA patterns, keyboard navigation, screen readers |

## Installation

```bash
# Initialize in existing project
npx shadcn@latest init

# Add components
npx shadcn@latest add button card dialog

# Add from URL or registry
npx shadcn@latest add https://example.com/r/my-component.json
```

## Quick Reference

- **Docs:** https://ui.shadcn.com/docs
- **GitHub:** https://github.com/shadcn-ui/ui
- **npm:** https://www.npmjs.com/package/shadcn
- **Blocks:** https://ui.shadcn.com/blocks
- **Charts:** https://ui.shadcn.com/charts
- **Registry:** https://ui.shadcn.com/docs/registry
