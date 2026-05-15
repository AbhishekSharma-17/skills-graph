# Stacking & Responsive Layout

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [Stacking](#stacking)
- [stackOffset Modes](#stackoffset-modes)
- [BarStack Component](#barstack-component)
- [ResponsiveContainer](#responsivecontainer)
- [Built-in Responsive Prop](#built-in-responsive-prop)
- [Layout Direction](#layout-direction)

## Stacking

Assign the same `stackId` to multiple Bar or Area components to stack them. Different `stackId` values create separate stack groups.

```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const data = [
  { month: 'Jan', direct: 4000, organic: 2400, referral: 1200 },
  { month: 'Feb', direct: 3000, organic: 1398, referral: 900 },
  { month: 'Mar', direct: 2000, organic: 9800, referral: 1600 },
];

<BarChart data={data}>
  <XAxis dataKey="month" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Bar dataKey="direct" stackId="traffic" fill="#8884d8" />
  <Bar dataKey="organic" stackId="traffic" fill="#82ca9d" />
  <Bar dataKey="referral" stackId="traffic" fill="#ffc658" />
</BarChart>
```

### Stacked Areas

```tsx
import { AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

<AreaChart data={data}>
  <XAxis dataKey="month" />
  <YAxis />
  <Tooltip />
  <Area type="monotone" dataKey="direct" stackId="1" stroke="#8884d8" fill="#8884d8" />
  <Area type="monotone" dataKey="organic" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
  <Area type="monotone" dataKey="referral" stackId="1" stroke="#ffc658" fill="#ffc658" />
</AreaChart>
```

### Mixed Stacked and Unstacked

```tsx
<BarChart data={data}>
  <Bar dataKey="a" stackId="group1" fill="#8884d8" />
  <Bar dataKey="b" stackId="group1" fill="#82ca9d" />
  <Bar dataKey="c" fill="#ffc658" />  {/* Unstacked, separate column */}
</BarChart>
```

## stackOffset Modes

Set on the parent chart component to control how stacked values are computed.

```tsx
<BarChart data={data} stackOffset="expand">
  <Bar dataKey="a" stackId="s" fill="#8884d8" />
  <Bar dataKey="b" stackId="s" fill="#82ca9d" />
</BarChart>
```

| Value | Behavior | Use Case |
|:------|:---------|:---------|
| `"none"` | Simple additive stacking (default) | Standard stacked chart |
| `"expand"` | Normalize to 0–1 range (100% stacking) | Percentage distribution |
| `"sign"` | Positive values stack up, negative stack down | Profit/loss |
| `"positive"` | Only positive values stacked | Revenue-only view |
| `"silhouette"` | Centered around zero (symmetric) | ThemeRiver / streamgraph |
| `"wiggle"` | Minimizes weighted change (streamgraph) | Smooth streamgraph |

### 100% Stacked Bar Chart

```tsx
<BarChart data={data} stackOffset="expand">
  <XAxis dataKey="month" />
  <YAxis tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
  <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
  <Bar dataKey="direct" stackId="a" fill="#8884d8" />
  <Bar dataKey="organic" stackId="a" fill="#82ca9d" />
  <Bar dataKey="referral" stackId="a" fill="#ffc658" />
</BarChart>
```

### Streamgraph

```tsx
<AreaChart data={data} stackOffset="wiggle">
  <Area type="monotone" dataKey="a" stackId="1" stroke="#8884d8" fill="#8884d8" />
  <Area type="monotone" dataKey="b" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
  <Area type="monotone" dataKey="c" stackId="1" stroke="#ffc658" fill="#ffc658" />
</AreaChart>
```

### reverseStackOrder

When `true`, renders stacked items in reverse SVG order. Affects which item appears on top visually.

```tsx
<BarChart data={data} reverseStackOrder>
  <Bar dataKey="a" stackId="s" fill="#8884d8" />
  <Bar dataKey="b" stackId="s" fill="#82ca9d" />
</BarChart>
```

## BarStack Component

Added in v3.6. Groups stacked bars and supports shared `radius` on the stack group — not possible with individual `stackId`.

```tsx
import { BarChart, Bar, BarStack, XAxis, YAxis } from 'recharts';

<BarChart data={data}>
  <XAxis dataKey="month" />
  <YAxis />
  <BarStack stackId="a" radius={[10, 10, 0, 0]}>
    <Bar dataKey="direct" fill="#8884d8" />
    <Bar dataKey="organic" fill="#82ca9d" />
    <Bar dataKey="referral" fill="#ffc658" />
  </BarStack>
</BarChart>
```

The `radius` applies to the outermost bar in the stack, producing rounded top corners on the full stacked column.

## ResponsiveContainer

Wrapper that makes charts responsive to their parent's dimensions using ResizeObserver.

```tsx
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis } from 'recharts';

<div style={{ width: '100%', height: 400 }}>
  <ResponsiveContainer>
    <LineChart data={data}>
      <XAxis dataKey="name" />
      <YAxis />
      <Line dataKey="value" />
    </LineChart>
  </ResponsiveContainer>
</div>
```

### ResponsiveContainer Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `width` | `number \| string` | `"100%"` | Container width |
| `height` | `number \| string` | `"100%"` | Container height |
| `aspect` | `number` | — | Width/height ratio (overrides height) |
| `minWidth` | `number` | `0` | Minimum width |
| `minHeight` | `number` | — | Minimum height |
| `maxHeight` | `number` | — | Maximum height |
| `debounce` | `number` | `0` | Resize debounce (ms) |
| `initialDimension` | `{width, height}` | `{-1, -1}` | Initial size before first measure |
| `onResize` | `function` | — | Callback: `(width, height)` |

**Supports all 12 chart types**: AreaChart, BarChart, ComposedChart, FunnelChart, LineChart, PieChart, RadarChart, RadialBarChart, Sankey, ScatterChart, SunburstChart, Treemap.

### Common Gotchas

**Parent must have defined dimensions**. The most common issue:

```tsx
// BAD: parent has no height
<div>
  <ResponsiveContainer>
    <LineChart data={data}><Line dataKey="value" /></LineChart>
  </ResponsiveContainer>
</div>

// GOOD: parent has explicit height
<div style={{ height: 400 }}>
  <ResponsiveContainer>
    <LineChart data={data}><Line dataKey="value" /></LineChart>
  </ResponsiveContainer>
</div>

// GOOD: parent uses flex
<div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
  <div style={{ flex: 1 }}>
    <ResponsiveContainer>
      <LineChart data={data}><Line dataKey="value" /></LineChart>
    </ResponsiveContainer>
  </div>
</div>
```

### Aspect Ratio

Lock the aspect ratio — height is calculated from width:

```tsx
<ResponsiveContainer width="100%" aspect={16 / 9}>
  <LineChart data={data}><Line dataKey="value" /></LineChart>
</ResponsiveContainer>
```

### Debounced Resize

```tsx
<ResponsiveContainer debounce={300} onResize={(w, h) => console.log(w, h)}>
  <LineChart data={data}><Line dataKey="value" /></LineChart>
</ResponsiveContainer>
```

## Built-in Responsive Prop

Added in v3.3 as a simpler alternative to ResponsiveContainer.

```tsx
<LineChart data={data} responsive width="100%" height={400}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line dataKey="value" />
</LineChart>
```

When `responsive={true}`:
- Chart adapts to parent dimensions
- `width` and `height` accept percentage strings
- No wrapper component needed
- Uses the same ResizeObserver internally

## Layout Direction

### Horizontal (Default)

Standard orientation — X axis horizontal, Y axis vertical:

```tsx
<BarChart layout="horizontal" data={data}>
  <XAxis type="category" dataKey="name" />
  <YAxis type="number" />
  <Bar dataKey="value" />
</BarChart>
```

### Vertical

Rotated — X axis becomes numeric (horizontal), Y axis becomes categorical (vertical):

```tsx
<BarChart layout="vertical" data={data}>
  <XAxis type="number" />
  <YAxis type="category" dataKey="name" width={100} />
  <Bar dataKey="value" fill="#8884d8" />
</BarChart>
```

Common for horizontal bar charts (ranking lists, comparison charts).

### Margin

Fine-tune spacing around the chart area:

```tsx
<LineChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 40 }}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line dataKey="value" />
</LineChart>
```

Increase `left` margin when YAxis labels are long (e.g., currency values). Increase `bottom` margin when XAxis labels are rotated.
