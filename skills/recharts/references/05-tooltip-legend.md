# Tooltip, Legend & Interactive Components

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [Tooltip](#tooltip)
- [Legend](#legend)
- [Brush](#brush)
- [Chart Synchronization](#chart-synchronization)

## Tooltip

Floating overlay that shows data values on hover or click. Renders as HTML (not SVG) via React Portal.

```tsx
import { LineChart, Line, Tooltip } from 'recharts';

<LineChart data={data}>
  <Line dataKey="value" />
  <Tooltip />
</LineChart>
```

### Tooltip Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `active` | `boolean \| undefined` | `undefined` | Force active state (undefined = auto) |
| `content` | `function \| ReactNode` | `DefaultTooltipContent` | Custom tooltip content |
| `formatter` | `function` | — | Transform values: returns `[formattedValue, formattedName]` |
| `labelFormatter` | `function` | — | Transform the axis label |
| `separator` | `string` | `" : "` | Between name and value |
| `trigger` | `"hover" \| "click"` | `"hover"` | Activation method |
| `shared` | `boolean` | — | Show all series at coordinate vs. individual |
| `cursor` | `bool \| object \| ReactNode` | `true` | Crosshair line |
| `position` | `{x, y}` | — | Fixed position (disables following mouse) |
| `offset` | `number` | `10` | Distance from cursor |
| `portal` | `HTMLElement` | — | Portal target for rendering (v3+) |
| `axisId` | `string \| number` | `0` | Which axis tooltip follows (v3+) |
| `defaultIndex` | `number` | — | Initial active data index |
| `filterNull` | `boolean` | `true` | Hide null values |
| `includeHidden` | `boolean` | `false` | Show hidden series |
| `itemSorter` | `string \| function` | `"name"` | Sort order (`"dataKey"`, `"name"`, `"value"`) |
| `allowEscapeViewBox` | `{x, y}` | `{x:false, y:false}` | Allow tooltip outside chart |
| `reverseDirection` | `{x, y}` | `{x:false, y:false}` | Flip tooltip side |
| `useTranslate3d` | `boolean` | `false` | Use GPU-accelerated positioning |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Animate transitions |
| `animationDuration` | `number` | `400` | Animation length in ms |
| `animationEasing` | `string` | `"ease"` | Easing function |

**Style props**: `contentStyle`, `labelStyle`, `itemStyle`, `wrapperStyle`, `wrapperClassName`, `labelClassName`

### Formatter

```tsx
<Tooltip
  formatter={(value, name, props) => [`$${value.toLocaleString()}`, name.toUpperCase()]}
  labelFormatter={(label) => `Month: ${label}`}
/>
```

The `formatter` function receives `(value, name, props)` and returns either:
- A single value (replaces the displayed value)
- An array `[formattedValue, formattedName]`

### Click-Triggered Tooltip

```tsx
<Tooltip trigger="click" />
```

### Fixed Position Tooltip

```tsx
<Tooltip position={{ x: 100, y: 50 }} />
```

### Cursor Customization

```tsx
// No cursor line
<Tooltip cursor={false} />

// Styled cursor
<Tooltip cursor={{ stroke: 'red', strokeWidth: 2 }} />

// Custom cursor component
<Tooltip cursor={<CustomCursorComponent />} />
```

## Legend

Chart legend showing series names and colors. Renders as HTML via React Portal.

```tsx
import { LineChart, Line, Legend } from 'recharts';

<LineChart data={data}>
  <Line dataKey="revenue" stroke="#8884d8" />
  <Line dataKey="profit" stroke="#82ca9d" />
  <Legend />
</LineChart>
```

### Legend Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `layout` | `"horizontal" \| "vertical"` | `"horizontal"` | Legend orientation |
| `align` | `"left" \| "center" \| "right"` | `"center"` | Horizontal alignment |
| `verticalAlign` | `"top" \| "middle" \| "bottom"` | `"bottom"` | Vertical alignment |
| `iconSize` | `number` | `14` | Icon dimensions |
| `iconType` | `string` | — | Override icon shape |
| `inactiveColor` | `string` | `"#ccc"` | Color for hidden series |
| `content` | `function \| ReactElement` | `DefaultLegendContent` | Custom renderer |
| `formatter` | `function` | — | Transform legend text |
| `itemSorter` | `string \| function` | `"value"` | Sort order |
| `portal` | `HTMLElement` | — | Portal target |
| `wrapperStyle` | `object` | — | Wrapper CSS |
| `width` | `number` | — | Fixed width |
| `height` | `number` | — | Fixed height |

**Event handlers**: `onClick`, `onMouseEnter`, `onMouseLeave`, `onBBoxUpdate`

### Interactive Legend (Toggle Series)

```tsx
function ChartWithToggle() {
  const [hidden, setHidden] = useState({});

  return (
    <LineChart data={data}>
      <Legend onClick={(e) => setHidden(prev => ({ ...prev, [e.dataKey]: !prev[e.dataKey] }))} />
      <Line dataKey="revenue" stroke="#8884d8" hide={hidden.revenue} />
      <Line dataKey="profit" stroke="#82ca9d" hide={hidden.profit} />
    </LineChart>
  );
}
```

### Legend Position

```tsx
// Top-left
<Legend align="left" verticalAlign="top" />

// Right side, vertical
<Legend layout="vertical" align="right" verticalAlign="middle" />
```

## Brush

Range selection slider for zooming into a subset of data.

```tsx
import { LineChart, Line, Brush, XAxis, YAxis } from 'recharts';

<LineChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line dataKey="value" />
  <Brush dataKey="name" height={30} stroke="#8884d8" />
</LineChart>
```

### Brush Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string` | — | Field for brush labels |
| `height` | `number` | `40` | Brush area height |
| `travellerWidth` | `number` | `5` | Handle width |
| `startIndex` | `number` | `0` | Initial start position |
| `endIndex` | `number` | data.length | Initial end position |
| `gap` | `number` | `1` | Points skipped between refreshes |
| `padding` | `{top,right,bottom,left}` | `{1,1,1,1}` | Internal padding |
| `leaveTimeOut` | `number` | `1000` | ms before brush deactivates |
| `tickFormatter` | `function` | — | Format brush labels |
| `traveller` | `function \| ReactElement` | — | Custom handle component |
| `alwaysShowText` | `boolean` | `false` | Always show range labels |
| `ariaLabel` | `string` | — | Accessibility label |
| `onChange` | `function` | — | Callback: `({startIndex, endIndex})` |
| `onDragEnd` | `function` | — | Callback on drag complete |

### Controlled Brush

```tsx
function ControlledBrush() {
  const [range, setRange] = useState({ startIndex: 0, endIndex: 20 });

  return (
    <LineChart data={data}>
      <Line dataKey="value" />
      <Brush
        startIndex={range.startIndex}
        endIndex={range.endIndex}
        onChange={setRange}
      />
    </LineChart>
  );
}
```

## Chart Synchronization

Charts with the same `syncId` share Tooltip and Brush state.

```tsx
<div>
  <LineChart data={data} syncId="dashboardSync">
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Line dataKey="revenue" stroke="#8884d8" />
  </LineChart>

  <BarChart data={data} syncId="dashboardSync">
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="orders" fill="#82ca9d" />
  </BarChart>
</div>
```

When hovering over one chart, the tooltip activates at the corresponding position in all synced charts.

### syncMethod

| Value | Behavior |
|:------|:---------|
| `"index"` | Sync by data array index (default) |
| `"value"` | Sync by matching data values |
| `function` | Custom sync function |

```tsx
<LineChart syncId="sync" syncMethod="value" data={data1}>
  ...
</LineChart>
<BarChart syncId="sync" syncMethod="value" data={data2}>
  ...
</BarChart>
```

**Known issue**: Brush handles don't visually update across synced charts. Workaround: add a hidden Brush to each synced chart with matching `startIndex`/`endIndex` values controlled by shared state.
