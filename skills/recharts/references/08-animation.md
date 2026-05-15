# Animation

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Overview

Recharts has built-in animation support for data series components. In v3, animations are handled internally (the `react-smooth` dependency was removed). The default `isAnimationActive="auto"` respects both SSR environments and the user's `prefers-reduced-motion` system setting.

## Animated Components

These components support animation props: Area, Bar, ErrorBar, Funnel, Line, Scatter, Pie, Radar, RadialBar, Treemap.

## Core Animation Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Enable animation |
| `animationBegin` | `number` | varies | Delay before start (ms) |
| `animationDuration` | `number` | varies | Animation length (ms) |
| `animationEasing` | `string \| function` | `"ease"` | Easing function |
| `onAnimationStart` | `function` | — | Callback when animation begins |
| `onAnimationEnd` | `function` | — | Callback when animation ends |

## isAnimationActive Behavior

| Value | Effect |
|:------|:-------|
| `"auto"` | Enabled in browser, disabled during SSR, respects `prefers-reduced-motion` |
| `true` | Always animate |
| `false` | Never animate |

`"auto"` is the recommended default. It handles:
- SSR: animations disabled to avoid hydration mismatch
- Accessibility: animations disabled when user has `prefers-reduced-motion: reduce`
- Browser: animations enabled

## Default Durations

| Component | animationDuration | animationBegin |
|:----------|:-----------------:|:--------------:|
| Bar | 400ms | 0ms |
| Scatter | 400ms | 0ms |
| ErrorBar | 400ms | 0ms |
| Line | 1500ms | 0ms |
| Area | 1500ms | 0ms |
| Pie | 1500ms | 400ms |
| Radar | 1500ms | 0ms |
| RadialBar | 1500ms | 0ms |
| Funnel | 1500ms | 400ms |
| Treemap | 1500ms | 0ms |

## Easing Functions

### Predefined Strings

| Value | Behavior |
|:------|:---------|
| `"ease"` | Slow start and end (default) |
| `"ease-in"` | Slow start, fast end |
| `"ease-out"` | Fast start, slow end |
| `"ease-in-out"` | Slow start and end |
| `"linear"` | Constant speed |
| `"spring"` | Physics-based spring simulation |

### Custom Cubic Bezier

```tsx
<Line dataKey="value" animationEasing="cubic-bezier(0.68, -0.55, 0.265, 1.55)" />
```

### Custom Function

The function receives progress (0 to 1) and returns the eased value (0 to 1):

```tsx
<Bar
  dataKey="value"
  animationEasing={(t) => {
    // Bounce easing
    if (t < 1 / 2.75) return 7.5625 * t * t;
    if (t < 2 / 2.75) return 7.5625 * (t -= 1.5 / 2.75) * t + 0.75;
    if (t < 2.5 / 2.75) return 7.5625 * (t -= 2.25 / 2.75) * t + 0.9375;
    return 7.5625 * (t -= 2.625 / 2.75) * t + 0.984375;
  }}
/>
```

## Staggered Entry Animations

Combine `animationBegin` with index for staggered effects:

```tsx
const data = [/* ... */];

<BarChart data={data}>
  {data.map((_, index) => (
    <Bar
      key={index}
      dataKey={`value${index}`}
      animationBegin={index * 200}
      animationDuration={800}
    />
  ))}
</BarChart>
```

For Pie chart entries that appear sequentially, use the default `animationBegin={400}` — the first animation finishes, then the next slice begins.

## Animation Callbacks

```tsx
<Line
  dataKey="value"
  onAnimationStart={() => console.log('Animation started')}
  onAnimationEnd={() => console.log('Animation finished')}
/>
```

Use cases:
- Show a loading state until animation completes
- Trigger subsequent animations
- Log timing metrics

## Disabling Animations

### Per Component

```tsx
<Line dataKey="value" isAnimationActive={false} />
```

### All Components (Global)

No built-in global toggle. Apply to each component or create a wrapper:

```tsx
const ANIMATION_OFF = { isAnimationActive: false as const };

<LineChart data={data}>
  <Line dataKey="a" {...ANIMATION_OFF} />
  <Line dataKey="b" {...ANIMATION_OFF} />
</LineChart>
```

### For Performance

Disable animations when:
- Rendering large datasets (>1000 points)
- Real-time updating charts
- Server-side rendering (handled automatically by `"auto"`)
- Printing or static exports

## Tooltip Animation

Tooltip has its own animation props:

```tsx
<Tooltip
  isAnimationActive={true}
  animationDuration={200}
  animationEasing="ease-out"
/>
```

Tooltip animation controls the transition between positions as the user moves their cursor.

## Common Patterns

### Data Update Animation

When `data` changes, animated components automatically transition to new values:

```tsx
function LiveChart() {
  const [data, setData] = useState(initialData);

  useEffect(() => {
    const interval = setInterval(() => {
      setData(generateNewData());
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <BarChart data={data}>
      <Bar dataKey="value" animationDuration={500} animationEasing="ease-out" />
    </BarChart>
  );
}
```

### Reduced Motion Support

The `"auto"` setting handles this, but you can also check manually:

```tsx
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

<Line dataKey="value" isAnimationActive={!prefersReducedMotion} />
```
