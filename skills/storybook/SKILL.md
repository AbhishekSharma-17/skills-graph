---
name: storybook
description: "Industry-standard UI component workshop for building, documenting, and testing components in isolation. MANDATORY TRIGGERS: storybook, stories, CSF, component story format, story file, addon, chromatic. Also trigger when the user wants to develop UI components in isolation, write component documentation, set up visual testing, create interaction tests with play functions, configure component controls, or build a design system catalog. When in doubt about whether to use this skill for component development or UI testing tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["storybook", "components", "testing", "documentation", "ui", "frontend", "react", "vue", "angular"]
---

# Storybook

> v10.5.3 | https://storybook.js.org/docs | https://github.com/storybookjs/storybook

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with Storybook, comparing component dev tools, understanding the ecosystem |
| [01-installation-setup.md](references/01-installation-setup.md) | Installing Storybook, configuring frameworks, main.ts/preview.ts setup |
| [02-writing-stories.md](references/02-writing-stories.md) | CSF format, meta objects, story exports, render functions, naming conventions |
| [03-args-controls.md](references/03-args-controls.md) | Args system, Controls addon, argTypes, control types, conditional controls |
| [04-decorators-parameters.md](references/04-decorators-parameters.md) | Wrapping stories, providing context, static metadata, parameter inheritance |
| [05-play-functions.md](references/05-play-functions.md) | Interaction scripting, user event simulation, canvas queries, composing stories |
| [06-interaction-testing.md](references/06-interaction-testing.md) | Component testing with play functions, assertions, spying, mount, lifecycle hooks |
| [07-visual-a11y-testing.md](references/07-visual-a11y-testing.md) | Chromatic visual testing, accessibility addon, axe-core, WCAG compliance |
| [08-documentation.md](references/08-documentation.md) | Autodocs, MDX, doc blocks, custom templates, table of contents |
| [09-addons-ecosystem.md](references/09-addons-ecosystem.md) | Essential addons, viewport, backgrounds, writing custom addons, addon API |
| [10-configuration.md](references/10-configuration.md) | main.ts, preview.ts, manager.ts, builders, styling, environment variables |
| [11-sharing-publishing.md](references/11-sharing-publishing.md) | Building static Storybook, Chromatic deployment, CI/CD, composition |
| [12-ai-integration.md](references/12-ai-integration.md) | MCP server, agentic setup, manifests, AI-assisted component development |

## Installation

```bash
npm create storybook@latest
# or for a specific version
npm create storybook@10.5
```

## Quick Reference

- [Official Docs](https://storybook.js.org/docs)
- [GitHub Repository](https://github.com/storybookjs/storybook)
- [npm Package](https://www.npmjs.com/package/storybook)
- [Addon Catalog](https://storybook.js.org/addons)
