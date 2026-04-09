# Technical Audit

Run systematic technical quality checks and generate a comprehensive report. This is a code-level audit, not a design critique. Check what is measurable and verifiable in the implementation.

## Table of Contents

- [5-Dimension Diagnostic Scan](#5-dimension-diagnostic-scan)
  - [1. Accessibility](#1-accessibility)
  - [2. Performance](#2-performance)
  - [3. Theming](#3-theming)
  - [4. Responsive Design](#4-responsive-design)
  - [5. Anti-Patterns](#5-anti-patterns)
- [Scoring](#scoring)
- [Report Format](#report-format)
- [Recommended Actions](#recommended-actions)

---

## 5-Dimension Diagnostic Scan

Run comprehensive checks across 5 dimensions. Score each dimension 0-4.

### 1. Accessibility

**Check for**:
- **Contrast issues**: Text contrast ratios below 4.5:1 (or 7:1 for AAA)
- **Missing ARIA**: Interactive elements without proper roles, labels, or states
- **Keyboard navigation**: Missing focus indicators, illogical tab order, keyboard traps
- **Semantic HTML**: Improper heading hierarchy, missing landmarks, divs used instead of buttons
- **Alt text**: Missing or poor image descriptions
- **Form issues**: Inputs without labels, poor error messaging, missing required indicators
- **Focus management**: Focus not moved to new content (modals, dynamic updates)
- **Screen reader**: State changes not announced, live regions missing

**Scoring**:

| Score | Criteria |
|-------|----------|
| 0 | Inaccessible -- fails WCAG A |
| 1 | Major gaps -- few ARIA labels, no keyboard nav |
| 2 | Partial -- some a11y effort, significant gaps |
| 3 | Good -- WCAG AA mostly met, minor gaps |
| 4 | Excellent -- WCAG AA fully met, approaches AAA |

### 2. Performance

**Check for**:
- **Layout thrashing**: Reading/writing layout properties in loops
- **Expensive animations**: Animating layout properties (width, height, top, left) instead of transform/opacity
- **Missing optimization**: Images without lazy loading, unoptimized assets, missing will-change
- **Bundle size**: Unnecessary imports, unused dependencies, tree-shaking gaps
- **Render performance**: Unnecessary re-renders, missing memoization
- **Render blocking**: CSS/JS blocking first paint, no critical CSS extraction
- **Image optimization**: Missing srcset, no WebP/AVIF fallbacks, oversized images
- **CLS (Cumulative Layout Shift)**: Elements that shift after load, missing dimension attributes on images

**Scoring**:

| Score | Criteria |
|-------|----------|
| 0 | Severe issues -- layout thrash, unoptimized everything |
| 1 | Major problems -- no lazy loading, expensive animations |
| 2 | Partial -- some optimization, gaps remain |
| 3 | Good -- mostly optimized, minor improvements possible |
| 4 | Excellent -- fast, lean, well-optimized |

### 3. Theming

**Check for**:
- **Hard-coded colors**: Colors not using design tokens or CSS custom properties
- **Broken dark mode**: Missing dark mode variants, poor contrast in dark theme
- **Inconsistent tokens**: Using wrong tokens, mixing token types
- **Theme switching issues**: Values that do not update on theme change
- **System preferences**: No respect for prefers-color-scheme, prefers-reduced-motion, prefers-contrast

**Scoring**:

| Score | Criteria |
|-------|----------|
| 0 | No theming -- hard-coded everything |
| 1 | Minimal tokens -- mostly hard-coded |
| 2 | Partial -- tokens exist but inconsistently used |
| 3 | Good -- tokens used, minor hard-coded values |
| 4 | Excellent -- full token system, dark mode works perfectly |

### 4. Responsive Design

**Check for**:
- **Fixed widths**: Hard-coded widths that break on mobile
- **Touch targets**: Interactive elements smaller than 44x44px
- **Horizontal scroll**: Content overflow on narrow viewports
- **Text scaling**: Layouts that break when text size increases
- **Missing breakpoints**: No mobile/tablet variants
- **Viewport handling**: Missing viewport meta tag, improper viewport units
- **Orientation**: Layout breaks on landscape/portrait switch

**Scoring**:

| Score | Criteria |
|-------|----------|
| 0 | Desktop-only -- breaks on mobile |
| 1 | Major issues -- some breakpoints, many failures |
| 2 | Partial -- works on mobile, rough edges |
| 3 | Good -- responsive, minor touch target or overflow issues |
| 4 | Excellent -- fluid, all viewports, proper touch targets |

### 5. Anti-Patterns

Check for AI slop tells and general design/code anti-patterns.

**Check for**:
- **Div soup**: Deeply nested divs instead of semantic elements
- **Inline styles**: Style attributes instead of classes or CSS
- **Z-index chaos**: Arbitrary z-index values without a system
- **Dead code**: Unused components, unreachable code paths, commented-out blocks
- **Hardcoded values**: Magic numbers, hardcoded strings, non-tokenized spacing
- **AI slop tells**: AI color palette, gradient text, glassmorphism, hero metrics, card grids, generic fonts

**Scoring**:

| Score | Criteria |
|-------|----------|
| 0 | AI slop gallery -- 5+ tells present |
| 1 | Heavy AI aesthetic -- 3-4 tells |
| 2 | Some tells -- 1-2 noticeable |
| 3 | Mostly clean -- subtle issues only |
| 4 | No AI tells -- distinctive, intentional design |

---

## Scoring

### Health Score Table

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | ? | [most critical a11y issue or "--"] |
| 2 | Performance | ? | |
| 3 | Theming | ? | |
| 4 | Responsive Design | ? | |
| 5 | Anti-Patterns | ? | |
| **Total** | | **??/20** | **[Rating band]** |

### Rating Bands

| Score Range | Rating | What It Means |
|-------------|--------|---------------|
| 18-20 | Excellent | Minor polish only |
| 14-17 | Good | Address weak dimensions |
| 10-13 | Acceptable | Significant work needed |
| 6-9 | Poor | Major overhaul required |
| 0-5 | Critical | Fundamental issues throughout |

---

## Report Format

### Anti-Patterns Verdict

Start here. Pass/fail: Does this look AI-generated? List specific tells. Be brutally honest.

### Executive Summary

- Audit Health Score: **??/20** ([rating band])
- Total issues found (count by severity: P0/P1/P2/P3)
- Top 3-5 critical issues
- Recommended next steps

### Detailed Findings by Severity

Tag every issue with P0-P3 severity:

| Priority | Name | Description | Action |
|----------|------|-------------|--------|
| **P0** | Blocking | Prevents task completion | Fix immediately |
| **P1** | Major | Significant difficulty or WCAG AA violation | Fix before release |
| **P2** | Minor | Annoyance, workaround exists | Fix in next pass |
| **P3** | Polish | Nice-to-fix, no real user impact | Fix if time permits |

For each issue, document:
- **[P?] Issue name**
- **Location**: Component, file, line
- **Category**: Accessibility / Performance / Theming / Responsive / Anti-Pattern
- **Impact**: How it affects users
- **Standard**: Which standard it violates (WCAG, performance budget, etc.)
- **Recommendation**: How to fix it

### Systemic Problems

Identify recurring problems that indicate systemic gaps rather than one-off mistakes:

- "Hard-coded colors appear in 15+ components -- should use design tokens"
- "Touch targets consistently too small (<44px) throughout mobile experience"
- "No loading states anywhere in the application"

These patterns indicate architectural decisions to address, not individual bugs to fix.

### Positive Findings

Note what is working well -- good practices to maintain and replicate. Always include this section. Developers need to know what to keep doing.

---

## Recommended Actions

List recommended actions in priority order (P0 first, then P1, then P2):

1. **[P?]** Brief description of what to fix (specific context from audit findings)
2. **[P?]** Brief description (specific context)

**Rules for recommendations**:
- Map findings to the most appropriate fix approach
- Order by severity, then by impact
- End with a polish pass as the final step if any fixes were recommended
- Be specific and actionable -- "Fix contrast on .btn-secondary (currently 2.8:1, needs 4.5:1)" not "Improve contrast"

**Important principles**:
- Be thorough but actionable. Too many P3 issues creates noise. Focus on what actually matters.
- Never report issues without explaining impact (why does this matter?)
- Never provide generic recommendations (be specific and actionable)
- Never skip positive findings (celebrate what works)
- Never forget to prioritize (everything cannot be P0)
- Never report false positives without verification
