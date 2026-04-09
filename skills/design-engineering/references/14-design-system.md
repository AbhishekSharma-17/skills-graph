# Design System

Techniques for normalizing existing UI to match design system standards and extracting reusable patterns into a shared system. Normalize brings features back in line with the system. Extract discovers patterns worth systematizing and builds improved reusable versions.

---

## Normalize

Audit and realign UI to match design system standards, spacing, tokens, and patterns. Use when features have drifted from the system or when consistency needs to be restored.

### Discover the Design System

Before making changes, deeply understand the context:

- Search for design system documentation, UI guidelines, component libraries, or style guides
- Study core design principles and aesthetic direction
- Understand target audience and personas
- Map component patterns and conventions
- Catalog design tokens (colors, typography, spacing)

If something is not clear, ask. Do not guess at design system principles.

### Analyze Current Feature for Drift

Assess what works and what does not:

- Where does the feature deviate from design system patterns?
- Which inconsistencies are cosmetic vs functional?
- What is the root cause -- missing tokens, one-off implementations, or conceptual misalignment?

### Create a Normalization Plan

Define specific changes that will align the feature:

- Which components can be replaced with design system equivalents?
- Which styles need to use design tokens instead of hard-coded values?
- How can UX patterns match established user flows?

Prioritize UX consistency and usability over visual polish alone.

### Execute Normalization

Systematically address inconsistencies across these dimensions:

- **Typography**: use design system fonts, sizes, weights, and line heights. Replace hard-coded values with typographic tokens or classes.
- **Color and Theme**: apply design system color tokens. Remove one-off color choices that break the palette.
- **Spacing and Layout**: use spacing tokens (margins, padding, gaps). Align with grid systems and layout patterns used elsewhere.
- **Components**: replace custom implementations with design system components. Ensure props and variants match established patterns.
- **Motion and Interaction**: match animation timing, easing, and interaction patterns to other features.
- **Responsive Behavior**: ensure breakpoints and responsive patterns align with design system standards.
- **Accessibility**: verify contrast ratios, focus states, ARIA labels match design system requirements.

### Clean Up

After normalization:

- Consolidate reusable components: move new shared components to the design system path
- Remove orphaned code: delete unused implementations, styles, or files made obsolete
- Verify quality: lint, type-check, and test. Ensure normalization did not introduce regressions
- Ensure DRYness: look for duplication introduced during refactoring and consolidate

**NEVER**:
- Create new one-off components when design system equivalents exist
- Hard-code values that should use design tokens
- Introduce new patterns that diverge from the design system
- Compromise accessibility for visual consistency

---

## Extract

Identify reusable patterns, components, and design tokens, then extract and consolidate them into the design system for systematic reuse.

### Discover Patterns Worth Extracting

Analyze the target area for extraction opportunities:

- **Repeated components**: similar UI patterns used multiple times (buttons, cards, inputs)
- **Hard-coded values**: colors, spacing, typography, shadows that should be tokens
- **Inconsistent variations**: multiple implementations of the same concept (3 different button styles)
- **Reusable patterns**: layout patterns, composition patterns, interaction patterns worth systematizing

### Component Extraction Criteria

Not everything should be extracted. Evaluate each candidate:

- **Used 3+ times**: or likely to be reused in the near future
- **Consistent pattern**: the implementations share a recognizable structure
- **Stable interface**: the component's API is unlikely to change drastically
- **General purpose**: not context-specific to a single feature
- **Maintenance benefit**: systematizing improves consistency more than it costs to maintain

### Plan Extraction

- **Components to extract**: which UI elements become reusable components?
- **Tokens to create**: which hard-coded values become design tokens?
- **Variants to support**: what variations does each component need?
- **Naming conventions**: component names, token names, prop names matching existing patterns
- **Migration path**: how to refactor existing uses to consume the new shared versions

Design systems grow incrementally. Extract what is clearly reusable now, not everything that might someday be reusable.

### Extract and Enrich

Build improved, reusable versions:

**Components** should have:
- Clear props API with sensible defaults
- Proper variants for different use cases
- Accessibility built in (ARIA, keyboard navigation, focus management)
- Documentation and usage examples

**Design tokens** should have:
- Clear naming (primitive vs semantic)
- Proper hierarchy and organization
- Documentation of when to use each token

**Patterns** should have:
- When to use this pattern
- Code examples
- Variations and combinations

### Token Architecture

Organize tokens by category with semantic naming:

- **Spacing tokens**: `--space-xs` (4px), `--space-sm` (8px), `--space-md` (16px), `--space-lg` (24px), `--space-xl` (32px), `--space-2xl` (48px), `--space-3xl` (64px), `--space-4xl` (96px)
- **Color tokens**: primitive (raw values) and semantic (purpose-based: `--color-text-primary`, `--color-surface-elevated`, `--color-border-subtle`)
- **Typography tokens**: `--font-display`, `--font-body`, `--font-mono`; size scale with semantic names (`--text-sm`, `--text-base`, `--text-lg`, `--text-xl`)
- **Shadow tokens**: `--shadow-sm`, `--shadow-md`, `--shadow-lg` with tinted shadows matching background hue
- **Motion tokens**: `--duration-fast` (150ms), `--duration-normal` (250ms), `--duration-slow` (400ms); `--ease-out` (cubic-bezier for deceleration)
- **Breakpoint tokens**: `--bp-sm` (640px), `--bp-md` (768px), `--bp-lg` (1024px), `--bp-xl` (1280px)

