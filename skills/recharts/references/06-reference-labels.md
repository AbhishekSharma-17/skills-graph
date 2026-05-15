# Reference Components & Labels

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [ReferenceLine](#referenceline)
- [ReferenceArea](#referencearea)
- [ReferenceDot](#referencedot)
- [ErrorBar](#errorbar)
- [Label](#label)
- [LabelList](#labellist)

## ReferenceLine

Draws a horizontal, vertical, or diagonal reference line on the chart.

```tsx
import { LineChart, Line, ReferenceLine, XAxis, YAxis } from 'recharts';

<LineChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line dataKey="value" />

  {/* Horizontal line at y=50 */}
  <ReferenceLine y={50} stroke="red" strokeDasharray="3 3" label="Target" />

  {/* Vertical line at x="Wed" */}
  <ReferenceLine x="Wed" stroke="blue" label="Midweek" />
</LineChart>
```

### ReferenceLine Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `x` | `string \| number` | — | Vertical line at data domain value |
| `y` | `string \| number` | — | Horizontal line at data domain value |
| `segment` | `[{x?,y?}, {x?,y?}]` | — | Diagonal line between two points |
| `ifOverflow` | `string` | `"discard"` | Behavior when outside domain |
| `position` | `"start" \| "middle" \| "end"` | `"middle"` | Position on band scale |
| `shape` | `function \| ReactElement` | — | Custom line renderer |
| `label` | `string \| object \| function \| ReactNode` | — | Text label |
| `stroke` | `string` | — | Line color |
| `strokeWidth` | `number` | `1` | Line thickness |
| `strokeDasharray` | `string` | — | Dash pattern |
| `xAxisId` | `string \| number` | `0` | Associated X axis |
| `yAxisId` | `string \| number` | `0` | Associated Y axis |
| `zIndex` | `number` | `400` | Layer order |

**ifOverflow options**:

| Value | Behavior |
|:------|:---------|
| `"discard"` | Don't render if outside domain (default) |
| `"hidden"` | Render but clip to chart area |
| `"visible"` | Render even outside chart area |
| `"extendDomain"` | Extend axis domain to include the reference |

### Diagonal Line

```tsx
<ReferenceLine
  segment={[{ x: 'Mon', y: 0 }, { x: 'Fri', y: 100 }]}
  stroke="red"
  strokeDasharray="5 5"
/>
```

### Label Positioning

```tsx
<ReferenceLine
  y={75}
  stroke="red"
  label={{ value: 'Threshold', position: 'insideTopRight', fill: 'red', fontSize: 12 }}
/>
```

## ReferenceArea

Highlights a rectangular region on the chart.

```tsx
<LineChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line dataKey="value" />

  {/* Highlight region */}
  <ReferenceArea x1="Tue" x2="Thu" y1={20} y2={80} fill="yellow" fillOpacity={0.3} />

  {/* Highlight from edge */}
  <ReferenceArea y1={90} fill="red" fillOpacity={0.1} label="Danger Zone" />
</LineChart>
```

### ReferenceArea Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `x1` | `string \| number` | — | Left boundary (extends to edge if omitted) |
| `x2` | `string \| number` | — | Right boundary |
| `y1` | `string \| number` | — | Bottom boundary |
| `y2` | `string \| number` | — | Top boundary |
| `ifOverflow` | `string` | `"discard"` | Behavior when outside domain |
| `radius` | `number \| [tl,tr,br,bl]` | — | Corner radius |
| `shape` | `function \| ReactElement` | — | Custom shape renderer |
| `label` | `string \| object \| function \| ReactNode` | — | Text label |
| `fill` | `string` | — | Fill color |
| `fillOpacity` | `number` | — | Fill transparency |
| `stroke` | `string` | — | Border color |
| `xAxisId` | `string \| number` | `0` | Associated X axis |
| `yAxisId` | `string \| number` | `0` | Associated Y axis |
| `zIndex` | `number` | `100` | Layer order |

**Partial boundaries**: omit `x1`, `x2`, `y1`, or `y2` to extend the area to the chart edge.

```tsx
// Highlight everything above y=80
<ReferenceArea y1={80} fill="red" fillOpacity={0.1} label="Critical" />

// Highlight a single column
<ReferenceArea x1="Wed" x2="Wed" fill="blue" fillOpacity={0.1} />
```

## ReferenceDot

Places a dot marker at a specific data coordinate.

```tsx
<LineChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line dataKey="value" />
  <ReferenceDot x="Wed" y={75} r={8} fill="red" stroke="none" label="Peak" />
</LineChart>
```

### ReferenceDot Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `x` | `string \| number` | — | X coordinate in data domain |
| `y` | `string \| number` | — | Y coordinate in data domain |
| `r` | `number` | `10` | Dot radius |
| `ifOverflow` | `string` | `"discard"` | Behavior when outside domain |
| `shape` | `function \| ReactElement` | — | Custom dot renderer |
| `label` | `string \| object \| function \| ReactNode` | — | Text label |
| `fill` | `string` | — | Fill color |
| `stroke` | `string` | — | Border color |
| `xAxisId` | `string \| number` | `0` | Associated X axis |
| `yAxisId` | `string \| number` | `0` | Associated Y axis |
| `zIndex` | `number` | `600` | Layer order |

**Event handlers**: `onClick`, `onMouseDown`, `onMouseUp`, `onMouseEnter`, `onMouseLeave`, `onMouseMove`

## ErrorBar

Draws error whiskers on Bar, Line, or Scatter data points.

```tsx
import { BarChart, Bar, ErrorBar, XAxis, YAxis } from 'recharts';

const data = [
  { name: 'A', value: 100, error: 10 },
  { name: 'B', value: 200, error: 25 },
  { name: 'C', value: 150, error: [10, 30] },  // asymmetric
];

<BarChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Bar dataKey="value" fill="#8884d8">
    <ErrorBar dataKey="error" width={4} strokeWidth={2} stroke="#333" />
  </Bar>
</BarChart>
```

### ErrorBar Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string` | required | Error field (number or [lower, upper]) |
| `direction` | `"x" \| "y"` | auto | Error direction |
| `width` | `number` | `5` | Whisker end cap width |
| `stroke` | `string` | `"black"` | Line color |
| `strokeWidth` | `number` | `1.5` | Line thickness |
| `isAnimationActive` | `boolean` | `true` | Animate |
| `animationDuration` | `number` | `400` | Duration in ms |
| `animationEasing` | `string` | `"ease-in-out"` | Easing |
| `zIndex` | `number` | `400` | Layer order |

**Symmetric vs asymmetric error**:
- Symmetric: `error: 10` → ±10 from the value
- Asymmetric: `error: [5, 15]` → -5/+15 from the value

**In Scatter charts**, `direction` is required:

```tsx
<Scatter data={data}>
  <ErrorBar dataKey="errorX" direction="x" />
  <ErrorBar dataKey="errorY" direction="y" />
</Scatter>
```

## Label

Positions text labels on axes, reference components, and chart elements.

```tsx
<ReferenceLine y={50} stroke="red">
  <Label value="Target" position="insideTopRight" fill="red" />
</ReferenceLine>

<YAxis>
  <Label value="Revenue ($)" angle={-90} position="insideLeft" />
</YAxis>
```

### Label Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `value` | `string \| number` | — | Label text (or use `children`) |
| `position` | `string` | `"middle"` | One of 20+ positions |
| `content` | `function \| ReactNode` | — | Custom render |
| `formatter` | `function` | — | Transform value |
| `offset` | `number` | `5` | Distance from anchor |
| `angle` | `number` | `0` | Rotation degrees |
| `textBreakAll` | `boolean` | `false` | Word break all |
| `zIndex` | `number` | `2000` | Layer order |

**Position values**: `bottom`, `center`, `top`, `inside`, `insideTop`, `insideBottom`, `insideLeft`, `insideRight`, `left`, `right`, `end`, `start`, `centerTop`, `centerBottom`, `insideTopLeft`, `insideBottomLeft`, `insideBottomRight`, `insideTopRight`, `insideStart`, `insideEnd`, `outside`, `middle`

## LabelList

Renders labels for each data point in a series component.

```tsx
import { BarChart, Bar, LabelList } from 'recharts';

<BarChart data={data}>
  <Bar dataKey="value" fill="#8884d8">
    <LabelList dataKey="value" position="top" />
  </Bar>
</BarChart>
```

### LabelList Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string` | — | Field to display (required for Scatter) |
| `position` | `string` | `"middle"` | Label position |
| `offset` | `number` | `5` | Distance from anchor |
| `content` | `function \| ReactNode` | — | Custom renderer |
| `formatter` | `function` | — | Transform values |
| `angle` | `number` | `0` | Rotation degrees |
| `textBreakAll` | `boolean` | `false` | Word break all |
| `valueAccessor` | `function` | — | Alternative to dataKey |
| `zIndex` | `number` | `2000` | Layer order |

**Parent components**: Area, Bar, Line, Radar, RadialBar, Scatter

### Custom Label Content

```tsx
<Bar dataKey="value" fill="#8884d8">
  <LabelList
    content={({ x, y, width, value }) => (
      <text x={x + width / 2} y={y - 5} textAnchor="middle" fill="#333" fontSize={11}>
        {`$${value}`}
      </text>
    )}
  />
</Bar>
```

### Labels on Lines

```tsx
<Line dataKey="value" stroke="#8884d8">
  <LabelList dataKey="value" position="top" offset={10} fontSize={10} />
</Line>
```
