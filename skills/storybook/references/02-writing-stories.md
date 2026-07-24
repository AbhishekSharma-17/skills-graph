# Storybook — Writing Stories

> Source: https://storybook.js.org/docs/writing-stories | v10.5.3

## Table of Contents

- [Component Story Format](#component-story-format)
- [Meta Object](#meta-object)
- [Defining Stories](#defining-stories)
- [Args](#args)
- [Render Functions](#render-functions)
- [Using Hooks](#using-hooks)
- [Story Naming](#story-naming)
- [Composite Components](#composite-components)
- [File Organization](#file-organization)
- [TypeScript Patterns](#typescript-patterns)

## Component Story Format

Stories use the Component Story Format (CSF), an ES module standard. Each story file has:

- **One default export** — metadata (the `meta` object)
- **One or more named exports** — individual stories

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta = {
  component: Button,
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    primary: true,
    label: 'Button',
  },
};
```

The default export must contain either a `title` property (explicit hierarchy) or a `component` property (auto-generated title from file path).

## Meta Object

The meta object configures all stories in the file:

```typescript
const meta = {
  component: Button,
  title: 'Design System/Button',      // Explicit sidebar hierarchy
  tags: ['autodocs'],                  // Enable auto-documentation
  args: {                              // Default args for all stories
    size: 'medium',
  },
  argTypes: {                          // Control configuration
    variant: {
      options: ['primary', 'secondary'],
      control: { type: 'radio' },
    },
  },
  parameters: {                        // Addon configuration
    layout: 'centered',
  },
  decorators: [                        // Wrapper components
    (Story) => (
      <div style={{ margin: '3em' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Button>;
```

### Meta Properties

| Property | Purpose |
|----------|---------|
| `component` | The component being documented |
| `title` | Sidebar hierarchy path (auto-generated if omitted) |
| `tags` | Story tags (`autodocs`, `!autodocs`, `!test`) |
| `args` | Default args for all stories in this file |
| `argTypes` | Arg metadata and control configuration |
| `parameters` | Static metadata for addons |
| `decorators` | Wrapper functions for all stories |
| `loaders` | Async data loading before rendering |
| `render` | Default render function for all stories |
| `subcomponents` | Related components for docs |
| `beforeEach` | Setup function before each story renders |

## Defining Stories

Stories are named exports using UpperCamelCase:

```typescript
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    primary: true,
    label: 'Button',
  },
};

export const Secondary: Story = {
  args: {
    primary: false,
    label: 'Button',
  },
};

export const Large: Story = {
  args: {
    size: 'large',
    label: 'Button',
  },
};
```

### Reusing Args Across Stories

Spread args from other stories to avoid repetition:

```typescript
export const Primary: Story = {
  args: {
    primary: true,
    label: 'Button',
  },
};

export const PrimaryLongLabel: Story = {
  args: {
    ...Primary.args,
    label: 'Button with a really long label text',
  },
};

export const Secondary: Story = {
  args: {
    ...Primary.args,
    primary: false,
  },
};
```

## Args

Args represent component inputs. They work across all frameworks (React props, Vue props, Angular @Input):

### Story-Level Args

```typescript
export const Primary: Story = {
  args: {
    primary: true,
    label: 'Click me',
    onClick: fn(),
  },
};
```

### Component-Level Args

Applied to all stories via the meta object:

```typescript
const meta = {
  component: Button,
  args: {
    primary: true,
  },
} satisfies Meta<typeof Button>;
```

### Global Args

In `.storybook/preview.ts`, applied to every story:

```typescript
const preview: Preview = {
  args: { theme: 'light' },
};
```

### Args Composition from Other Files

Import and reuse child component args for page-level stories:

```typescript
import * as HeaderStories from './Header.stories';

const meta = { component: Page } satisfies Meta<typeof Page>;
export default meta;

export const LoggedIn: Story = {
  args: {
    ...HeaderStories.LoggedIn.args,
  },
};
```

### Dynamic Args with useArgs

```typescript
import { useArgs } from 'storybook/preview-api';

export const Controlled: Story = {
  args: { isChecked: false, label: 'Toggle' },
  render: function Render(args) {
    const [{ isChecked }, updateArgs] = useArgs();
    function onChange() {
      updateArgs({ isChecked: !isChecked });
    }
    return <Checkbox {...args} onChange={onChange} isChecked={isChecked} />;
  },
};
```

**Important**: Do not mix Storybook hooks (`useArgs`) with React hooks (`useState`).

## Render Functions

Override the default rendering when you need custom markup:

### Story-Level Render

```typescript
export const InAlert: Story = {
  args: { primary: true, label: 'Button' },
  render: (args) => (
    <Alert>
      Alert text
      <Button {...args} />
    </Alert>
  ),
};
```

Always spread `args` onto the component so Controls continue to work.

### Meta-Level Render

Set a default render for all stories in the file:

```typescript
const meta = {
  component: Button,
  render: (args) => (
    <div className="button-wrapper">
      <Button {...args} />
    </div>
  ),
} satisfies Meta<typeof Button>;
```

### Context in Render Functions

Render functions receive a second `context` argument:

```typescript
export const WithContext: Story = {
  render: (args, { parameters, globals }) => {
    const theme = globals.theme || 'light';
    return (
      <ThemeProvider theme={theme}>
        <Button {...args} />
      </ThemeProvider>
    );
  },
};
```

## Using Hooks

React hooks work in render functions but are considered advanced:

```typescript
const ButtonWithState = () => {
  const [count, setCount] = useState(0);
  return (
    <Button
      label={`Clicked ${count} times`}
      onClick={() => setCount(count + 1)}
    />
  );
};

export const WithState: Story = {
  render: () => <ButtonWithState />,
};
```

Prefer args over hooks when possible — args integrate with Controls, Actions, and other addons.

## Story Naming

### Default Naming

Story names derive from the export name, converted from UpperCamelCase:

```typescript
export const PrimaryButton: Story = {};   // "Primary Button"
export const LargeWithIcon: Story = {};    // "Large With Icon"
```

### Custom Names

```typescript
export const Primary: Story = {
  name: 'Primary (Recommended)',
  args: { primary: true, label: 'Button' },
};
```

### Hierarchy with Titles

Organize stories using `/` in the meta title:

```typescript
const meta = {
  title: 'Design System/Atoms/Button',
  component: Button,
} satisfies Meta<typeof Button>;
```

Or let Storybook auto-generate from file paths.

## Composite Components

### Multi-Component Stories

```typescript
import { List } from './List';
import { ListItem } from './ListItem';
import * as ListItemStories from './ListItem.stories';

const meta = {
  component: List,
  subcomponents: { ListItem },
} satisfies Meta<typeof List>;

export default meta;

export const Default: Story = {
  render: (args) => (
    <List {...args}>
      <ListItem {...ListItemStories.Selected.args} />
      <ListItem {...ListItemStories.Default.args} />
      <ListItem {...ListItemStories.Default.args} />
    </List>
  ),
};
```

## File Organization

Colocate story files with their components:

```
src/
└── components/
    ├── Button/
    │   ├── Button.tsx
    │   ├── Button.stories.tsx
    │   ├── Button.test.tsx
    │   └── Button.css
    └── Card/
        ├── Card.tsx
        └── Card.stories.tsx
```

Story files are development-only and excluded from production bundles.

## TypeScript Patterns

### Basic Setup

```typescript
import type { Meta, StoryObj } from '@storybook/react';

const meta = {
  component: Button,
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;
```

The `satisfies` keyword provides type checking without widening the type — `StoryObj<typeof meta>` infers the correct arg types.

### With Explicit Args

```typescript
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    primary: true,     // Type-checked against Button props
    label: 'Button',   // Autocomplete available
  },
};
```

### Framework-Specific Types

Replace `@storybook/react` with your framework:

```typescript
import type { Meta, StoryObj } from '@storybook/vue3';
import type { Meta, StoryObj } from '@storybook/angular';
import type { Meta, StoryObj } from '@storybook/svelte';
import type { Meta, StoryObj } from '@storybook/web-components';
```

## Common Pitfalls

1. **Missing default export** — CSF requires exactly one default export
2. **Non-UpperCamelCase exports** — Story exports must use PascalCase
3. **Not spreading args in render** — Controls won't work without `{...args}`
4. **Mixing Storybook/React hooks** — Don't use `useState` alongside `useArgs`
5. **Circular imports** — Importing story args from sibling files can create cycles

## Related Topics

- [Args & Controls](03-args-controls.md) — Deep dive into the args system
- [Decorators & Parameters](04-decorators-parameters.md) — Wrapping and configuring stories
- [Play Functions](05-play-functions.md) — Adding interactions to stories