### Migration Strategy

Replace existing uses with the new shared versions:

- **Find all instances**: search for the patterns you have extracted
- **Replace systematically**: update each use to consume the shared version
- **Gradual replacement**: do not try to migrate everything at once. Replace feature by feature.
- **Backwards compatibility period**: keep old implementations temporarily if needed, mark as deprecated
- **Test thoroughly**: ensure visual and functional parity after each migration
- **Delete dead code**: remove the old implementations once fully migrated

### Document

Update design system documentation:

- Add new components to the component library
- Document token usage and values
- Add examples and guidelines
- Update any Storybook or component catalog

**NEVER**:
- Extract one-off, context-specific implementations without generalization
- Create components so generic they are useless
- Extract without considering existing design system conventions
- Skip proper TypeScript types or prop documentation
- Create tokens for every single value (tokens should have semantic meaning)

---

## Token Naming Conventions

### Primitive vs Semantic Tokens

Design tokens work best as a two-layer system:

**Primitive tokens** are raw values with descriptive names:
```css
--blue-500: oklch(0.55 0.15 250);
--gray-100: oklch(0.95 0.005 250);
--space-4: 16px;
--radius-md: 8px;
```

**Semantic tokens** map primitives to purposes:
```css
--color-text-primary: var(--gray-900);
--color-text-secondary: var(--gray-600);
--color-text-disabled: var(--gray-400);
--color-surface-default: var(--gray-50);
--color-surface-elevated: var(--white);
--color-surface-sunken: var(--gray-100);
--color-border-default: var(--gray-200);
--color-border-subtle: var(--gray-100);
--color-accent-default: var(--blue-500);
--color-accent-hover: var(--blue-600);
--color-success: var(--green-500);
--color-warning: var(--amber-500);
--color-error: var(--red-500);
```

Semantic tokens are the ones consumed by components. Primitives are internal to the design system. This separation makes theming possible -- swap the primitive mappings for dark mode or alternate themes without touching any component code.

### Spacing Token Scale

Use a 4pt base with a non-linear scale. The 8pt-only scale is too coarse for fine UI work:

| Token | Value | Typical Use |
|-------|-------|-------------|
| `--space-1` | 4px | Tight internal gaps, icon-to-label |
| `--space-2` | 8px | Input padding, compact lists |
| `--space-3` | 12px | Between related elements |
| `--space-4` | 16px | Standard component padding |
| `--space-6` | 24px | Between groups of elements |
| `--space-8` | 32px | Section internal padding |
| `--space-12` | 48px | Between major sections |
| `--space-16` | 64px | Page-level separation |
| `--space-24` | 96px | Hero-level breathing room |

### Typography Token Scale

Define a scale that creates clear visual hierarchy with sufficient contrast between steps:

| Token | Size | Weight | Use |
|-------|------|--------|-----|
| `--text-xs` | 12px | 400-500 | Captions, labels, metadata |
| `--text-sm` | 14px | 400-500 | Secondary text, descriptions |
| `--text-base` | 16px | 400 | Body text |
| `--text-lg` | 18px | 500 | Lead paragraphs, emphasis |
| `--text-xl` | 20px | 600 | Card titles, subheadings |
| `--text-2xl` | 24px | 600 | Section headings |
| `--text-3xl` | 30px | 700 | Page headings |
| `--text-4xl` | 36px | 700-800 | Hero subheadings |
| `--text-5xl` | 48px | 800 | Display text |
| `--text-6xl` | 60px | 800-900 | Hero headlines |

### Component Token Patterns

Components should consume semantic tokens, not primitives:

```css
.button-primary {
  background: var(--color-accent-default);
  color: var(--color-text-on-accent);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: background var(--duration-fast) var(--ease-out);
}

.button-primary:hover {
  background: var(--color-accent-hover);
}
```

This ensures every component automatically adapts when tokens change for theming, dark mode, or brand updates.

---

## Design System Health Checks

Periodically audit your design system for drift and decay:

- **Token coverage**: what percentage of color, spacing, and typography values in the codebase come from tokens vs hard-coded values?
- **Component adoption**: are teams using design system components or building one-offs?
- **Variant sprawl**: are components accumulating too many variants? Prune unused ones.
- **Documentation freshness**: do docs match the actual implementation?
- **Accessibility compliance**: do all components still meet WCAG standards after updates?
- **Performance impact**: is the design system CSS growing unbounded? Check bundle size.
- **Consistency score**: pick 5 random pages and count visual inconsistencies. Zero is the target.
