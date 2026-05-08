# shadcn/ui — Accessibility

> Source: [ui.shadcn.com/docs/components](https://ui.shadcn.com/docs/components) | Radix UI Accessibility Patterns

## Table of Contents
- [Foundation](#foundation)
- [Radix UI Primitives](#radix-ui-primitives)
- [Keyboard Navigation Patterns](#keyboard-navigation-patterns)
- [ARIA Attributes](#aria-attributes)
- [Focus Management](#focus-management)
- [Screen Reader Support](#screen-reader-support)
- [Form Accessibility](#form-accessibility)
- [Color Contrast](#color-contrast)
- [Motion and Animation](#motion-and-animation)
- [Testing Accessibility](#testing-accessibility)
- [Common Mistakes](#common-mistakes)

## Foundation

shadcn/ui inherits accessibility from Radix UI primitives. Radix implements WAI-ARIA design patterns with:
- Correct `role` and `aria-*` attributes on all components
- Keyboard navigation following ARIA Authoring Practices
- Focus management (trapping, restoration, roving tabindex)
- Screen reader announcements for state changes
- Tested with NVDA, JAWS, and VoiceOver

Your responsibility: provide accessible names, maintain color contrast, and avoid breaking the DOM structure Radix sets up.

## Radix UI Primitives

Components and the WAI-ARIA patterns they implement:

| Component | Pattern | Key Behavior |
|-----------|---------|-------------|
| Dialog | Dialog (modal) | Focus trap, Escape to close |
| AlertDialog | Alert Dialog | Non-dismissible, requires action |
| DropdownMenu | Menu | Arrow key navigation, typeahead |
| Select | Listbox | Arrow keys, typeahead search |
| Tabs | Tablist | Arrow keys switch, Enter/Space activate |
| Accordion | Accordion | Arrow keys navigate, Enter/Space toggle |
| Switch | Switch | Space to toggle, checked state |
| Checkbox | Checkbox | Space to toggle, tri-state support |
| RadioGroup | Radio Group | Arrow keys select, one active |
| Tooltip | Tooltip | Focus/hover reveals, Escape dismisses |
| Popover | Non-modal dialog | Focus management, Escape closes |
| Slider | Slider | Arrow keys adjust value |
| Toggle | Toggle button | aria-pressed state |

## Keyboard Navigation Patterns

### Dialog / Sheet / Drawer

```
Tab         → Move focus between focusable elements inside
Shift+Tab   → Move focus backward
Escape      → Close the dialog
```

Focus is trapped inside the dialog. When closed, focus returns to the trigger element.

### Dropdown Menu / Context Menu

```
Enter/Space → Open menu (on trigger), select item
ArrowDown   → Move to next item
ArrowUp     → Move to previous item
ArrowRight  → Open submenu
ArrowLeft   → Close submenu
Escape      → Close menu
Home        → First item
End         → Last item
Type chars  → Typeahead search
```

### Tabs

```
ArrowLeft   → Previous tab
ArrowRight  → Next tab
Home        → First tab
End         → Last tab
Enter/Space → Activate focused tab
```

### Accordion

```
Enter/Space → Toggle section
ArrowDown   → Next section trigger
ArrowUp     → Previous section trigger
Home        → First section trigger
End         → Last section trigger
```

### Select

```
Enter/Space → Open/close dropdown
ArrowDown   → Next option
ArrowUp     → Previous option
Home        → First option
End         → Last option
Type chars  → Typeahead search
```

### Slider

```
ArrowRight/Up   → Increase value
ArrowLeft/Down  → Decrease value
Home            → Minimum value
End             → Maximum value
Page Up         → Increase by large step
Page Down       → Decrease by large step
```

## ARIA Attributes

### Required Attributes You Must Provide

**Accessible names for controls:**

```tsx
// Icon-only buttons MUST have aria-label
<Button variant="ghost" size="icon" aria-label="Close sidebar">
  <X className="h-4 w-4" />
</Button>

// Or use sr-only text
<Button variant="ghost" size="icon">
  <X className="h-4 w-4" />
  <span className="sr-only">Close sidebar</span>
</Button>
```

**Dialog titles are required:**

```tsx
// DialogTitle provides the accessible name for the dialog
<DialogHeader>
  <DialogTitle>Edit Profile</DialogTitle>
  <DialogDescription>Make changes to your profile.</DialogDescription>
</DialogHeader>

// If you want to hide the title visually
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";

<DialogHeader>
  <VisuallyHidden>
    <DialogTitle>Image Preview</DialogTitle>
  </VisuallyHidden>
</DialogHeader>
```

**Form labels are required:**

```tsx
// Every input needs an accessible label
<Label htmlFor="email">Email</Label>
<Input id="email" type="email" />

// Or use aria-label for inputs without visible labels
<Input aria-label="Search" placeholder="Search..." />
```

### Attributes Radix Handles Automatically

- `role` on all interactive elements
- `aria-expanded` on triggers for expandable content
- `aria-selected` on tabs and menu items
- `aria-checked` on checkboxes and switches
- `aria-haspopup` on menu triggers
- `aria-controls` linking triggers to content
- `aria-labelledby` linking dialogs to titles
- `aria-describedby` linking to descriptions
- `aria-disabled` on disabled elements
- `aria-hidden` on decorative elements

## Focus Management

### Focus Trapping

Dialogs, Sheets, and Alert Dialogs automatically trap focus. Tab cycles through focusable elements inside without escaping to the background.

### Focus Restoration

When a dialog/popover closes, focus returns to the element that triggered it.

### Focus Visible Styles

Never remove focus indicators:

```css
/* DO — customize the focus ring */
*:focus-visible {
  outline: 2px solid var(--ring);
  outline-offset: 2px;
}

/* DON'T — remove focus styles */
*:focus {
  outline: none; /* NEVER DO THIS */
}
```

shadcn/ui uses Tailwind's `focus-visible:` utilities for focus styles that only appear on keyboard navigation, not mouse clicks.

### asChild Pattern

Use `asChild` to compose triggers with your own elements while preserving accessibility:

```tsx
// asChild passes all accessibility props to your element
<DialogTrigger asChild>
  <Button variant="outline">Open</Button>
</DialogTrigger>

// Without asChild, Radix renders its own <button>
<DialogTrigger>Open</DialogTrigger>
```

## Screen Reader Support

### Live Regions for Dynamic Content

```tsx
// Toast/Sonner uses aria-live internally
// For custom notifications:
<div role="status" aria-live="polite">
  {message && <p>{message}</p>}
</div>

// Assertive for errors
<div role="alert" aria-live="assertive">
  {error && <p>{error}</p>}
</div>
```

### Visually Hidden Text

For screen-reader-only content:

```tsx
// Using Tailwind's sr-only
<span className="sr-only">Close navigation menu</span>

// Using Radix VisuallyHidden
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
<VisuallyHidden>Loading complete</VisuallyHidden>
```

### Decorative Images

```tsx
// Decorative — hide from screen readers
<img src="/pattern.svg" alt="" aria-hidden="true" />

// Informative — describe the content
<img src="/chart.png" alt="Revenue chart showing 20% growth in Q4" />
```

## Form Accessibility

shadcn/ui's Form component automatically handles:

```tsx
<FormField
  control={form.control}
  name="username"
  render={({ field }) => (
    <FormItem>
      {/* FormLabel auto-links to FormControl via htmlFor/id */}
      <FormLabel>Username</FormLabel>
      {/* FormControl wraps input with correct aria attributes */}
      <FormControl>
        <Input {...field} />
      </FormControl>
      {/* FormDescription links via aria-describedby */}
      <FormDescription>Your public display name.</FormDescription>
      {/* FormMessage announces errors via aria-describedby + aria-invalid */}
      <FormMessage />
    </FormItem>
  )}
/>
```

What gets generated in the DOM:

```html
<label for="username">Username</label>
<input id="username" aria-describedby="username-description username-error" aria-invalid="true" />
<p id="username-description">Your public display name.</p>
<p id="username-error" role="alert">Username is required.</p>
```

## Color Contrast

### WCAG Requirements

| Level | Body Text | Large Text | UI Components |
|-------|-----------|------------|---------------|
| AA | 4.5:1 | 3:1 | 3:1 |
| AAA | 7:1 | 4.5:1 | 4.5:1 |

### shadcn/ui Default Contrast

The default themes meet WCAG AA. When customizing colors:

```css
/* Check contrast: foreground against background */
:root {
  --foreground: oklch(0.145 0 0);    /* Near black */
  --background: oklch(1 0 0);        /* White */
  /* Contrast ratio: ~19:1 — excellent */
}

/* Muted text is the most common contrast risk */
:root {
  --muted-foreground: oklch(0.556 0 0);
  --background: oklch(1 0 0);
  /* Verify: ~5.5:1 — passes AA for body text */
}
```

### Testing Tools

- Chrome DevTools → Accessibility panel
- axe DevTools browser extension
- Lighthouse accessibility audit
- WAVE browser extension

## Motion and Animation

### Respecting prefers-reduced-motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Tailwind provides `motion-reduce:` and `motion-safe:` variants:

```tsx
<div className="motion-safe:animate-bounce motion-reduce:animate-none">
  ...
</div>
```

## Testing Accessibility

### Manual Testing Checklist

1. **Keyboard-only** — navigate entire UI without a mouse
2. **Screen reader** — test with VoiceOver (Mac) or NVDA (Windows)
3. **Zoom** — verify layout at 200% browser zoom
4. **Color contrast** — check all text/background combinations
5. **Focus indicators** — visible focus on every interactive element
6. **Labels** — every control has an accessible name
7. **Error messages** — announced to screen readers
8. **Headings** — logical heading hierarchy (h1 → h2 → h3)

### Automated Testing

```bash
npm install -D @axe-core/react
```

```tsx
// In development only
if (process.env.NODE_ENV === "development") {
  import("@axe-core/react").then((axe) => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

## Common Mistakes

1. **Removing DialogTitle** — screen readers can't identify the dialog without it. Use `VisuallyHidden` if you don't want it visible.

2. **Icon buttons without labels** — `<Button size="icon"><X /></Button>` is inaccessible. Add `aria-label` or `sr-only` text.

3. **Custom wrappers breaking focus** — adding a `<div>` between trigger and Radix content can break focus management. Use `asChild` instead.

4. **Overriding focus styles** — `outline: none` on `:focus` hides the keyboard indicator. Use `:focus-visible` to hide only on mouse clicks.

5. **Color-only status indicators** — don't rely solely on color. Use icons, text, or patterns alongside color for colorblind users.

6. **Missing form error associations** — use the `Form` component which auto-wires `aria-describedby` and `aria-invalid`. Manual forms must do this explicitly.

7. **Auto-playing animations** — respect `prefers-reduced-motion`. Use `motion-safe:` Tailwind variant for animations.

8. **Tabs with icons only** — screen readers announce tab labels. Always include text, even if hidden with `sr-only`.
