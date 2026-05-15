# Polar Charts

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [PieChart](#piechart)
- [Pie Component Props](#pie-component-props)
- [RadarChart](#radarchart)
- [Radar Component Props](#radar-component-props)
- [RadialBarChart](#radialbart)
- [RadialBar Component Props](#radialbar-component-props)
- [Polar Axes](#polar-axes)
- [Common Patterns](#common-patterns)

## PieChart

```tsx
import { PieChart, Pie, Tooltip, Legend } from 'recharts';

const data = [
  { name: 'Chrome', value: 400 },
  { name: 'Firefox', value: 300 },
  { name: 'Safari', value: 200 },
  { name: 'Edge', value: 100 },
];

<PieChart width={400} height={400}>
  <Pie data={data} dataKey="value" cx="50%" cy="50%" outerRadius={120} fill="#8884d8" label />
  <Tooltip />
  <Legend />
</PieChart>
```

### PieChart Props

| Prop | Type | Default |
|:-----|:-----|:--------|
| `width` | `number \| string` | — |
| `height` | `number \| string` | — |
| `margin` | `{top, right, bottom, left}` | `{5,5,5,5}` |
| `responsive` | `boolean` | `false` |
| `accessibilityLayer` | `boolean` | `true` |

### Pie Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `data` | `Array<object>` | — | Pie-specific data |
| `dataKey` | `string \| number` | `"value"` | Numeric field for slice size |
| `nameKey` | `string` | `"name"` | Label field |
| `cx` | `number \| string` | `"50%"` | Center x |
| `cy` | `number \| string` | `"50%"` | Center y |
| `innerRadius` | `number \| string` | `0` | Donut hole (0 = full pie) |
| `outerRadius` | `number \| string` | `"80%"` | Outer edge |
| `startAngle` | `number` | `0` | Arc start (degrees) |
| `endAngle` | `number` | `360` | Arc end (degrees) |
| `paddingAngle` | `number` | `0` | Gap between slices |
| `minAngle` | `number` | `0` | Minimum slice angle |
| `cornerRadius` | `number` | — | Rounded sector corners |
| `label` | `bool \| object \| function \| ReactNode` | `false` | Slice labels |
| `labelLine` | `bool \| object \| function` | `true` | Line from slice to label |
| `shape` | `function \| ReactElement` | — | Custom sector renderer (v3.5+) |
| `legendType` | `string` | `"rect"` | Shape in legend |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Enable animation |
| `animationDuration` | `number` | `1500` | Duration in ms |
| `animationBegin` | `number` | `400` | Delay before animation |
| `zIndex` | `number` | `100` | Layer order |

**Donut chart** — set `innerRadius`:

```tsx
<Pie data={data} dataKey="value" innerRadius={60} outerRadius={100} paddingAngle={5} />
```

**Nested pies** — multiple Pie components with different radii:

```tsx
<PieChart width={400} height={400}>
  <Pie data={outerData} dataKey="value" outerRadius={120} fill="#8884d8" />
  <Pie data={innerData} dataKey="value" innerRadius={70} outerRadius={100} fill="#82ca9d" />
</PieChart>
```

**Half pie** — adjust angles:

```tsx
<Pie data={data} dataKey="value" startAngle={180} endAngle={0} outerRadius={100} />
```

**Custom colors per slice** — use `shape` prop (v3.5+):

```tsx
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

<Pie
  data={data}
  dataKey="value"
  shape={(props) => {
    const fill = COLORS[props.index % COLORS.length];
    return <Sector {...props} fill={fill} />;
  }}
/>
```

**Active slice highlighting** — use `shape` with `isActive` (v3.5+):

```tsx
<Pie
  data={data}
  dataKey="value"
  shape={(props) => {
    const { isActive, outerRadius, ...rest } = props;
    return <Sector {...rest} outerRadius={isActive ? outerRadius + 10 : outerRadius} />;
  }}
/>
```

Note: `activeShape` and `inactiveShape` props are deprecated in v3.5+. Use `shape` with the `isActive` boolean instead.

## RadarChart

```tsx
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

const data = [
  { subject: 'Math', score: 120, fullMark: 150 },
  { subject: 'Chinese', score: 98, fullMark: 150 },
  { subject: 'English', score: 86, fullMark: 150 },
  { subject: 'Geography', score: 99, fullMark: 150 },
  { subject: 'Physics', score: 85, fullMark: 150 },
  { subject: 'History', score: 65, fullMark: 150 },
];

<RadarChart cx="50%" cy="50%" outerRadius="80%" width={500} height={500} data={data}>
  <PolarGrid />
  <PolarAngleAxis dataKey="subject" />
  <PolarRadiusAxis angle={30} domain={[0, 150]} />
  <Radar name="Student A" dataKey="score" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
</RadarChart>
```

### RadarChart Props

| Prop | Type | Default |
|:-----|:-----|:--------|
| `cx` | `number \| string` | `"50%"` |
| `cy` | `number \| string` | `"50%"` |
| `outerRadius` | `number \| string` | `"80%"` |
| `innerRadius` | `number` | `0` |
| `startAngle` | `number` | `90` |
| `endAngle` | `number` | `-270` |

### Radar Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string \| number` | required | Numeric field |
| `dot` | `bool \| object \| function \| ReactNode` | `false` | Point markers |
| `activeDot` | `bool \| object \| function \| ReactNode` | `true` | Hover dot |
| `shape` | `function \| ReactElement` | — | Custom polygon |
| `connectNulls` | `boolean` | `false` | Bridge nulls |
| `legendType` | `string` | `"rect"` | Legend shape |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Animation |
| `animationDuration` | `number` | `1500` | Duration in ms |

**Multiple radars** for comparison:

```tsx
<RadarChart data={data}>
  <PolarGrid />
  <PolarAngleAxis dataKey="subject" />
  <Radar name="Student A" dataKey="scoreA" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
  <Radar name="Student B" dataKey="scoreB" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
  <Legend />
</RadarChart>
```

## RadialBarChart

```tsx
import { RadialBarChart, RadialBar, Legend, Tooltip } from 'recharts';

const data = [
  { name: '18-24', uv: 31.47, fill: '#8884d8' },
  { name: '25-29', uv: 26.69, fill: '#83a6ed' },
  { name: '30-34', uv: 15.69, fill: '#8dd1e1' },
  { name: '35-39', uv: 8.22, fill: '#82ca9d' },
];

<RadialBarChart
  width={500}
  height={300}
  cx="50%"
  cy="50%"
  innerRadius="10%"
  outerRadius="80%"
  barSize={10}
  data={data}
>
  <RadialBar minAngle={15} background clockWise dataKey="uv" />
  <Legend />
  <Tooltip />
</RadialBarChart>
```

### RadialBarChart Props

| Prop | Type | Default |
|:-----|:-----|:--------|
| `cx` | `number \| string` | `"50%"` |
| `cy` | `number \| string` | `"50%"` |
| `innerRadius` | `number \| string` | — |
| `outerRadius` | `number \| string` | — |
| `barSize` | `number` | — |
| `startAngle` | `number` | `0` |
| `endAngle` | `number` | `360` |

### RadialBar Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string \| number` | — | Numeric field |
| `barSize` | `number` | — | Bar thickness |
| `cornerRadius` | `number` | `0` | Rounded ends |
| `background` | `bool \| object \| function` | — | Track background |
| `label` | `bool \| object \| function` | — | Bar labels |
| `shape` | `function \| ReactElement` | — | Custom renderer |
| `stackId` | `string \| number` | — | Stacking group |
| `minPointSize` | `number` | `0` | Minimum bar size |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Animation |
| `animationDuration` | `number` | `1500` | Duration in ms |
| `zIndex` | `number` | `300` | Layer order |

## Polar Axes

### PolarAngleAxis

Controls the labels around the circle perimeter:

```tsx
<PolarAngleAxis
  dataKey="subject"
  tick={{ fill: '#666', fontSize: 12 }}
  axisLineType="circle"  // "polygon" (default) or "circle"
/>
```

| Prop | Type | Default |
|:-----|:-----|:--------|
| `dataKey` | `string` | — |
| `axisLineType` | `"polygon" \| "circle"` | `"polygon"` |
| `tick` | `bool \| object \| function` | `true` |
| `tickLine` | `bool \| object` | `true` |
| `tickFormatter` | `function` | — |
| `orientation` | `"outer" \| "inner"` | `"outer"` |

### PolarRadiusAxis

Controls the radial axis (spoke with tick marks):

```tsx
<PolarRadiusAxis angle={30} domain={[0, 150]} tick={{ fill: '#999' }} />
```

| Prop | Type | Default |
|:-----|:-----|:--------|
| `angle` | `number` | `0` |
| `domain` | `[min, max]` | auto |
| `orientation` | `"left" \| "right"` | `"right"` |
| `tick` | `bool \| object \| function` | `true` |
| `tickCount` | `number` | `5` |
| `scale` | `string` | `"auto"` |

### PolarGrid

Background grid for polar charts:

```tsx
<PolarGrid gridType="circle" stroke="#eee" />
```

| Prop | Type | Default |
|:-----|:-----|:--------|
| `gridType` | `"polygon" \| "circle"` | `"polygon"` |
| `radialLines` | `boolean` | `true` |
| `stroke` | `string` | `"#ccc"` |
| `strokeDasharray` | `string` | — |

## Common Patterns

### Pie with Custom Labels

```tsx
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

<Pie data={data} dataKey="value" label={renderCustomLabel} labelLine={false} />
```

### Progress Ring (RadialBar)

```tsx
const progress = [{ name: 'Progress', value: 75, fill: '#8884d8' }];

<RadialBarChart
  width={200} height={200}
  cx="50%" cy="50%"
  innerRadius="60%" outerRadius="80%"
  startAngle={90} endAngle={-270}
  data={progress}
>
  <RadialBar dataKey="value" background cornerRadius={10} />
</RadialBarChart>
```
