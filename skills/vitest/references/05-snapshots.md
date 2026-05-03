# Snapshot Testing

> Source: [vitest.dev/guide/snapshot](https://vitest.dev/guide/snapshot.html) | Version: 4.x

## Table of Contents

- [What Are Snapshots](#what-are-snapshots)
- [File Snapshots](#file-snapshots)
- [Inline Snapshots](#inline-snapshots)
- [Custom File Snapshots](#custom-file-snapshots)
- [Updating Snapshots](#updating-snapshots)
- [Error Snapshots](#error-snapshots)
- [ARIA Snapshots](#aria-snapshots)
- [Custom Serializers](#custom-serializers)
- [Custom Snapshot Matchers](#custom-snapshot-matchers)
- [Configuration](#configuration)
- [Best Practices](#best-practices)

---

## What Are Snapshots

Snapshot testing captures a serialized value and compares it against a stored reference on subsequent runs. If the output changes, the test fails, prompting review.

```typescript
import { expect, test } from 'vitest'

test('renders correctly', () => {
  const result = render({ name: 'Alice', role: 'admin' })
  expect(result).toMatchSnapshot()
})
```

First run creates a `.snap` file in `__snapshots__/`. Subsequent runs compare against it.

## File Snapshots

### toMatchSnapshot()

Stores snapshots in a companion `.snap` file:

```typescript
test('serializes user object', () => {
  const user = { name: 'Alice', age: 30, email: 'alice@test.com' }
  expect(user).toMatchSnapshot()
})
```

Generated snapshot file (`__snapshots__/example.test.ts.snap`):

```
exports['serializes user object 1'] = `
{
  "age": 30,
  "email": "alice@test.com",
  "name": "Alice",
}
`;
```

### With Shape Hint

Provide expected shape while still snapshot-testing dynamic values:

```typescript
test('user has required fields', () => {
  const user = getUser()
  expect(user).toMatchSnapshot({
    id: expect.any(Number),
    createdAt: expect.any(Date),
    name: 'Alice',
  })
})
```

## Inline Snapshots

### toMatchInlineSnapshot()

Store snapshots directly in the test file:

```typescript
test('uppercase conversion', () => {
  expect(toUpperCase('hello')).toMatchInlineSnapshot('"HELLO"')
})
```

On first run (or update), Vitest writes the snapshot string as the argument:

```typescript
// Before first run:
expect(result).toMatchInlineSnapshot()

// After first run, Vitest modifies the file:
expect(result).toMatchInlineSnapshot(`
  {
    "name": "Alice",
    "status": "active",
  }
`)
```

### When to Use Inline vs File

| Use Inline | Use File |
|-----------|----------|
| Small, readable values | Large objects or deeply nested structures |
| Quick visual feedback in test file | Multiple snapshots per test |
| Component render output | Generated HTML/JSON |

## Custom File Snapshots

### toMatchFileSnapshot()

Store snapshots in an explicit file with any extension:

```typescript
test('render HTML', async () => {
  const html = renderComponent()
  await expect(html).toMatchFileSnapshot('./snapshots/component.html')
})
```

Benefits:
- Custom file extensions for syntax highlighting
- Easier review in PRs (real `.html`, `.json`, `.css` files)
- Explicit file paths for organization

## Updating Snapshots

### In Watch Mode

Press `u` in the terminal to update all failing snapshots.

### Via CLI

```bash
# Update all snapshots
npx vitest -u

# Update only new snapshots (skip existing)
npx vitest --update new

# Explicit modes
npx vitest --update all    # update all
npx vitest --update none   # never update (CI default)
```

### CI Behavior

Vitest skips snapshot updates in CI by default. To explicitly prevent updates:

```typescript
export default defineConfig({
  test: {
    snapshotOptions: {
      updateSnapshot: 'none',
    },
  },
})
```

## Error Snapshots

### toThrowErrorMatchingSnapshot()

Snapshot the error message from a thrown error:

```typescript
test('throws descriptive error', () => {
  expect(() => {
    validateInput(null)
  }).toThrowErrorMatchingSnapshot()
})
```

### toThrowErrorMatchingInlineSnapshot()

```typescript
test('throws validation error', () => {
  expect(() => {
    validateInput(null)
  }).toThrowErrorMatchingInlineSnapshot('"Input must not be null"')
})
```

## ARIA Snapshots

For browser mode testing, capture accessibility tree snapshots:

```typescript
test('accessible form', async () => {
  const screen = render(<LoginForm />)
  await expect(screen.getByRole('form')).toMatchAriaSnapshot(`
    - form "Login":
      - textbox "Email"
      - textbox "Password"
      - button "Sign In"
  `)
})
```

### toMatchAriaInlineSnapshot()

```typescript
await expect(element).toMatchAriaInlineSnapshot(`
  - heading "Dashboard" [level=1]
  - navigation "Main"
`)
```

## Custom Serializers

### Via expect.addSnapshotSerializer()

```typescript
expect.addSnapshotSerializer({
  test(val) {
    return val && val instanceof User
  },
  serialize(val, config, indentation, depth, refs, printer) {
    return `User { name: ${printer(val.name, config, indentation, depth, refs)} }`
  },
})

test('custom serialized user', () => {
  expect(new User('Alice')).toMatchInlineSnapshot(`User { name: "Alice" }`)
})
```

### Via Config

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    snapshotSerializers: ['./src/test/user-serializer.ts'],
  },
})
```

## Custom Snapshot Matchers

Build reusable snapshot matchers using the `Snapshots` helper:

```typescript
import { expect, test, Snapshots } from 'vitest'

const { toMatchSnapshot, toMatchInlineSnapshot } = Snapshots

expect.extend({
  toMatchTrimmedSnapshot(received: string) {
    return toMatchSnapshot.call(this, received.trim())
  },

  toMatchTrimmedInlineSnapshot(received: string, expected?: string) {
    return toMatchInlineSnapshot.call(this, received.trim(), expected)
  },
})

test('trimmed snapshot', () => {
  expect('  hello world  ').toMatchTrimmedInlineSnapshot('"hello world"')
})
```

## Configuration

```typescript
export default defineConfig({
  test: {
    snapshotFormat: {
      printBasicPrototype: false, // default: false (cleaner output than Jest)
      escapeString: false,
      indent: 2,
    },
    snapshotSerializers: [],
    resolveSnapshotPath: (testPath, snapExtension) =>
      testPath.replace('src/', 'snapshots/') + snapExtension,
  },
})
```

### Key Differences from Jest

| Setting | Jest Default | Vitest Default |
|---------|-------------|----------------|
| `printBasicPrototype` | `true` | `false` |
| Message separator | `:` | `>` |
| Error snapshot format | Includes stack | Message only |

## Best Practices

1. **Review snapshots in PRs** — treat snapshot changes like code changes
2. **Keep snapshots small** — large snapshots are hard to review and break frequently
3. **Use inline for small values** — easier to review without switching files
4. **Use file snapshots for generated content** — HTML, SVG, JSON with proper extensions
5. **Don't snapshot implementation details** — snapshot the public interface
6. **Use shape hints for dynamic data** — `expect.any()` for IDs, timestamps
7. **Delete unused snapshots** — run `vitest --update` periodically to clean up
8. **Custom serializers for domain objects** — make snapshots more readable

---

**Related:** [02-assertions.md](02-assertions.md) for matchers, [07-browser-mode.md](07-browser-mode.md) for ARIA snapshots
