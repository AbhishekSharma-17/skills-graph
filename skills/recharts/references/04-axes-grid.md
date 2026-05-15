# Axes & Grid

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [XAxis](#xaxis)
- [YAxis](#yaxis)
- [ZAxis](#zaxis)
- [CartesianGrid](#cartesiangrid)
- [Domain Configuration](#domain-configuration)
- [Scale Types](#scale-types)
- [Tick Configuration](#tick-configuration)
- [Common Patterns](#common-patterns)

## XAxis

Horizontal axis for Cartesian charts.

```tsx
<XAxis
  dataKey="name"
  type="category"
  tickFormatter={(value) => value.substring(0, 3)}
  angle={-45}
  textAnchor="end"
  height={60}
/>
```

### XAxis Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string` | — | Data field for tick values |
| `type` | `"category" \| "number" \| "auto"` | `"category"` | Axis data type (`"auto"` in v3.7+) |
| `domain` | `array` | auto | Value range (see Domain Config) |
| `orientation` | `"bottom" \| "top"` | `"bottom"` | Position |
| `ticks` | `array` | — | Manual tick values |
| `tickCount` | `number` | `5` | Number of ticks (number type only) |
| `tickFormatter` | `function` | — | Transform tick labels |
| `tick` | `bool \| object \| function` | `true` | Tick label appearance |
| `tickLine` | `bool \| object` | `true` | Tick mark lines |
| `tickSize` | `number` | `6` | Tick mark length |
| `tickMargin` | `number` | — | Gap between tick and label |
| `axisLine` | `bool \| object` | `true` | Axis line |
| `scale` | `string` | `"auto"` | Scale function (see Scale Types) |
| `niceTicks` | `string` | `"auto"` | Tick algorithm (v3.8+) |
| `interval` | `number \| string` | `"preserveEnd"` | Tick display interval |
| `minTickGap` | `number` | `5` | Minimum px between ticks |
| `angle` | `number` | — | Rotate tick labels (degrees) |
| `padding` | `object \| string` | `{left:0,right:0}` | Inner padding (`"gap"` or `"no-gap"`) |
| `reversed` | `boolean` | `false` | Reverse axis direction |
| `mirror` | `boolean` | `false` | Mirror ticks to other side |
| `allowDataOverflow` | `boolean` | `false` | Clip data outside domain |
| `allowDecimals` | `boolean` | `true` | Allow decimal ticks |
| `allowDuplicatedCategory` | `boolean` | `true` | Allow duplicate category values |
| `includeHidden` | `boolean` | `false` | Include hidden series in domain (v3+) |
| `hide` | `boolean` | `false` | Hide entire axis |
| `height` | `number` | `30` | Axis height |
| `label` | `string \| object \| ReactNode` | — | Axis label |
| `name` | `string` | — | Name for tooltip display |
| `unit` | `string` | — | Unit suffix for tooltip |
| `xAxisId` | `string \| number` | `0` | Axis identifier |

**interval options**:
- `0` — show every tick
- `"preserveStart"` — always show first tick, auto-skip others
- `"preserveEnd"` — always show last tick, auto-skip others (default)
- A number `n` — show every nth tick

## YAxis

Vertical axis. Mostly identical to XAxis with these differences:

| Prop | Default (differs from XAxis) |
|:-----|:-----------------------------|
| `type` | `"number"` (XAxis: `"category"`) |
| `orientation` | `"left"` (or `"right"`) |
| `width` | `60` (supports `"auto"` in v3+) |
| `padding` | `{top:0, bottom:0}` |
| `yAxisId` | `0` |

```tsx
// Auto-width YAxis (v3+)
<YAxis width="auto" />

// Right-side YAxis
<YAxis yAxisId="right" orientation="right" />

// Formatted YAxis
<YAxis tickFormatter={(value) => `$${value.toLocaleString()}`} />
```

## ZAxis

Virtual axis — controls Scatter point size. Renders no visual elements.

```tsx
<ScatterChart>
  <XAxis type="number" dataKey="x" />
  <YAxis type="number" dataKey="y" />
  <ZAxis type="number" dataKey="z" range={[60, 400]} />
  <Scatter data={data} fill="#8884d8" />
</ScatterChart>
```

| Prop | Type | Default |
|:-----|:-----|:--------|
| `dataKey` | `string` | — |
| `type` | `"number" \| "category"` | `"number"` |
| `range` | `[min, max]` | `[64, 64]` |
| `domain` | `array` | auto |
| `zAxisId` | `string \| number` | `0` |

## CartesianGrid

Background grid lines.

```tsx
// Basic grid
<CartesianGrid strokeDasharray="3 3" />

// Striped background
<CartesianGrid
  horizontalFill={['#f5f5f5', '#fff']}
  verticalFill={['#f5f5f5', '#fff']}
  fillOpacity={0.5}
/>

// Grid aligned to ticks only
<CartesianGrid syncWithTicks />
```

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `horizontal` | `boolean` | `true` | Show horizontal lines |
| `vertical` | `boolean` | `true` | Show vertical lines |
| `horizontalFill` | `string[]` | — | Alternating row colors |
| `verticalFill` | `string[]` | — | Alternating column colors |
| `horizontalValues` | `array` | — | Draw lines at specific data values |
| `verticalValues` | `array` | — | Draw lines at specific data values |
| `syncWithTicks` | `boolean` | `false` | Align grid to tick positions |
| `fill` | `string` | `"none"` | Background fill |
| `fillOpacity` | `number` | — | Fill transparency |
| `strokeDasharray` | `string` | — | Dash pattern (e.g., `"3 3"`) |
| `stroke` | `string` | — | Line color |
| `xAxisId` | `string \| number` | `0` | Match to XAxis |
| `yAxisId` | `string \| number` | `0` | Match to YAxis |
| `zIndex` | `number` | `-100` | Layer order |

## Domain Configuration

The `domain` prop on XAxis/YAxis controls the value range. Multiple formats:

```tsx
// Fixed range
<YAxis domain={[0, 100]} />

// Data-driven
<YAxis domain={['dataMin', 'dataMax']} />

// Data-driven with padding
<YAxis domain={['dataMin - 100', 'dataMax + 100']} />

// Function-based
<YAxis domain={[
  (dataMin) => Math.floor(dataMin / 10) * 10,
  (dataMax) => Math.ceil(dataMax / 10) * 10,
]} />

// Auto nice ticks
<YAxis domain={['auto', 'auto']} />

// Mixed
<YAxis domain={[0, 'dataMax + 1000']} />

// Full domain function
<YAxis domain={(domainArray) => [domainArray[0] - 10, domainArray[1] + 10]} />
```

**Important**: `domain` only works when `type="number"`. For category axes, domain is the list of category values.

## Scale Types

The `scale` prop supports 20+ D3 scale types:

| Scale | Use Case |
|:------|:---------|
| `"auto"` | Auto-detect (default) |
| `"linear"` | Uniform numeric |
| `"log"` | Exponential data |
| `"pow"` | Power scale |
| `"sqrt"` | Square root |
| `"symlog"` | Symmetric log (handles negatives) |
| `"time"` | Date/time data |
| `"utc"` | UTC time |
| `"band"` | Equal-width bands (categories) |
| `"point"` | Points at equal intervals |
| `"ordinal"` | Discrete unordered |
| `"identity"` | 1:1 mapping |
| `"quantile"` | Quantile bins |
| `"quantize"` | Equal-range bins |
| `"threshold"` | Custom breakpoints |
| `"sequential"` | Sequential color |
| `"diverging"` | Diverging color |

**Log scale example**:

```tsx
<YAxis scale="log" domain={[1, 10000]} allowDataOverflow />
```

## Tick Configuration

### niceTicks (v3.8+)

Controls the tick value generation algorithm:

| Value | Behavior |
|:------|:---------|
| `"auto"` | Default algorithm |
| `"none"` | Use domain endpoints exactly |
| `"adaptive"` | Adaptive nice values |
| `"snap125"` | Snap to 1-2-5 intervals |

### Custom Tick Component

```tsx
const CustomTick = ({ x, y, payload }) => (
  <g transform={`translate(${x},${y})`}>
    <text x={0} y={0} dy={16} textAnchor="middle" fill="#666" fontSize={12}>
      {payload.value}
    </text>
  </g>
);

<XAxis tick={<CustomTick />} />
```

### Rotated Ticks

```tsx
<XAxis
  dataKey="name"
  angle={-45}
  textAnchor="end"
  height={80}
  interval={0}
/>
```

### Formatted Ticks

```tsx
// Currency
<YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />

// Date
<XAxis
  dataKey="date"
  type="number"
  domain={['dataMin', 'dataMax']}
  tickFormatter={(ts) => new Date(ts).toLocaleDateString()}
/>

// Percentage
<YAxis tickFormatter={(value) => `${value}%`} />
```

## Common Patterns

### Dual Axes

```tsx
<ComposedChart data={data}>
  <XAxis dataKey="month" />
  <YAxis yAxisId="left" tickFormatter={(v) => `$${v}`} />
  <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `${v}%`} />
  <CartesianGrid strokeDasharray="3 3" />
  <Bar yAxisId="left" dataKey="revenue" fill="#8884d8" />
  <Line yAxisId="right" dataKey="growth" stroke="#ff7300" />
</ComposedChart>
```

### Time Series

```tsx
const data = [
  { date: new Date('2024-01-01').getTime(), value: 100 },
  { date: new Date('2024-02-01').getTime(), value: 200 },
];

<LineChart data={data}>
  <XAxis
    dataKey="date"
    type="number"
    scale="time"
    domain={['dataMin', 'dataMax']}
    tickFormatter={(ts) => new Intl.DateTimeFormat('en', { month: 'short' }).format(ts)}
  />
  <YAxis />
  <Line dataKey="value" />
</LineChart>
```

### Hidden Axes (Sparkline)

```tsx
<LineChart width={200} height={40} data={data}>
  <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} dot={false} />
</LineChart>
```

### Grid Only at Specific Values

```tsx
<CartesianGrid horizontalValues={[0, 50, 100]} verticalValues={['Mon', 'Wed', 'Fri']} />
```
