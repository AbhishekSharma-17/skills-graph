# Recharts Overview

> Source: [recharts.org](https://recharts.org) | [GitHub](https://github.com/recharts/recharts)

## What Is Recharts

Recharts is a composable charting library for React built on top of D3. It renders native SVG elements and uses a declarative component-based API. Charts are composed by nesting child components (axes, series, tooltips) inside a parent chart component.

Key characteristics:
- **Declarative**: compose charts from React components, not imperative API calls
- **Native SVG**: all chart elements are standard SVG — style with CSS, inspect in DevTools
- **Composable**: mix and match Line, Bar, Area, Scatter in a single ComposedChart
- **TypeScript-first**: ships its own types (no `@types/recharts` needed in v3)
- **Accessible**: keyboard navigation and screen reader support enabled by default in v3

## Installation

```bash
npm install recharts
# or
yarn add recharts
# or
pnpm add recharts
```

**Peer dependencies**: `react >=16.8`, `react-dom >=16`, `react-is >=16.8`

**v3 minimum requirements**: React 16.8+, TypeScript 5.x+, Node.js v18+, TS target ES6

## Quick Start

```tsx
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';

const data = [
  { month: 'Jan', revenue: 4000 },
  { month: 'Feb', revenue: 3000 },
  { month: 'Mar', revenue: 5000 },
  { month: 'Apr', revenue: 4500 },
  { month: 'May', revenue: 6000 },
];

function RevenueChart() {
  return (
    <LineChart width={600} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="revenue" stroke="#8884d8" strokeWidth={2} />
    </LineChart>
  );
}
```

## Chart Types

Recharts provides 12 chart types in three categories:

### Cartesian Charts (x/y axes)
| Component | Use Case |
|:----------|:---------|
| `LineChart` | Trends over time, continuous data |
| `BarChart` | Categorical comparisons |
| `AreaChart` | Trends with volume emphasis |
| `ComposedChart` | Overlay Line + Bar + Area + Scatter |
| `ScatterChart` | Correlation between two variables |
| `FunnelChart` | Conversion funnels |

### Polar Charts (circular layout)
| Component | Use Case |
|:----------|:---------|
| `PieChart` | Proportional distribution |
| `RadarChart` | Multi-variable comparison |
| `RadialBarChart` | Radial progress bars |

### Hierarchical Charts
| Component | Use Case |
|:----------|:---------|
| `Treemap` | Nested hierarchical data as rectangles |
| `SunburstChart` | Hierarchical data as concentric rings |
| `Sankey` | Flow/transfer between categories |

## Architecture

Every Recharts chart follows the same pattern:

```
<ChartType>           ← Parent container (data, dimensions)
  <CartesianGrid />   ← Background grid
  <XAxis />           ← Axes
  <YAxis />
  <Tooltip />         ← Interactive overlay (HTML, not SVG)
  <Legend />           ← Series legend (HTML, not SVG)
  <Series />          ← Data series (Line, Bar, Area, Pie, etc.)
  <ReferenceLine />   ← Optional annotations
</ChartType>
```

The parent chart component owns the `data` prop. Child series components reference fields via `dataKey`. Tooltip and Legend are HTML elements rendered via React Portal — they sit above the SVG layer.

## Common Chart-Level Props

All Cartesian charts share these props:

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `width` | `number \| string` | — | Chart width (px or %) |
| `height` | `number \| string` | — | Chart height (px or %) |
| `data` | `Array<object>` | — | Data array |
| `margin` | `{top, right, bottom, left}` | `{5,5,5,5}` | Internal padding |
| `layout` | `"horizontal" \| "vertical"` | `"horizontal"` | Axis orientation |
| `responsive` | `boolean` | `false` | Built-in responsive mode (v3.3+) |
| `accessibilityLayer` | `boolean` | `true` | Keyboard + screen reader (v3) |
| `syncId` | `string \| number` | — | Sync tooltip/brush across charts |

## Data Format

Recharts expects a flat array of objects. Each object is one data point:

```ts
const data = [
  { name: 'Page A', uv: 4000, pv: 2400, amt: 2400 },
  { name: 'Page B', uv: 3000, pv: 1398, amt: 2210 },
];
```

Series components use `dataKey` to select which field to render:

```tsx
<BarChart data={data}>
  <Bar dataKey="uv" fill="#8884d8" />
  <Bar dataKey="pv" fill="#82ca9d" />
</BarChart>
```

## Responsive Charts

Two approaches in v3:

```tsx
// Approach 1: ResponsiveContainer wrapper (classic)
import { ResponsiveContainer, LineChart, Line } from 'recharts';

<ResponsiveContainer width="100%" height={400}>
  <LineChart data={data}>
    <Line dataKey="value" />
  </LineChart>
</ResponsiveContainer>

// Approach 2: Built-in responsive prop (v3.3+)
<LineChart data={data} responsive width="100%" height={400}>
  <Line dataKey="value" />
</LineChart>
```

**Critical**: `ResponsiveContainer` requires its parent element to have defined dimensions. If the parent has no height, the chart won't render.

## Event Handling

All charts support mouse and touch events:

```tsx
<LineChart
  data={data}
  onClick={(e) => console.log('clicked', e.activePayload)}
  onMouseMove={(e) => console.log('hover', e.activeLabel)}
>
  <Line
    dataKey="value"
    onClick={(data, index) => console.log('line clicked', data)}
  />
</LineChart>
```

Chart-level events: `onClick`, `onMouseDown`, `onMouseUp`, `onMouseMove`, `onMouseEnter`, `onMouseLeave`, `onTouchStart`, `onTouchMove`, `onTouchEnd`

## What Changed in v3

Key improvements over v2:
- `accessibilityLayer` defaults to `true` — keyboard and screen reader support
- Built-in `responsive` prop on all charts (no wrapper needed)
- YAxis `width="auto"` — auto-calculated width
- Hooks API for accessing chart internals from custom components
- `Cell` component deprecated — use `shape` prop instead
- `react-smooth` dependency removed — animations are internal
- TypeScript generics for type-safe `data` and `dataKey` (v3.8+)
- `isAnimationActive="auto"` respects `prefers-reduced-motion` and SSR

See `references/12-migration-v3.md` for the full migration guide.
