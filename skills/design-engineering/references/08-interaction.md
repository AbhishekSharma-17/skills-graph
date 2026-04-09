# Interaction Design

## Table of Contents

- [The Eight Interactive States](#the-eight-interactive-states)
- [Focus Management](#focus-management)
- [Form Design](#form-design)
- [Loading States](#loading-states)
- [Native Dialog and Modal](#native-dialog-and-modal)
- [Popover API](#popover-api)
- [CSS Anchor Positioning](#css-anchor-positioning)
- [Dropdown Patterns](#dropdown-patterns)
- [Destructive Actions](#destructive-actions)
- [Roving Tabindex](#roving-tabindex)
- [Skip Links](#skip-links)
- [Gesture Discoverability](#gesture-discoverability)
- [Progressive Disclosure](#progressive-disclosure)

---

## The Eight Interactive States

Every interactive element must handle all eight states. Missing any state creates a broken experience for some user group.

| State | When | Visual Treatment |
|-------|------|------------------|
| **Default** | At rest | Base styling, clearly interactive |
| **Hover** | Pointer over (not touch) | Subtle lift, color shift, cursor change |
| **Active/Pressed** | Being clicked or tapped | Pressed-in feel, darker shade |
| **Focus** | Keyboard or programmatic focus | Visible ring (see Focus Management) |
| **Disabled** | Not currently interactive | Reduced opacity (0.5-0.6), `cursor: not-allowed` |
| **Loading** | Processing an action | Spinner replacing label, skeleton, or progress bar |
| **Error** | Invalid or failed state | Red/danger border, icon, inline message |
| **Success** | Action completed | Green/success indicator, check icon, confirmation |

### Common Mistakes

- Designing hover without focus or vice versa. Keyboard users never see hover states.
- Using only color to indicate state. Always pair color with shape, icon, or text.
- Forgetting active state on mobile where there is no hover.
- Disabled elements with no explanation of why they are disabled.

### Implementation Pattern

```css
.button { /* default */ }
.button:hover { /* pointer over */ }
.button:active { /* pressed */ }
.button:focus-visible { /* keyboard focus */ }
.button:disabled { opacity: 0.5; cursor: not-allowed; }
.button[aria-busy="true"] { /* loading */ }
.button[aria-invalid="true"] { /* error */ }
```

---

## Focus Management

### :focus-visible for Keyboard-Only Rings

Never remove outlines globally. Use `:focus-visible` to show focus rings only for keyboard users, not mouse clicks:

```css
/* Remove default for all focus */
button:focus {
  outline: none;
}

/* Show ring for keyboard navigation only */
button:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

### Focus Ring Design Rules

- **Contrast**: 3:1 minimum against adjacent colors.
- **Thickness**: 2-3px solid line.
- **Offset**: 2px from the element edge (not inside it).
- **Consistency**: Same ring style across all interactive elements.
- **Never remove without replacement**: `outline: none` without `:focus-visible` is an accessibility violation.

### Focus Order

Focus order must follow visual reading order. Use `tabindex="0"` to make non-interactive elements focusable when needed. Never use `tabindex` values greater than 0 -- they create unpredictable tab order.

---

## Form Design

### Placeholders Are NOT Labels

Placeholders disappear when users type. They are hints, not labels. Always use visible `<label>` elements:

```html
<!-- Wrong -->
<input placeholder="Email address">

<!-- Right -->
<label for="email">Email address</label>
<input id="email" type="email" placeholder="name@example.com">
```

### Validation

- **Validate on blur**, not on every keystroke. Exception: password strength meters.
- Place error messages **below** the field.
- Connect errors to fields with `aria-describedby`.
- Show success state when a previously invalid field is corrected.

```html
<label for="email">Email</label>
<input id="email" aria-describedby="email-error" aria-invalid="true">
<p id="email-error" role="alert">Enter a valid email address (e.g., name@example.com)</p>
```

### Layout

- **Single-column preferred** -- reduces cognitive load and prevents field-skipping.
- Group related fields with `<fieldset>` and `<legend>`.
- Place labels above inputs (not to the side) for consistent scanning.
- Mark required fields clearly but do not rely solely on asterisks.

---

## Loading States

### Skeleton Screens Over Spinners

Skeleton screens preview the shape of incoming content and feel faster than generic spinners.

- Match the skeleton shape to the actual content layout.
- Animate with a shimmer effect (left-to-right gradient pulse).
- Avoid layout shift -- the skeleton and loaded content must occupy the same space.

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 25%,
    var(--skeleton-shine) 50%,
    var(--skeleton-base) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}
```

### Optimistic Updates

Show success immediately, rollback on failure. Appropriate for low-stakes actions (likes, follows, toggles). Never use for payments, deletions, or actions that cannot be undone.

### Loading Copy

Be specific: "Saving your draft..." not "Loading...". For long waits, set time expectations or show a progress bar.

---

## Native Dialog and Modal

### Use the `<dialog>` Element

The native `<dialog>` element provides built-in focus trapping and Escape-to-close:

```html
<dialog id="confirm-dialog">
  <h2>Confirm action</h2>
  <p>This will delete the project permanently.</p>
  <form method="dialog">
    <button value="cancel">Keep project</button>
    <button value="confirm">Delete project</button>
  </form>
</dialog>
```

```javascript
const dialog = document.querySelector('#confirm-dialog');
dialog.showModal(); // Opens with backdrop, focus trap, Escape to close
```

### The `inert` Attribute

When a modal is open, mark background content as `inert` to prevent focus and interaction:

```html
<main inert>
  <!-- Cannot be focused or clicked while modal is open -->
</main>
<dialog open>
  <h2>Modal content</h2>
</dialog>
```

### Modal Best Practices

- Always provide a visible close mechanism (button or X).
- Escape key must close the modal.
- Return focus to the trigger element when the modal closes.
- Backdrop click should close non-critical modals.
- Keep modal content concise -- if it needs scrolling, reconsider the pattern.

---

## Popover API

The `[popover]` attribute creates non-modal overlays without JavaScript for simple cases:

```html
<button popovertarget="info-panel">More info</button>
<div id="info-panel" popover>
  <p>Additional details appear here.</p>
</div>
```

### Benefits

- **Light dismiss**: Clicking outside closes automatically.
- **Top layer**: Renders above all content, no z-index wars.
- **Accessible by default**: Proper focus management built in.
- **No JS needed**: For simple show/hide toggling.

### Popover + Anchor Combo

Combine popover with anchor positioning for correctly placed overlays:

```html
<button popovertarget="menu" class="trigger">Open</button>
<div id="menu" popover class="dropdown">
  <button>Option 1</button>
  <button>Option 2</button>
</div>
```

The `popover` attribute places the element in the top layer, which sits above all content regardless of z-index or overflow. No portal needed.

---

## CSS Anchor Positioning

Tether overlays to trigger elements without JavaScript:

```css
.trigger {
  anchor-name: --menu-trigger;
}

.dropdown {
  position: fixed;
  position-anchor: --menu-trigger;
  position-area: block-end span-inline-end;
  margin-top: 4px;
}

/* Flip above if no room below */
@position-try --flip-above {
  position-area: block-start span-inline-end;
  margin-bottom: 4px;
}
```

Because the dropdown uses `position: fixed`, it escapes any `overflow` clipping on ancestor elements. The `@position-try` block handles viewport edges automatically.

**Browser support**: Chrome 125+, Edge 125+. Use a fixed-positioning fallback with manual coordinates for Firefox and Safari.

### Portal/Teleport Fallback

In component frameworks, render overlays at the document root:

- **React**: `createPortal(dropdown, document.body)`
- **Vue**: `<Teleport to="body">`
- **Svelte**: Portal library or mount to `document.body`

Calculate position from `getBoundingClientRect()`, apply `position: fixed` with `top` and `left` values. Recalculate on scroll and resize.

---

## Dropdown Patterns

### Listbox vs Menu (Different ARIA)

- **Listbox** (`role="listbox"`): For selecting a value (combobox, select replacement). Selection changes state.
- **Menu** (`role="menu"`): For triggering actions (context menu, action menu). Items are commands.

Do not mix these roles. A dropdown that selects an option is a listbox. A dropdown that triggers "Edit", "Delete", "Share" is a menu.

### Keyboard Navigation

- **Enter/Space**: Open dropdown, activate item.
- **Arrow Down/Up**: Move through items.
- **Escape**: Close without selecting.
- **Home/End**: Jump to first/last item.
- **Typeahead**: Typing characters jumps to matching item.

### Anti-Patterns

- `position: absolute` inside `overflow: hidden` -- dropdown gets clipped. Use `position: fixed` or top layer.
- Arbitrary z-index like `z-index: 9999`. Use a semantic scale: dropdown (100), sticky (200), modal-backdrop (300), modal (400), toast (500), tooltip (600).
- Rendering dropdown inline without an escape from parent stacking context.

---

## Destructive Actions

### Prefer Undo Over Confirm Dialogs

Users click through confirmation dialogs mindlessly. Undo is more effective:

1. Remove item from UI immediately.
2. Show an undo toast with a timer.
3. Actually delete after the toast expires.

### When Confirmation Is Necessary

Use confirm dialogs only for:

- Truly irreversible actions (account deletion, data purge).
- High-cost operations (billing changes).
- Batch operations affecting many items.

### Name the Destruction

Be specific in the confirmation:

- "Delete project 'Alpha'" not "Are you sure?"
- "Remove 5 team members" not "Delete selected"
- Button labels: "Delete project" / "Keep project", never "Yes" / "No"

---

## Roving Tabindex

For component groups (tabs, toolbars, menu items, radio groups), use roving tabindex so the group is one Tab stop and arrow keys navigate within:

```html
<div role="tablist">
  <button role="tab" tabindex="0" aria-selected="true">Tab 1</button>
  <button role="tab" tabindex="-1">Tab 2</button>
  <button role="tab" tabindex="-1">Tab 3</button>
</div>
```

- Arrow keys move `tabindex="0"` between items.
- Tab moves to the next component entirely.
- Wrap around: Right arrow on last item goes to first.
- Support both horizontal (Left/Right) and vertical (Up/Down) arrows based on layout.

---

## Skip Links

Always include a "Skip to main content" link as the first focusable element:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<!-- Navigation here -->
<main id="main-content">
  <!-- Page content -->
</main>
```

```css
.skip-link {
  position: absolute;
  left: -9999px;
}

.skip-link:focus {
  position: static;
  /* Or position at top of page visually */
}
```

For complex pages, add multiple skip links: "Skip to search", "Skip to results", "Skip to footer".

---

## Gesture Discoverability

Swipe-to-delete, pull-to-refresh, and similar gestures are invisible. Never rely on gesture-only interactions.

### Making Gestures Discoverable

- **Partial reveal**: Show a delete button peeking from the edge on list items.
- **Onboarding hints**: Coach marks on first use showing the gesture.
- **Visible fallback**: Always provide a visible alternative (a menu with "Delete", a refresh button).

### Rules

- Every gesture must have a visible, tappable alternative.
- Do not assume users know platform-specific gestures.
- Long-press menus should also be accessible via a visible button.

---

## Progressive Disclosure

Show what users need now. Hide complexity behind expand, detail, or secondary views.

### Patterns

- **Accordion/Details**: `<details>/<summary>` for collapsible sections.
- **Tabs**: Group related content behind tab panels.
- **"Show more" links**: Truncate long content with a reveal action.
- **Advanced settings**: Hide behind an "Advanced" toggle or link.
- **Staged forms**: Multi-step wizards instead of one overwhelming form.

### Principles

- Primary actions and information are always visible.
- Secondary or advanced features are one interaction away.
- Never hide critical information behind progressive disclosure.
- Provide clear signals that more content exists (chevrons, "Show more", counts).
