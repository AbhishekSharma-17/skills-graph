# Storybook — Args & Controls

> Source: https://storybook.js.org/docs/writing-stories/args | https://storybook.js.org/docs/essentials/controls | v10.5.3

## Table of Contents

- [Args System](#args-system)
- [Controls Addon](#controls-addon)
- [Control Types Reference](#control-types-reference)
- [ArgTypes Configuration](#argtypes-configuration)
- [Control Type Matchers](#control-type-matchers)
- [Complex Value Mapping](#complex-value-mapping)
- [Conditional Controls](#conditional-controls)
- [URL-Based Args](#url-based-args)
- [Panel Configuration](#panel-configuration)
- [Disabling Controls](#disabling-controls)

## Args System

Args are Storybook's mechanism for defining component arguments. They can dynamically change props, slots, styles, and inputs. When an arg value changes, the component re-renders live.

### Levels of Args

Args cascade from global to story level, with more specific values winning:

```typescript
// Global — .storybook/preview.ts
const preview: Preview = {
  args: { theme: 'light' },
};

// Component — meta default export
const meta = {
  component: Button,
  args: { primary: true },
} satisfies Meta<typeof Button>;

// Story — individual export
export const Primary: Story = {
  args: { label: 'Click me' },
};
// Effective args: { theme: 'light', primary: true, label: 'Click me' }
```

### Args Composition

Reuse args from other stories to reduce duplication:

```typescript
export const Primary: Story = {
  args: { primary: true, label: 'Button', size: 'medium' },
};

export const PrimarySmall: Story = {
  args: {
    ...Primary.args,
    size: 'small',
  },
};
```

### Cross-File Composition

Import args from child component stories for page compositions:

```typescript
import * as HeaderStories from './Header.stories';
import * as FooterStories from './Footer.stories';

export const FullPage: Story = {
  args: {
    header: HeaderStories.LoggedIn.args,
    footer: FooterStories.Default.args,
  },
};
```

## Controls Addon

The Controls addon auto-generates an interactive UI for manipulating args. It infers control types from component prop types and arg values.

### Automatic Inference

When you define a `component` in meta, Storybook analyzes its prop types and generates controls automatically:

```typescript
// Button has: primary: boolean, label: string, size: 'sm' | 'md' | 'lg'
const meta = {
  component: Button,
} satisfies Meta<typeof Button>;

// Controls panel auto-generates:
// - Toggle for `primary`
// - Text input for `label`
// - Select dropdown for `size`
```

## Control Types Reference

| Data Type | Control | Description |
|-----------|---------|-------------|
| `boolean` | `boolean` | Toggle switch |
| `number` | `number` | Numeric input with optional min/max/step |
| `number` | `range` | Slider |
| `object` | `object` | JSON editor for objects/arrays |
| `file` | `file` | File input returning URLs |
| `enum` | `radio` | Radio button group |
| `enum` | `inline-radio` | Inline radio buttons |
| `enum` | `check` | Multi-select checkboxes |
| `enum` | `inline-check` | Inline checkboxes |
| `enum` | `select` | Dropdown single select |
| `enum` | `multi-select` | Dropdown multi select |
| `string` | `text` | Text input |
| `string` | `color` | Color picker with presets |
| `string` | `date` | Date picker (returns UNIX timestamp) |

### Control Configuration Examples

```typescript
const meta = {
  component: Widget,
  argTypes: {
    // Boolean toggle
    isActive: { control: 'boolean' },

    // Number with constraints
    width: {
      control: { type: 'number', min: 100, max: 1200, step: 50 },
    },

    // Range slider
    opacity: {
      control: { type: 'range', min: 0, max: 1, step: 0.1 },
    },

    // File upload (images only)
    avatar: {
      control: { type: 'file', accept: '.png,.jpg,.jpeg' },
    },

    // Radio buttons
    variant: {
      control: 'radio',
      options: ['primary', 'secondary', 'ghost'],
    },

    // Select dropdown
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
    },

    // Color picker with presets
    backgroundColor: {
      control: {
        type: 'color',
        presetColors: [
          { color: '#ff4785', title: 'Coral' },
          { color: '#1ea7fd', title: 'Blue' },
          '#333333',
        ],
      },
    },
  },
} satisfies Meta<typeof Widget>;
```

## ArgTypes Configuration

ArgTypes define metadata about each arg — description, default value, table display, and control behavior:

```typescript
const meta = {
  component: Button,
  argTypes: {
    variant: {
      description: 'The visual style of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'primary' },
        category: 'Appearance',
      },
      options: ['primary', 'secondary', 'ghost'],
      control: { type: 'select' },
    },
    onClick: {
      description: 'Click handler',
      table: { category: 'Events' },
      action: 'clicked',
    },
  },
} satisfies Meta<typeof Button>;
```

### Table Categories

Group args into categories in the Controls panel:

```typescript
argTypes: {
  label:   { table: { category: 'Content' } },
  variant: { table: { category: 'Appearance' } },
  size:    { table: { category: 'Appearance' } },
  onClick: { table: { category: 'Events' } },
}
```

## Control Type Matchers

Auto-infer control types from arg names using regex patterns in `.storybook/preview.ts`:

```typescript
const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,    // Color picker
        date: /Date$/,                     // Date picker
      },
    },
  },
};
```

Any arg name ending in `color` or `background` gets a color picker. Any arg ending in `Date` gets a date picker.

## Complex Value Mapping

Map simple serializable values to complex types (JSX, objects, functions):

```typescript
const meta = {
  component: IconButton,
  argTypes: {
    icon: {
      options: ['arrow-up', 'arrow-down', 'check', 'close'],
      mapping: {
        'arrow-up': <ArrowUpIcon />,
        'arrow-down': <ArrowDownIcon />,
        'check': <CheckIcon />,
        'close': <CloseIcon />,
      },
      control: {
        type: 'select',
        labels: {
          'arrow-up': 'Arrow Up',
          'arrow-down': 'Arrow Down',
          'check': 'Checkmark',
          'close': 'Close',
        },
      },
    },
  },
} satisfies Meta<typeof IconButton>;
```

Mapping does not have to be exhaustive — unmapped values pass through directly.

## Conditional Controls

Show or hide controls based on other control values:

```typescript
const meta = {
  component: Button,
  argTypes: {
    label: { control: 'text' },
    advanced: { control: 'boolean' },
    // Only visible when `advanced` is true
    margin: { control: 'number', if: { arg: 'advanced' } },
    padding: { control: 'number', if: { arg: 'advanced' } },
  },
} satisfies Meta<typeof Button>;
```

### Conditional Operators

| Operator | Check |
|----------|-------|
| `truthy` | Is value truthy? (default) |
| `exists` | Is value defined? |
| `eq` | Value equals given value |
| `neq` | Value does not equal given value |

### Mutually Exclusive Controls

```typescript
argTypes: {
  label: {
    control: 'text',
    if: { arg: 'image', truthy: false },
  },
  image: {
    control: { type: 'select', options: ['hero.jpg', 'thumb.jpg'] },
    if: { arg: 'label', truthy: false },
  },
}
```

### Global-Based Conditionals

```typescript
argTypes: {
  advancedSetting: {
    if: { global: 'theme', eq: 'dark' },
  },
}
```

## URL-Based Args

Override initial args via URL query parameters:

```
?path=/story/button--primary&args=label:Hello;primary:true;size:large
```

Supported value formats:
- Strings: `label:Hello`
- Numbers: `size:42`
- Booleans: `primary:true`
- Null: `value:!null`
- Undefined: `value:!undefined`
- Dates: `start:!date(2024-01-01)`
- Colors: `bg:!hex(ff4785)`, `bg:!rgba(255,71,133,1)`
- Objects: `style.width:100`
- Arrays: `items[0]:first;items[1]:second`

## Panel Configuration

### Expanded Documentation

Show full type info and description:

```typescript
parameters: {
  controls: { expanded: true },
}
```

### Filtering Controls

```typescript
// Include only specific controls
export const Minimal: Story = {
  parameters: {
    controls: { include: ['label', 'variant'] },
  },
};

// Exclude controls by regex
export const Simplified: Story = {
  parameters: {
    controls: { exclude: /^on[A-Z]/ },
  },
};
```

### Sorting Controls

```typescript
const meta = {
  component: Button,
  parameters: {
    controls: { sort: 'requiredFirst' },  // 'none' | 'alpha' | 'requiredFirst'
  },
} satisfies Meta<typeof Button>;
```

### Preset Color Swatches

```typescript
parameters: {
  controls: {
    presetColors: [
      { color: '#ff4785', title: 'Storybook Coral' },
      { color: '#1ea7fd', title: 'Storybook Blue' },
      'rgba(0, 159, 183, 1)',
    ],
  },
}
```

## Disabling Controls

```typescript
// Hide control AND documentation row
argTypes: {
  internalProp: { table: { disable: true } },
}

// Hide control only, keep documentation
argTypes: {
  readOnlyProp: { control: false },
}

// Disable save-from-UI (prevent story creation from Controls)
parameters: {
  controls: { disableSaveFromUI: true },
}
```

## Common Pitfalls

1. **Controls not appearing** — Ensure `component` is set in meta and props are typed
2. **Controls not updating story** — Happens when inline rendering is disabled
3. **Complex objects not editable** — Use the JSON editor control type or mapping
4. **Missing color/date matchers** — Add matchers to preview.ts parameters

## Related Topics

- [Writing Stories](02-writing-stories.md) — Story format and args basics
- [Decorators & Parameters](04-decorators-parameters.md) — Static metadata configuration
- [Configuration](10-configuration.md) — Preview and main configuration
