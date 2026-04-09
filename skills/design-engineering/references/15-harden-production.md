# Harden & Production

Making interfaces resilient against edge cases, errors, internationalization issues, and real-world usage. Then optimizing performance for fast, smooth production experiences. Designs that only work with perfect data are not production-ready.

## Table of Contents

- [Hardening](#hardening)
  - [Text Overflow and Wrapping](#text-overflow-and-wrapping)
  - [Internationalization (i18n)](#internationalization-i18n)
  - [Error Handling](#error-handling)
  - [Edge Cases and Boundary Conditions](#edge-cases-and-boundary-conditions)
  - [Input Validation](#input-validation)
  - [Accessibility Resilience](#accessibility-resilience)
  - [Performance Resilience](#performance-resilience)
- [Performance Optimization](#performance-optimization)
  - [Loading Performance](#loading-performance)
  - [Rendering Performance](#rendering-performance)
  - [Animation Performance](#animation-performance)
- [Core Web Vitals](#core-web-vitals)
  - [Largest Contentful Paint (LCP)](#largest-contentful-paint-lcp)
  - [First Input Delay and INP](#first-input-delay-and-inp)
  - [Cumulative Layout Shift (CLS)](#cumulative-layout-shift-cls)
- [React and Framework Optimization](#react-and-framework-optimization)
- [Network Optimization](#network-optimization)
- [Testing Strategies](#testing-strategies)

---

## Hardening

### Text Overflow and Wrapping

**Single line with ellipsis**:
```css
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

**Multi-line with clamp**:
```css
.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

**Word breaking for long strings**:
```css
.wrap {
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
```

**Flex/Grid overflow prevention**:
```css
.flex-item {
  min-width: 0; /* Allow shrinking below content size */
  overflow: hidden;
}
.grid-item {
  min-width: 0;
  min-height: 0;
}
```

**Responsive text sizing**:
- Use `clamp()` for fluid typography
- Set minimum readable sizes (14px on mobile)
- Test text scaling (zoom to 200%)
- Ensure containers expand with text

### Internationalization (i18n)

**Text expansion rates by language**:
- German: 30% longer than English
- Finnish: 30-40% longer
- French: 15-20% longer
- Japanese/Chinese/Korean: may be shorter but need more vertical space
- Arabic/Hebrew: RTL layout required

**Text expansion handling**:
- Add 30-40% space budget for translations
- Use flexbox/grid that adapts to content
- Test with longest language (usually German)
- Avoid fixed widths on text containers

```jsx
// Bad: assumes short English text
<button className="w-24">Submit</button>

// Good: adapts to content
<button className="px-4 py-2">Submit</button>
```

**RTL (Right-to-Left) layout**:
```css
/* Use logical properties */
margin-inline-start: 1rem; /* Not margin-left */
padding-inline: 1rem;      /* Not padding-left/right */
border-inline-end: 1px solid; /* Not border-right */

/* Flip directional icons */
[dir="rtl"] .arrow { transform: scaleX(-1); }
```

**CJK character sets**:
- Use UTF-8 encoding everywhere
- Test with Chinese, Japanese, Korean characters
- Test with emoji (they can be 2-4 bytes)
- Handle different scripts (Latin, Cyrillic, Arabic)

**Date/time/number formatting**:
```javascript
// Use Intl API for proper formatting
new Intl.DateTimeFormat('en-US').format(date); // 1/15/2024
new Intl.DateTimeFormat('de-DE').format(date); // 15.1.2024

new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD'
}).format(1234.56); // $1,234.56
```

**Pluralization rules**:
```javascript
// Bad: assumes English pluralization
`${count} item${count !== 1 ? 's' : ''}`

// Good: use proper i18n library
t('items', { count }) // Handles complex plural rules
```

### Error Handling

**Graceful degradation**:
- Core functionality works without JavaScript
- Images have alt text as fallback
- Progressive enhancement approach
- Fallbacks for unsupported features

**Network errors**:
- Show clear error messages with what happened
- Provide retry button
- Offer offline mode if applicable
- Handle timeout scenarios

**API error handling by status code**:
- 400: show validation errors inline
- 401: redirect to login
- 403: show permission error
- 404: show not found state
- 429: show rate limit message with wait time
- 500: show generic error, offer support contact

**Error boundaries** (React):
- Wrap major sections in error boundaries
- Show fallback UI instead of blank screen
- Log errors for debugging
- Provide recovery actions

**Form validation errors**:
- Inline errors near fields
- Clear, specific messages
- Suggest corrections
- Preserve user input on error

### Edge Cases and Boundary Conditions

**Empty states**: 0 items in list, no search results, no notifications, no data. Always provide a clear next action.

**Loading states**: initial load, pagination, refresh. Show what is loading ("Loading your projects..."). Time estimates for long operations.

**Quantity extremes**:
- 0 items: empty state
- 1 item: singular grammar, no "showing 1 results"
- Maximum items: pagination or virtual scrolling
- Very long text: truncation or wrapping strategy
- Special characters: emoji, accents, symbols

**Concurrent operations**:
- Prevent double-submission (disable button while loading)
- Handle race conditions
- Optimistic updates with rollback
- Conflict resolution

**Permission states**: no permission to view, no permission to edit, read-only mode. Clear explanation of why access is limited.

### Input Validation

**Client-side validation**:
- Required fields
- Format validation (email, phone, URL)
- Length limits
- Pattern matching
- Custom validation rules

**Server-side validation** (always):
- Never trust client-side alone
- Validate and sanitize all inputs
- Protect against injection attacks
- Rate limiting

```html
<input
  type="text"
  maxlength="100"
  pattern="[A-Za-z0-9]+"
  required
  aria-describedby="username-hint"
/>
<small id="username-hint">
  Letters and numbers only, up to 100 characters
</small>
```

### Accessibility Resilience

**Keyboard navigation**: all functionality accessible via keyboard, logical tab order, focus management in modals, skip links for long content.

**Screen reader support**: proper ARIA labels, announce dynamic changes (live regions), descriptive alt text, semantic HTML.

**Motion sensitivity**:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**High contrast mode**: test in Windows high contrast mode, do not rely only on color, provide alternative visual cues.

### Performance Resilience

**Slow connections**: progressive image loading, skeleton screens, optimistic UI updates, offline support (service workers).

**Memory leaks**: clean up event listeners, cancel subscriptions, clear timers/intervals, abort pending requests on unmount.

**Throttling and debouncing**:
```javascript
const debouncedSearch = debounce(handleSearch, 300);
const throttledScroll = throttle(handleScroll, 100);
```

---

## Performance Optimization

Measure before and after. Premature optimization wastes time. Optimize what actually matters.

### Loading Performance

**Images**:
- Modern formats (WebP, AVIF)
- Proper sizing (do not load 3000px image for 300px display)
- Lazy loading for below-fold images
- Responsive images with `srcset` and `picture` element
- Compress to 80-85% quality (usually imperceptible)
- Use CDN for delivery

```html
<img
  src="hero.webp"
  srcset="hero-400.webp 400w, hero-800.webp 800w, hero-1200.webp 1200w"
  sizes="(max-width: 400px) 400px, (max-width: 800px) 800px, 1200px"
  loading="lazy"
  alt="Hero image"
/>
```

**JavaScript**:
- Code splitting (route-based, component-based)
- Tree shaking (remove unused code)
- Remove unused dependencies
- Dynamic imports for large components

```javascript
const HeavyChart = lazy(() => import('./HeavyChart'));
```

**CSS**:
- Remove unused CSS
- Critical CSS inline, rest async
- Minimize CSS files
- Use CSS containment for independent regions

**Fonts**:
- `font-display: swap` or `optional`
- Subset fonts (only characters you need)
- Preload critical fonts
- Limit font weights loaded

```css
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0020-007F; /* Basic Latin only */
}
```

### Rendering Performance

**Avoid layout thrashing**:
```javascript
// Bad: alternating reads and writes (causes reflows)
elements.forEach(el => {
  const height = el.offsetHeight;
  el.style.height = height * 2;
});

// Good: batch reads, then batch writes
const heights = elements.map(el => el.offsetHeight);
elements.forEach((el, i) => {
  el.style.height = heights[i] * 2;
});
```

**DOM optimization**:
- Use CSS `contain` property for independent regions
- Minimize DOM depth (flatter is faster)
- Reduce DOM size (fewer elements)
- Use `content-visibility: auto` for long lists
- Virtual scrolling for very long lists (react-window, react-virtualized)

### Animation Performance

**GPU acceleration**:
```css
/* GPU-accelerated (fast) */
.animated {
  transform: translateX(100px);
  opacity: 0.5;
}

/* CPU-bound (slow -- avoid) */
.animated {
  left: 100px;
  width: 300px;
}
```

**60fps target**:
- 16ms per frame budget
- Use `requestAnimationFrame` for JS animations
- Debounce/throttle scroll handlers
- Use CSS animations when possible
- Avoid long-running JavaScript during animations
- Use `will-change` sparingly (creates new layers, uses memory)

**Intersection Observer** for efficient viewport detection:
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Element visible: lazy load or animate
    }
  });
});
```

---

## Core Web Vitals

### Largest Contentful Paint (LCP)

Target: under 2.5 seconds.

- Optimize hero images (preload, proper format, proper size)
- Inline critical CSS
- Preload key resources
- Use CDN
- Server-side rendering for above-fold content

### First Input Delay and INP

FID target: under 100ms. INP target: under 200ms.

- Break up long tasks
- Defer non-critical JavaScript
- Use web workers for heavy computation
- Reduce JavaScript execution time
- Minimize main thread blocking

### Cumulative Layout Shift (CLS)

Target: under 0.1.

- Set explicit dimensions on images and videos
- Do not inject content above existing content
- Use `aspect-ratio` CSS property
- Reserve space for ads/embeds
- Use transform animations (not layout properties)
- Use `font-display: swap` with fallback font metrics

```css
.image-container {
  aspect-ratio: 16 / 9;
}
```

---

## React and Framework Optimization

- `memo()` for expensive components (only when measured as necessary)
- `useMemo()` and `useCallback()` for expensive computations (not for every value)
- Virtualize long lists
- Code split routes with `lazy()` and `Suspense`
- Key stability: use stable IDs, not array indices
- Avoid inline function creation in render (only when it causes measured re-renders)
- Use React DevTools Profiler to identify actual bottlenecks

Framework-agnostic principles:
- Minimize re-renders
- Debounce expensive operations
- Memoize computed values
- Lazy load routes and components

---

## Network Optimization

**Reduce requests**: combine small files, use SVG sprites for icons, inline small critical assets, remove unused third-party scripts.

**Optimize APIs**: use pagination (do not load everything), GraphQL for requesting only needed fields, response compression (gzip, brotli), HTTP caching headers, CDN for static assets.

**Slow connections**: adaptive loading based on connection (`navigator.connection`), optimistic UI updates, request prioritization, progressive enhancement.

---

## Testing Strategies

**Extreme data testing**:
- Very long text: names with 100+ characters
- Emoji in all text fields
- RTL text (Arabic or Hebrew)
- CJK characters (Chinese, Japanese, Korean)
- Special characters and symbols

**Network testing**:
- Disable internet entirely
- Throttle to 3G
- Force API errors for all status codes
- Test timeout scenarios

**Scale testing**:
- 1000+ items in lists
- Rapid concurrent actions (click submit 10 times)
- Large file uploads
- Many simultaneous users

**Device testing**:
- Low-end Android devices (not just flagship iPhone)
- Real devices, not just browser DevTools
- Multiple browsers (Chrome, Firefox, Safari, Edge)
- Screen readers (VoiceOver, NVDA)
- Keyboard-only navigation

**Automated testing**:
- Unit tests for edge cases
- Integration tests for error scenarios
- E2E tests for critical paths
- Visual regression tests
- Accessibility tests (axe, WAVE)

**NEVER**:
- Optimize without measuring (premature optimization)
- Sacrifice accessibility for performance
- Break functionality while optimizing
- Use `will-change` everywhere
- Lazy load above-fold content
- Optimize micro-optimizations while ignoring major bottlenecks
- Forget about mobile performance
- Assume perfect input (validate everything)
- Ignore internationalization (design for global)
- Leave error messages generic ("Error occurred")
- Trust client-side validation alone
- Use fixed widths for text
- Block entire interface when one component errors
