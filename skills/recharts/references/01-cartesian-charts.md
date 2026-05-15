# Cartesian Charts

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [LineChart](#linechart)
- [Line Component Props](#line-component-props)
- [BarChart](#barchart)
- [Bar Component Props](#bar-component-props)
- [AreaChart](#areachart)
- [Area Component Props](#area-component-props)
- [ComposedChart](#composedchart)
- [ScatterChart](#scatterchart)
- [Scatter Component Props](#scatter-component-props)
- [Shared Chart Props](#shared-chart-props)
- [Curve Types](#curve-types)

## LineChart

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const data = [
  { name: 'Mon', sales: 4000, orders: 2400 },
  { name: 'Tue', sales: 3000, orders: 1398 },
  { name: 'Wed', sales: 2000, orders: 9800 },
  { name: 'Thu', sales: 2780, orders: 3908 },
  { name: 'Fri', sales: 1890, orders: 4800 },
];

<LineChart width={730} height={300} data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line type="monotone" dataKey="sales" stroke="#8884d8" />
  <Line type="monotone" dataKey="orders" stroke="#82ca9d" />
</LineChart>
```

### Line Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string \| number` | required | Field in data objects |
| `type` | `CurveType` | `"linear"` | Interpolation curve (see Curve Types) |
| `stroke` | `string` | `"#3182bd"` | Line color |
| `strokeWidth` | `number` | `1` | Line thickness |
| `strokeDasharray` | `string` | — | Dash pattern (e.g., `"5 5"`) |
| `dot` | `bool \| object \| function \| ReactNode` | `true` | Data point markers |
| `activeDot` | `bool \| object \| function \| ReactNode` | `true` | Hover state dot |
| `connectNulls` | `boolean` | `false` | Bridge over null values |
| `label` | `bool \| object \| function \| ReactNode` | `false` | Data point labels |
| `legendType` | `string` | `"line"` | Shape in legend |
| `hide` | `boolean` | `false` | Hide series but keep in tooltip |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Enable animation |
| `animationDuration` | `number` | `1500` | Duration in ms |
| `animationEasing` | `string \| function` | `"ease"` | Easing function |
| `xAxisId` | `string \| number` | `0` | Which XAxis to use |
| `yAxisId` | `string \| number` | `0` | Which YAxis to use |
| `zIndex` | `number` | `400` | SVG layer order |

## BarChart

```tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<BarChart width={730} height={300} data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Bar dataKey="sales" fill="#8884d8" />
  <Bar dataKey="orders" fill="#82ca9d" />
</BarChart>
```

### Bar-Specific Chart Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `barGap` | `number \| string` | `4` | Gap between bars in same category |
| `barCategoryGap` | `number \| string` | `"10%"` | Gap between categories |
| `barSize` | `number \| string` | auto | Bar width |
| `maxBarSize` | `number` | — | Maximum bar dimension |
| `stackOffset` | `string` | `"none"` | Stacking strategy |
| `reverseStackOrder` | `boolean` | `false` | Reverse SVG layering |

### Bar Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string \| number` | required | Field in data objects |
| `fill` | `string` | — | Bar fill color |
| `radius` | `number \| [tl, tr, br, bl]` | — | Corner radius |
| `barSize` | `number \| string` | — | Override chart-level barSize |
| `stackId` | `string \| number` | — | Group bars for stacking |
| `background` | `bool \| object \| function \| ReactElement` | `false` | Background fill |
| `shape` | `function \| ReactElement` | — | Custom bar shape |
| `activeBar` | `bool \| object \| function \| ReactElement` | `false` | Hover state |
| `label` | `bool \| object \| function \| ReactNode` | `false` | Bar labels |
| `minPointSize` | `number \| function` | `0` | Minimum bar height |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Enable animation |
| `animationDuration` | `number` | `400` | Duration in ms |
| `zIndex` | `number` | `300` | SVG layer order |

**Stacking bars**:

```tsx
<BarChart data={data}>
  <Bar dataKey="a" stackId="stack1" fill="#8884d8" />
  <Bar dataKey="b" stackId="stack1" fill="#82ca9d" />
  <Bar dataKey="c" fill="#ffc658" /> {/* Separate, unstacked */}
</BarChart>
```

## AreaChart

```tsx
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

<AreaChart width={730} height={300} data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Area type="monotone" dataKey="sales" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
</AreaChart>
```

### Area Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string \| number` | required | Field in data objects |
| `type` | `CurveType` | `"linear"` | Interpolation curve |
| `stroke` | `string` | `"#3182bd"` | Border color |
| `fill` | `string` | auto-generated | Fill color |
| `fillOpacity` | `number` | — | Fill transparency |
| `stackId` | `string \| number` | — | Group for stacking |
| `baseValue` | `"dataMax" \| "dataMin" \| number` | — | Baseline for fill |
| `dot` | `bool \| object \| function \| ReactNode` | `false` | Data point markers |
| `activeDot` | `bool \| object \| function \| ReactNode` | `true` | Hover state dot |
| `connectNulls` | `boolean` | `false` | Bridge null values |
| `label` | `bool \| object \| function \| ReactNode` | `false` | Data point labels |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Enable animation |
| `animationDuration` | `number` | `1500` | Duration in ms |
| `zIndex` | `number` | `100` | SVG layer order |

**Gradient fill**:

```tsx
<AreaChart data={data}>
  <defs>
    <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
      <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
      <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
    </linearGradient>
  </defs>
  <Area type="monotone" dataKey="uv" stroke="#8884d8" fill="url(#colorUv)" />
</AreaChart>
```

## ComposedChart

Overlay multiple series types in one chart:

```tsx
import { ComposedChart, Area, Bar, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';

<ComposedChart width={730} height={300} data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Area type="monotone" dataKey="amt" fill="#8884d8" stroke="#8884d8" />
  <Bar dataKey="pv" barSize={20} fill="#413ea0" />
  <Line type="monotone" dataKey="uv" stroke="#ff7300" />
</ComposedChart>
```

ComposedChart accepts Area, Bar, Line, and Scatter as children simultaneously. All share the same axes and data array.

## ScatterChart

```tsx
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip } from 'recharts';

const scatterData = [
  { x: 100, y: 200, z: 200 },
  { x: 120, y: 100, z: 260 },
  { x: 170, y: 300, z: 400 },
];

<ScatterChart width={730} height={300}>
  <XAxis type="number" dataKey="x" name="weight" unit="kg" />
  <YAxis type="number" dataKey="y" name="height" unit="cm" />
  <ZAxis type="number" dataKey="z" range={[60, 400]} name="score" />
  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
  <Scatter name="People" data={scatterData} fill="#8884d8" />
</ScatterChart>
```

### Scatter Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `data` | `Array<object>` | — | Scatter-specific data (overrides chart data) |
| `dataKey` | `string \| number` | — | Maps to y-axis value |
| `shape` | `string \| function \| ReactElement` | `"circle"` | Point shape |
| `legendType` | `string` | `"rect"` | Shape in legend |
| `line` | `bool \| object \| function \| ReactElement` | `false` | Connect points |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Enable animation |
| `animationDuration` | `number` | `400` | Duration in ms |
| `zIndex` | `number` | `600` | SVG layer order |

Note: `ZAxis` is a virtual axis — it controls Scatter point size via `range` but renders no visual axis.

## Shared Chart Props

All Cartesian charts (LineChart, BarChart, AreaChart, ComposedChart, ScatterChart, FunnelChart) share:

| Prop | Type | Default |
|:-----|:-----|:--------|
| `width` | `number \| string` | — |
| `height` | `number \| string` | — |
| `data` | `Array<object>` | — |
| `layout` | `"horizontal" \| "vertical"` | `"horizontal"` |
| `margin` | `{top, right, bottom, left}` | `{5,5,5,5}` |
| `responsive` | `boolean` | `false` |
| `syncId` | `string \| number` | — |
| `syncMethod` | `"index" \| "value" \| function` | `"index"` |
| `accessibilityLayer` | `boolean` | `true` |
| `throttleDelay` | `"raf" \| number` | `"raf"` |

**Vertical layout** swaps axis roles:

```tsx
<BarChart layout="vertical" data={data}>
  <XAxis type="number" />
  <YAxis type="category" dataKey="name" />
  <Bar dataKey="value" fill="#8884d8" />
</BarChart>
```

## Curve Types

The `type` prop on Line and Area accepts these interpolation methods:

| Type | Description |
|:-----|:------------|
| `"linear"` | Straight segments (default) |
| `"monotone"` | Smooth curve preserving monotonicity |
| `"monotoneX"` | Monotone in x |
| `"monotoneY"` | Monotone in y |
| `"natural"` | Natural cubic spline |
| `"basis"` | B-spline |
| `"basisOpen"` | Open B-spline |
| `"basisClosed"` | Closed B-spline |
| `"bump"` | Bumped curve |
| `"bumpX"` | Horizontal bump |
| `"bumpY"` | Vertical bump |
| `"step"` | Step function (midpoint) |
| `"stepBefore"` | Step before point |
| `"stepAfter"` | Step after point |
| `"linearClosed"` | Closed linear |

You can also pass a D3 `CurveFactory` function for custom interpolation.

## Common Patterns

### Multiple Y Axes

```tsx
<ComposedChart data={data}>
  <XAxis dataKey="name" />
  <YAxis yAxisId="left" />
  <YAxis yAxisId="right" orientation="right" />
  <Line yAxisId="left" dataKey="revenue" stroke="#8884d8" />
  <Bar yAxisId="right" dataKey="orders" fill="#82ca9d" />
</ComposedChart>
```

### Negative Values

```tsx
<BarChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <ReferenceLine y={0} stroke="#000" />
  <Bar dataKey="profit" fill={(entry) => entry.profit >= 0 ? '#82ca9d' : '#ff6b6b'} />
</BarChart>
```

### Click-to-Select

```tsx
function InteractiveChart() {
  const [activeIndex, setActiveIndex] = useState(null);

  return (
    <BarChart data={data} onClick={(state) => {
      if (state) setActiveIndex(state.activeTooltipIndex);
    }}>
      <Bar dataKey="value" fill="#8884d8">
        {data.map((entry, index) => (
          <Cell key={index} fill={index === activeIndex ? '#ff7300' : '#8884d8'} />
        ))}
      </Bar>
    </BarChart>
  );
}
```

Note: `Cell` is deprecated in v3.7+. Prefer using the `shape` prop for per-bar customization.
