# Migration to v3

> Source: [recharts/recharts Wiki — v3.0 Migration](https://github.com/recharts/recharts/wiki/v3.0-Migration)

## Table of Contents

- [Requirements](#requirements)
- [Removed Props](#removed-props)
- [Behavioral Changes](#behavioral-changes)
- [Type Changes](#type-changes)
- [Removed Dependencies](#removed-dependencies)
- [New Features by Version](#new-features-by-version)
- [Migration Checklist](#migration-checklist)

## Requirements

| Requirement | v2 | v3 |
|:------------|:---|:---|
| React | 16+ | 16.8+ (hooks) |
| TypeScript | 4.x | 5.x+ |
| Node.js | 14+ | 18+ |
| TS target | ES5 | ES6+ |

## Removed Props

| Component | Removed Prop | Replacement |
|:----------|:------------|:------------|
| Scatter | `activeIndex` | Use Tooltip |
| Bar | `activeIndex` | Use Tooltip |
| Pie | `activeIndex` | Use Tooltip |
| Pie | `blendStroke` | Use `stroke="none"` |
| Pie | `activeShape` | Use `shape` with `isActive` (v3.5+) |
| Pie | `inactiveShape` | Use `shape` with `isActive` (v3.5+) |
| All | `alwaysShow` | Was deprecated in v2, now removed |
| Reference* | `isFront` | Removed (was non-functional) |
| Funnel | `animateNewValues` | Removed as unused |
| Area | `animateNewValues` | Removed as unused |
| Scatter | internal `points` | Removed |
| Legend | internal `payload` | Removed |
| Customized | extra child props | Use hooks instead |
| All | `Cell` component | Use `shape` prop (deprecated v3.7, removal v4.0) |

## Behavioral Changes

### Accessibility Default

```tsx
// v2: accessibilityLayer defaults to false
// v3: accessibilityLayer defaults to true
<LineChart accessibilityLayer={false}> // Opt out explicitly if needed
```

### Tooltip in Scatter Charts

v3 automatically applies color to Scatter tooltip entries. If you relied on no color, override with `tooltipType="none"`.

### Keyboard Events

v3: keyboard navigation no longer triggers `onMouseMove`. If you depended on this, listen for keyboard events separately.

### Axis Lines

v3: X/Y axis lines display even when there are no ticks. To hide: `<XAxis axisLine={false} />`.

### Multiple Y Axes

v3: multiple Y axes render alphabetically by `yAxisId`, not by JSX order. To control order, use numeric `yAxisId` values.

### CartesianGrid

v3: requires explicit `xAxisId`/`yAxisId` matching axis components if you have multiple axes.

### Area connectNulls

v3: when `connectNulls={true}`, null data points convert to `0` (they bridge visually but affect the baseline).

### Legend Ordering

v3: no guaranteed legend order. If order matters, use a custom `content` renderer.

### SVG Layering

v3: render order in SVG determines visual layering. Use `zIndex` prop (v3.4+) to control explicitly.

### Default z-index Values

| Component | zIndex |
|:----------|:------:|
| CartesianGrid | -100 |
| PolarGrid | -100 |
| Area | 100 |
| ReferenceArea | 100 |
| Pie | 100 |
| Bar | 300 |
| RadialBar | 300 |
| Line | 400 |
| ReferenceLine | 400 |
| ErrorBar | 400 |
| PolarAngleAxis | 500 |
| PolarRadiusAxis | 500 |
| Scatter | 600 |
| ReferenceDot | 600 |
| Label | 2000 |
| LabelList | 2000 |

## Type Changes

| v2 | v3 | Notes |
|:---|:---|:------|
| `TooltipProps` | `TooltipContentProps` | For custom tooltip content components |
| `TooltipProps.label: string` | `label: undefined \| string \| number` | Broader type |
| `Sankey` types | Stricter | Validate SankeyData structure |
| `ResponsiveContainer` ref | Flat `ref.current` | Was nested `ref.current.current` in v2 |

## Removed Dependencies

| Dependency | Status | v3 Equivalent |
|:-----------|:-------|:--------------|
| `recharts-scale` | Removed | `getNiceTickValues` from recharts |
| `react-smooth` | Removed | Internal animation system |

If you imported from `recharts-scale` directly:

```tsx
// v2
import { getNiceTickValues } from 'recharts-scale';

// v3
import { getNiceTickValues } from 'recharts';
```

## New Features by Version

### v3.0.0 (Jun 2025)

- `accessibilityLayer` defaults to `true`
- Hooks API: `useChartWidth`, `useChartHeight`, `useActiveTooltipLabel`
- Tooltip `portal` prop for custom DOM location
- Tooltip `axisId` prop to select which axis tooltip follows
- Direct custom components in charts (no `<Customized>` wrapper)
- `isAnimationActive="auto"` respects `prefers-reduced-motion` and SSR
- Internal animation engine (no `react-smooth`)
- YAxis `width="auto"` — auto-calculated width

### v3.1.0

- `usePlotArea` hook returns `{x, y, width, height}`

### v3.3.0 (Oct 2025)

- `responsive` prop on all charts — built-in ResponsiveContainer replacement
- `width` and `height` accept percentage strings when `responsive={true}`

### v3.4.0 (Nov 2025)

- `zIndex` prop on all series and reference components
- `ZIndexLayer` and `DefaultZIndexes` for layer management
- `Line` gets `shape` prop for custom point rendering
- Sankey `align` and `verticalAlign` props

### v3.5.0 (Nov 2025)

- `Pie` gets `shape` prop with `isActive` boolean
- `activeShape` and `inactiveShape` deprecated
- `reverseStackOrder` prop

### v3.6.0 (Dec 2025)

- `BarStack` component for grouped stacked bars with shared `radius`
- Ranged stacked bar support

### v3.7.0 (Jan 2026)

- `Cell` component deprecated (removal in v4.0)
- `useIsTooltipActive` hook
- `useActiveTooltipCoordinate` hook
- XAxis/YAxis `type="auto"` — automatic type detection

### v3.8.0 (Mar 2026)

- TypeScript generics for `data` and `dataKey` props
- `niceTicks` prop: `"auto"`, `"none"`, `"adaptive"`, `"snap125"`
- Scale hooks: `useXAxisScale`, `useYAxisScale`, `useXAxisInverseScale`, `useYAxisInverseScale`
- Inverse data/tick snap scale hooks

### v3.8.1 (Mar 2026)

- Tooltip flicker fix
- Memory leak fix in animation cleanup

## Migration Checklist

1. **Update dependencies**:
   ```bash
   npm install recharts@latest
   npm uninstall @types/recharts  # if installed
   ```

2. **Update tsconfig.json**:
   ```json
   { "compilerOptions": { "target": "ES6" } }
   ```

3. **Search and replace**:
   - `activeIndex` → remove (use Tooltip)
   - `blendStroke` → `stroke="none"`
   - `alwaysShow` → remove
   - `isFront` → remove
   - `animateNewValues` → remove
   - `activeShape=` → `shape=` with `isActive` check
   - `inactiveShape=` → merge into `shape=`
   - `<Customized>` → direct child component + hooks
   - `<Cell` → `shape` prop (non-urgent, Cell works until v4.0)
   - `import { getNiceTickValues } from 'recharts-scale'` → from `'recharts'`

4. **Check behavior**:
   - Accessibility layer is now ON by default
   - Multiple Y axes may render in different order
   - CartesianGrid needs matching axis IDs
   - Area `connectNulls` null→0 conversion

5. **Type fixes**:
   - Custom tooltip: use `TooltipContentProps` (not `TooltipProps`)
   - Check `label` type is `string | number | undefined`
   - Validate Sankey data types

6. **Test**:
   - Visual regression test all charts
   - Verify keyboard navigation works
   - Test SSR/hydration
   - Check animation behavior with `prefers-reduced-motion`
