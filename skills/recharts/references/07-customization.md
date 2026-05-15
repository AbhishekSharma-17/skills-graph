# Customization

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [Custom Tooltip](#custom-tooltip)
- [Custom Legend](#custom-legend)
- [Custom Dots](#custom-dots)
- [Custom Bar Shapes](#custom-bar-shapes)
- [Custom Pie Sectors](#custom-pie-sectors)
- [Custom Axis Ticks](#custom-axis-ticks)
- [Custom Labels](#custom-labels)
- [Direct Custom Components](#direct-custom-components)
- [Shape Primitives](#shape-primitives)

## Custom Tooltip

Pass a React component to `<Tooltip content={...} />`. The component receives `{active, payload, label}` props. Must render HTML elements (not SVG) since Tooltip is an HTML overlay.

```tsx
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
    payload: Record<string, unknown>;
  }>;
  label?: string | number;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div style={{ background: '#fff', border: '1px solid #ccc', padding: '10px', borderRadius: '4px' }}>
      <p style={{ margin: 0, fontWeight: 'bold' }}>{label}</p>
      {payload.map((entry, index) => (
        <p key={index} style={{ margin: '4px 0', color: entry.color }}>
          {entry.name}: ${entry.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

<LineChart data={data}>
  <Line dataKey="revenue" />
  <Tooltip content={<CustomTooltip />} />
</LineChart>
```

### Accessing Full Data Point

Each `payload` entry contains the original data object in `payload.payload`:

```tsx
function DetailTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;

  return (
    <div className="tooltip">
      <h4>{data.name}</h4>
      <p>Revenue: ${data.revenue}</p>
      <p>Growth: {data.growthRate}%</p>
      <p>Region: {data.region}</p>
    </div>
  );
}
```

## Custom Legend

Pass a React component to `<Legend content={...} />`. Receives `{payload}` with series information.

```tsx
interface LegendEntry {
  value: string;
  type: string;
  color: string;
  dataKey: string;
  inactive: boolean;
}

function CustomLegend({ payload }: { payload: LegendEntry[] }) {
  return (
    <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
      {payload.map((entry, index) => (
        <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{
            width: 12, height: 12, borderRadius: '50%',
            background: entry.color, opacity: entry.inactive ? 0.3 : 1,
          }} />
          <span style={{ fontSize: 13, color: entry.inactive ? '#999' : '#333' }}>
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

<LineChart data={data}>
  <Legend content={<CustomLegend />} />
  <Line dataKey="revenue" stroke="#8884d8" />
  <Line dataKey="profit" stroke="#82ca9d" />
</LineChart>
```

## Custom Dots

Customize data point markers on Line and Area charts.

### Object Props

```tsx
// Simple customization via object
<Line dataKey="value" dot={{ r: 6, fill: '#8884d8', stroke: '#fff', strokeWidth: 2 }} />

// Disable dots
<Line dataKey="value" dot={false} />

// Only show active dot on hover
<Line dataKey="value" dot={false} activeDot={{ r: 8, fill: '#ff7300' }} />
```

### Function Renderer

```tsx
<Line
  dataKey="value"
  dot={(props) => {
    const { cx, cy, value, index } = props;
    if (value > 100) {
      return <circle cx={cx} cy={cy} r={6} fill="red" stroke="none" />;
    }
    return <circle cx={cx} cy={cy} r={4} fill="#8884d8" stroke="none" />;
  }}
/>
```

### React Element

```tsx
function AlertDot({ cx, cy, value }) {
  if (value > threshold) {
    return (
      <svg x={cx - 10} y={cy - 10} width={20} height={20}>
        <polygon points="10,0 20,20 0,20" fill="red" />
      </svg>
    );
  }
  return <circle cx={cx} cy={cy} r={4} fill="#8884d8" />;
}

<Line dataKey="value" dot={<AlertDot />} />
```

### Active Dot (Hover State)

```tsx
<Line
  dataKey="value"
  activeDot={(props) => {
    const { cx, cy } = props;
    return (
      <g>
        <circle cx={cx} cy={cy} r={12} fill="#8884d8" fillOpacity={0.2} />
        <circle cx={cx} cy={cy} r={6} fill="#8884d8" stroke="#fff" strokeWidth={2} />
      </g>
    );
  }}
/>
```

## Custom Bar Shapes

Use the `shape` prop on Bar for custom rendering.

```tsx
function RoundedBar({ x, y, width, height, fill }) {
  const radius = 8;
  return (
    <path
      d={`M${x},${y + height}
          L${x},${y + radius}
          Q${x},${y} ${x + radius},${y}
          L${x + width - radius},${y}
          Q${x + width},${y} ${x + width},${y + radius}
          L${x + width},${y + height}
          Z`}
      fill={fill}
    />
  );
}

<Bar dataKey="value" shape={<RoundedBar />} />
```

### Conditional Bar Colors

```tsx
<Bar
  dataKey="value"
  shape={(props) => {
    const fill = props.payload.value >= 0 ? '#82ca9d' : '#ff6b6b';
    return <Rectangle {...props} fill={fill} />;
  }}
/>
```

### Bar with Icons

```tsx
<Bar
  dataKey="value"
  shape={(props) => {
    const { x, y, width, height, fill } = props;
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} />
        <text x={x + width / 2} y={y - 5} textAnchor="middle" fontSize={16}>
          {props.payload.emoji}
        </text>
      </g>
    );
  }}
/>
```

## Custom Pie Sectors

Since v3.5, use the `shape` prop with `isActive` boolean:

```tsx
import { PieChart, Pie, Sector } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

<Pie
  data={data}
  dataKey="value"
  shape={(props) => {
    const { isActive, index, outerRadius, ...rest } = props;
    return (
      <Sector
        {...rest}
        outerRadius={isActive ? outerRadius + 10 : outerRadius}
        fill={COLORS[index % COLORS.length]}
        stroke={isActive ? '#333' : 'none'}
        strokeWidth={isActive ? 2 : 0}
      />
    );
  }}
/>
```

**Deprecated**: `activeShape` and `inactiveShape` props. Use `shape` with `isActive` instead.

## Custom Axis Ticks

```tsx
function CustomXTick({ x, y, payload }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} dy={16} textAnchor="middle" fill="#666" fontSize={12}>
        {payload.value}
      </text>
      <line x1={0} y1={0} x2={0} y2={6} stroke="#666" />
    </g>
  );
}

<XAxis dataKey="name" tick={<CustomXTick />} />
```

### Image Ticks

```tsx
const icons = { Chrome: '/chrome.svg', Firefox: '/firefox.svg' };

function IconTick({ x, y, payload }) {
  return (
    <g transform={`translate(${x - 12},${y})`}>
      <image href={icons[payload.value]} width={24} height={24} />
    </g>
  );
}

<XAxis dataKey="browser" tick={<IconTick />} height={40} />
```

## Custom Labels

```tsx
// Function label on bars
<Bar dataKey="value">
  <LabelList
    content={({ x, y, width, height, value }) => (
      <text
        x={x + width / 2}
        y={y + height / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#fff"
        fontSize={12}
        fontWeight="bold"
      >
        {value > 0 ? value : ''}
      </text>
    )}
  />
</Bar>

// Label on line with background
<Line dataKey="value" label={(props) => {
  const { x, y, value } = props;
  return (
    <g>
      <rect x={x - 15} y={y - 20} width={30} height={16} rx={3} fill="#8884d8" />
      <text x={x} y={y - 10} textAnchor="middle" fill="#fff" fontSize={10}>
        {value}
      </text>
    </g>
  );
}} />
```

## Direct Custom Components

In v3, you can place custom React components directly as chart children — no `<Customized>` wrapper needed. Use hooks to access chart internals.

```tsx
import { LineChart, Line, useChartWidth, useChartHeight, usePlotArea } from 'recharts';

function Watermark() {
  const plotArea = usePlotArea();
  if (!plotArea) return null;

  return (
    <text
      x={plotArea.x + plotArea.width / 2}
      y={plotArea.y + plotArea.height / 2}
      textAnchor="middle"
      fill="#ccc"
      fontSize={48}
      opacity={0.3}
      transform={`rotate(-30, ${plotArea.x + plotArea.width / 2}, ${plotArea.y + plotArea.height / 2})`}
    >
      DRAFT
    </text>
  );
}

<LineChart data={data}>
  <Line dataKey="value" />
  <Watermark />
</LineChart>
```

Note: The `<Customized>` component still exists in v3 but is deprecated. Children of `<Customized>` no longer receive extra chart props — use hooks instead.

## Shape Primitives

Recharts exports SVG shape components for use in custom renderers:

| Component | Description |
|:----------|:------------|
| `Cross` | Cross marker |
| `Curve` | D3-powered curve path |
| `Dot` | Circle dot |
| `Polygon` | Polygon shape |
| `Rectangle` | Rect with optional radius |
| `Sector` | Pie/donut sector |
| `Trapezoid` | Funnel trapezoid |
| `Symbols` | D3 symbol shapes |

```tsx
import { Rectangle, Sector, Dot } from 'recharts';

// Use in custom shape renderers
<Bar shape={(props) => <Rectangle {...props} radius={[10, 10, 0, 0]} />} />
```
