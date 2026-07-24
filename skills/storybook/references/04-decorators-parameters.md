# Storybook — Decorators & Parameters

> Source: https://storybook.js.org/docs/writing-stories/decorators | https://storybook.js.org/docs/writing-stories/parameters | v10.5.3

## Table of Contents

- [Decorators](#decorators)
- [Decorator Levels](#decorator-levels)
- [Context Object](#context-object)
- [Decorator Patterns](#decorator-patterns)
- [Decorator Execution Order](#decorator-execution-order)
- [Parameters](#parameters)
- [Parameter Levels](#parameter-levels)
- [Parameter Inheritance](#parameter-inheritance)
- [Tags](#tags)
- [Loaders](#loaders)

## Decorators

A decorator wraps a story in extra rendering functionality — layout, context providers, mocked data, or styling. They let you add functionality without modifying the component itself.

### Basic Decorator

```typescript
const meta = {
  component: Button,
  decorators: [
    (Story) => (
      <div style={{ margin: '3em' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Button>;
```

## Decorator Levels

### Story-Level

Apply to a single story:

```typescript
export const Primary: Story = {
  decorators: [
    (Story) => (
      <div style={{ padding: '2rem', background: '#f5f5f5' }}>
        <Story />
      </div>
    ),
  ],
};
```

### Component-Level

Apply to all stories in a file via the meta object:

```typescript
const meta = {
  component: Card,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: '400px' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Card>;
```

### Global-Level

Apply to every story in `.storybook/preview.ts`:

```typescript
const preview: Preview = {
  decorators: [
    (Story) => (
      <ThemeProvider theme="light">
        <Story />
      </ThemeProvider>
    ),
  ],
};

export default preview;
```

## Context Object

Decorators receive a second parameter with the story's context:

```typescript
const meta = {
  component: Button,
  decorators: [
    (Story, context) => {
      const { args, argTypes, globals, parameters, viewMode } = context;
      return (
        <div className={parameters.theme === 'dark' ? 'dark' : 'light'}>
          <Story />
        </div>
      );
    },
  ],
} satisfies Meta<typeof Button>;
```

### Context Properties

| Property | Type | Description |
|----------|------|-------------|
| `args` | object | Current story arguments |
| `argTypes` | object | Arg metadata and controls config |
| `globals` | object | Global values (toolbar selections) |
| `hooks` | object | Storybook API hooks (`useArgs`, `useGlobals`) |
| `parameters` | object | Static metadata for addons |
| `viewMode` | string | Current view (`'story'` or `'docs'`) |

## Decorator Patterns

### Theme Provider

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

### Router/Navigation Mock

```typescript
const meta = {
  component: ProfilePage,
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/profile/1']}>
        <Routes>
          <Route path="/profile/:id" element={<Story />} />
        </Routes>
      </MemoryRouter>
    ),
  ],
} satisfies Meta<typeof ProfilePage>;
```

### Redux/State Provider

```typescript
const meta = {
  component: TaskList,
  decorators: [
    (Story) => (
      <Provider store={createMockStore()}>
        <Story />
      </Provider>
    ),
  ],
} satisfies Meta<typeof TaskList>;
```

### Conditional Layout

```typescript
const preview: Preview = {
  decorators: [
    (Story, { parameters }) => {
      switch (parameters.pageLayout) {
        case 'page':
          return (
            <div className="page-layout">
              <Story />
            </div>
          );
        case 'page-mobile':
          return (
            <div className="page-mobile-layout">
              <Story />
            </div>
          );
        default:
          return <Story />;
      }
    },
  ],
};
```

### i18n Provider

```typescript
const preview: Preview = {
  decorators: [
    (Story, { globals }) => {
      const locale = globals.locale || 'en';
      return (
        <I18nProvider locale={locale}>
          <Story />
        </I18nProvider>
      );
    },
  ],
};
```

## Decorator Execution Order

Decorators execute in this order (outermost to innermost):

1. **Global decorators** — in definition order
2. **Component decorators** — in definition order
3. **Story decorators** — in definition order

The last decorator in the array wraps closest to the component.

## Parameters

Parameters are static, named metadata about a story. They configure addon behavior and are not editable by users at runtime (unlike args).

### Common Parameters

```typescript
const meta = {
  component: Button,
  parameters: {
    layout: 'centered',                    // 'centered' | 'fullscreen' | 'padded'
    backgrounds: {
      default: 'dark',
      options: {
        light: { name: 'Light', value: '#ffffff' },
        dark: { name: 'Dark', value: '#333333' },
      },
    },
    viewport: {
      defaultViewport: 'mobile1',
    },
    docs: {
      description: {
        component: 'A reusable button component',
      },
    },
    controls: {
      expanded: true,
      sort: 'requiredFirst',
    },
    actions: {
      disable: false,
    },
  },
} satisfies Meta<typeof Button>;
```

## Parameter Levels

### Story-Level

```typescript
export const OnDarkBackground: Story = {
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
};
```

### Component-Level

```typescript
const meta = {
  component: Button,
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof Button>;
```

### Global-Level

```typescript
// .storybook/preview.ts
const preview: Preview = {
  parameters: {
    layout: 'padded',
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
  },
};
```

## Parameter Inheritance

Parameters merge across levels — more specific parameters override less specific ones:

```
Global → Component → Story
```

Parameters are **merged**, not replaced. Story-level parameters override specific keys while keeping globally-defined settings for unspecified keys.

```typescript
// Global: { layout: 'padded', backgrounds: { default: 'light' } }
// Component: { layout: 'centered' }
// Story: { backgrounds: { default: 'dark' } }
// Effective: { layout: 'centered', backgrounds: { default: 'dark' } }
```

## Tags

Tags are string labels that control story behavior. They enable or disable features:

```typescript
// Enable autodocs for all stories in this file
const meta = {
  component: Button,
  tags: ['autodocs'],
} satisfies Meta<typeof Button>;

// Disable autodocs for a specific story
export const Internal: Story = {
  tags: ['!autodocs'],
};

// Exclude from test runner
export const DevOnly: Story = {
  tags: ['!test'],
};
```

### Global Tags

```typescript
// .storybook/preview.ts
const preview: Preview = {
  tags: ['autodocs'],
};
```

### Common Tags

| Tag | Effect |
|-----|--------|
| `autodocs` | Generate automatic docs page |
| `!autodocs` | Exclude from autodocs |
| `!test` | Exclude from test runner |
| `!dev` | Hide from development sidebar |

## Loaders

Loaders are async functions that fetch data before a story renders. The loaded data is available in the story's render context:

### Story-Level Loader

```typescript
export const WithApiData: Story = {
  loaders: [
    async () => ({
      todo: await (
        await fetch('https://jsonplaceholder.typicode.com/todos/1')
      ).json(),
    }),
  ],
  render: (args, { loaded: { todo } }) => (
    <TodoItem {...args} {...todo} />
  ),
};
```

### Global Loader

```typescript
// .storybook/preview.ts
const preview: Preview = {
  loaders: [
    async () => ({
      currentUser: await (
        await fetch('https://api.example.com/me')
      ).json(),
    }),
  ],
};
```

### Loader Execution

- All loaders run in **parallel**
- Results merge into the `loaded` context field
- Precedence: global < component < story (story loaders override)

### Loaders vs Args

Use **args** for simple, serializable component inputs. Use **loaders** when you need to fetch data asynchronously before rendering.

## Common Pitfalls

1. **Decorator state leaking** — Each story should be independent; use `beforeEach` for cleanup
2. **Parameter deep merge confusion** — Nested objects merge, they don't replace
3. **Global decorators order** — Later decorators wrap closer to the component
4. **Loader data not available in args** — Access loaded data via `context.loaded`, not `args`

## Related Topics

- [Writing Stories](02-writing-stories.md) — Story format basics
- [Args & Controls](03-args-controls.md) — Interactive arg manipulation
- [Configuration](10-configuration.md) — Preview and global configuration
