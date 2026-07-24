# Storybook — Documentation

> Source: https://storybook.js.org/docs/writing-docs/autodocs | https://storybook.js.org/docs/writing-docs/mdx | v10.5.3

## Table of Contents

- [Autodocs](#autodocs)
- [Enabling Autodocs](#enabling-autodocs)
- [Custom Templates](#custom-templates)
- [MDX Documentation](#mdx-documentation)
- [Doc Blocks](#doc-blocks)
- [Table of Contents](#table-of-contents)
- [Subcomponents](#subcomponents)
- [Theme Customization](#theme-customization)

## Autodocs

Autodocs is Storybook's automatic documentation generation. It infers component metadata (args, argTypes, parameters) and generates a documentation page at the root of each component's story hierarchy. The generated page includes a component description, an interactive preview of the primary story, and an arg table with controls.

## Enabling Autodocs

### Globally (All Components)

```typescript
// .storybook/preview.ts
const preview: Preview = {
  tags: ['autodocs'],
};

export default preview;
```

### Per Component

```typescript
const meta = {
  component: Button,
  tags: ['autodocs'],
} satisfies Meta<typeof Button>;
```

### Excluding Specific Components

```typescript
const meta = {
  component: InternalWidget,
  tags: ['!autodocs'],
} satisfies Meta<typeof InternalWidget>;
```

### Configuration in main.ts

```typescript
// .storybook/main.ts
const config: StorybookConfig = {
  docs: {
    defaultName: 'Docs',    // Name of the docs page in sidebar
    docsMode: false,          // true = docs-only, hides story pages
  },
};
```

## Custom Templates

### JSX Template

Replace the default doc page layout:

```typescript
// .storybook/preview.ts
import {
  Title,
  Subtitle,
  Description,
  Primary,
  Controls,
  Stories,
} from '@storybook/blocks';

const preview: Preview = {
  parameters: {
    docs: {
      page: () => (
        <>
          <Title />
          <Subtitle />
          <Description />
          <Primary />
          <Controls />
          <Stories />
        </>
      ),
    },
  },
};
```

### MDX Template

Create a reusable MDX template:

```mdx
{/* .storybook/DocumentationTemplate.mdx */}
import { Meta, Title, Primary, Controls, Stories } from '@storybook/blocks';

<Meta isTemplate />

<Title />

## Overview

<Primary />

## Props

<Controls />

## Examples

<Stories />
```

Reference it in preview configuration:

```typescript
import DocumentationTemplate from './DocumentationTemplate.mdx';

const preview: Preview = {
  parameters: {
    docs: {
      page: DocumentationTemplate,
    },
  },
};
```

### Per-Component Template Override

```typescript
const meta = {
  component: Button,
  tags: ['autodocs'],
  parameters: {
    docs: {
      page: () => (
        <>
          <Title />
          <Description />
          <Primary />
          <Controls />
        </>
      ),
    },
  },
} satisfies Meta<typeof Button>;
```

## MDX Documentation

MDX combines Markdown and JSX for custom documentation pages. Create `.mdx` files alongside stories or as standalone guides.

### Attached MDX (Component Docs)

```mdx
{/* Button.mdx */}
import { Meta, Story, Canvas, Controls } from '@storybook/blocks';
import * as ButtonStories from './Button.stories';

<Meta of={ButtonStories} />

# Button

A versatile button component used across the design system.

## Usage Guidelines

- Use **Primary** for main calls to action
- Use **Secondary** for less prominent actions
- Always include an accessible label

## Interactive Demo

<Canvas of={ButtonStories.Primary} />

## Props

<Controls of={ButtonStories.Primary} />

## All Variants

<Canvas>
  <Story of={ButtonStories.Primary} />
  <Story of={ButtonStories.Secondary} />
  <Story of={ButtonStories.Outline} />
</Canvas>
```

### Unattached MDX (Standalone Pages)

```mdx
{/* Introduction.mdx */}
import { Meta } from '@storybook/blocks';

<Meta title="Design System/Introduction" />

# Design System

Welcome to our component library documentation.

## Getting Started

Install the package:

```bash
npm install @myorg/components
```

## Principles

1. **Consistency** — Use components from this library
2. **Accessibility** — All components meet WCAG 2.1 AA
3. **Performance** — Tree-shakeable, zero runtime overhead
```

## Doc Blocks

Doc blocks are pre-built components for documentation pages:

### Available Blocks

| Block | Purpose |
|-------|---------|
| `<Title />` | Component name |
| `<Subtitle />` | Secondary heading |
| `<Description />` | Component description from source |
| `<Primary />` | First story with zoom controls |
| `<Controls />` | Interactive arg table |
| `<Stories />` | All remaining stories |
| `<Canvas />` | Story preview with source panel |
| `<Story />` | Single story inline |
| `<Source />` | Code snippet |
| `<ArgTypes />` | Read-only arg table |
| `<Meta />` | Attach MDX to a component |
| `<Markdown />` | Render markdown strings |
| `<Unstyled />` | Remove doc styling wrapper |

### Canvas Block

```mdx
import { Canvas } from '@storybook/blocks';
import * as ButtonStories from './Button.stories';

{/* With source code panel */}
<Canvas of={ButtonStories.Primary} />

{/* Without source panel */}
<Canvas of={ButtonStories.Primary} sourceState="hidden" />

{/* Multiple stories in one canvas */}
<Canvas>
  <Story of={ButtonStories.Small} />
  <Story of={ButtonStories.Medium} />
  <Story of={ButtonStories.Large} />
</Canvas>
```

### Source Block

```mdx
import { Source } from '@storybook/blocks';

<Source code={`
import { Button } from '@myorg/components';

<Button variant="primary" onClick={() => {}}>
  Click me
</Button>
`} language="tsx" />
```

### Controls Block

```mdx
import { Controls } from '@storybook/blocks';
import * as ButtonStories from './Button.stories';

{/* Controls for a specific story */}
<Controls of={ButtonStories.Primary} />

{/* Controls with specific columns */}
<Controls include={['label', 'variant', 'size']} />
```

## Table of Contents

### Enable Globally

```typescript
const preview: Preview = {
  parameters: {
    docs: {
      toc: true,
    },
  },
};
```

### Configuration Options

| Option | Description |
|--------|-------------|
| `contentsSelector` | CSS selector for heading container |
| `disable` | Hide TOC (boolean) |
| `headingSelector` | Which headings to include (`'h1, h2, h3'`) |
| `ignoreSelector` | Headings to exclude |
| `title` | Custom TOC caption |

### Per-Component Override

```typescript
const meta = {
  component: SimpleButton,
  parameters: {
    docs: {
      toc: { disable: true },
    },
  },
} satisfies Meta<typeof SimpleButton>;
```

## Subcomponents

Document related components together using `subcomponents`:

```typescript
const meta = {
  component: List,
  subcomponents: { ListItem, ListHeader },
  tags: ['autodocs'],
} satisfies Meta<typeof List>;
```

This creates tabbed views in the ArgTypes doc block — each tab showing the props for a different subcomponent.

## Theme Customization

### Apply Theme to Docs

```typescript
import { themes, ensure } from 'storybook/theming';

const preview: Preview = {
  parameters: {
    docs: {
      theme: ensure(themes.dark),
    },
  },
};
```

### Custom Docs Container

```typescript
import { DocsContainer } from '@storybook/blocks';

const CustomContainer = ({ children, ...props }) => (
  <DocsContainer {...props}>
    <div className="custom-docs-wrapper">
      {children}
    </div>
  </DocsContainer>
);

const preview: Preview = {
  parameters: {
    docs: {
      container: CustomContainer,
    },
  },
};
```

### Override MDX Components

```typescript
import { MDXProvider } from '@mdx-js/react';
import { DocsContainer } from '@storybook/blocks';
import * as DesignSystem from './design-system';

const CustomDocsContainer = (props) => (
  <MDXProvider
    components={{
      h1: DesignSystem.H1,
      h2: DesignSystem.H2,
      code: DesignSystem.Code,
    }}
  >
    <DocsContainer {...props} />
  </MDXProvider>
);
```

Component replacement only affects Markdown syntax (`#`). Native HTML elements (`<h1>`) are not replaced.

## Common Pitfalls

1. **Autodocs not generating** — Ensure `tags: ['autodocs']` is set
2. **Monorepo imports** — Import from source paths, not package root
3. **MDX not rendering** — Check that `@storybook/addon-docs` is in addons
4. **TOC not visible** — Requires more than one heading; hides below 1200px width

## Related Topics

- [Writing Stories](02-writing-stories.md) — Story format and structure
- [Addons Ecosystem](09-addons-ecosystem.md) — Docs addon configuration
- [Configuration](10-configuration.md) — Main and preview setup
