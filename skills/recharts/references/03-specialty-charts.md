# Specialty Charts

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [Treemap](#treemap)
- [Sankey](#sankey)
- [FunnelChart](#funnelchart)
- [SunburstChart](#sunburstchart)

## Treemap

Displays hierarchical data as nested rectangles. Each rectangle's area is proportional to its value.

```tsx
import { Treemap, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  {
    name: 'Frontend',
    children: [
      { name: 'React', size: 4000 },
      { name: 'Vue', size: 2000 },
      { name: 'Angular', size: 1500 },
      { name: 'Svelte', size: 800 },
    ],
  },
  {
    name: 'Backend',
    children: [
      { name: 'Node.js', size: 3500 },
      { name: 'Python', size: 3000 },
      { name: 'Go', size: 1200 },
    ],
  },
];

<ResponsiveContainer width="100%" height={400}>
  <Treemap
    data={data}
    dataKey="size"
    aspectRatio={4 / 3}
    stroke="#fff"
    fill="#8884d8"
  >
    <Tooltip />
  </Treemap>
</ResponsiveContainer>
```

### Treemap Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `data` | `Array<object>` | — | Hierarchical data with `children` arrays |
| `dataKey` | `string` | `"value"` | Numeric field for rectangle size |
| `nameKey` | `string` | `"name"` | Label field |
| `type` | `"flat" \| "nest"` | — | `"nest"` enables interactive drill-down |
| `aspectRatio` | `number` | `1.618` | Width/height ratio (golden ratio) |
| `content` | `function \| ReactElement` | — | Custom rectangle renderer |
| `nestIndexContent` | `function \| ReactElement` | — | Header for nest mode |
| `nodeGap` | `number` | `0` | Gap between rectangles |
| `nodeInset` | `number` | `0` | Inset padding |
| `colorPanel` | `string[]` | — | Color palette |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Animation |
| `animationDuration` | `number` | `1500` | Duration in ms |
| `animationEasing` | `string` | `"linear"` | Easing function |

**Custom content renderer**:

```tsx
const CustomTreemapContent = ({ x, y, width, height, name, value, depth }) => (
  <g>
    <rect x={x} y={y} width={width} height={height} fill={depth === 1 ? '#8884d8' : '#a4a0e8'} stroke="#fff" />
    {width > 50 && height > 20 && (
      <text x={x + width / 2} y={y + height / 2} textAnchor="middle" fill="#fff" fontSize={12}>
        {name}
      </text>
    )}
  </g>
);

<Treemap data={data} dataKey="size" content={<CustomTreemapContent />} />
```

**Nest mode** — click to drill into children:

```tsx
<Treemap data={data} dataKey="size" type="nest" nestIndexContent={(props) => (
  <text x={props.x + 5} y={props.y + 18} fill="#fff" fontSize={14} fontWeight="bold">
    {props.name}
  </text>
)} />
```

## Sankey

Visualizes flow/transfers between nodes. Nodes are connected by weighted links.

```tsx
import { Sankey, Tooltip, ResponsiveContainer } from 'recharts';

const data = {
  nodes: [
    { name: 'Visit' },
    { name: 'Direct' },
    { name: 'Organic' },
    { name: 'Referral' },
    { name: 'Sign Up' },
    { name: 'Purchase' },
  ],
  links: [
    { source: 0, target: 3, value: 100 },
    { source: 1, target: 3, value: 200 },
    { source: 2, target: 3, value: 150 },
    { source: 3, target: 4, value: 250 },
    { source: 3, target: 5, value: 200 },
  ],
};

<ResponsiveContainer width="100%" height={400}>
  <Sankey data={data} nodeWidth={10} nodePadding={60} linkCurvature={0.5}>
    <Tooltip />
  </Sankey>
</ResponsiveContainer>
```

### Sankey Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `data` | `{nodes, links}` | — | SankeyData structure |
| `dataKey` | `string` | `"value"` | Link weight field |
| `nameKey` | `string` | `"name"` | Node label field |
| `nodeWidth` | `number` | `10` | Node rectangle width |
| `nodePadding` | `number` | `10` | Vertical gap between nodes |
| `linkCurvature` | `number` | `0.5` | Link curve amount (0=straight, 1=max) |
| `iterations` | `number` | `32` | Layout iterations (more = better) |
| `sort` | `boolean` | `true` | Sort nodes by value |
| `align` | `"justify" \| "left"` | `"justify"` | Horizontal alignment (v3.4+) |
| `verticalAlign` | `"justify" \| "top"` | `"justify"` | Vertical alignment (v3.4+) |
| `node` | `function \| ReactElement` | — | Custom node renderer |
| `link` | `function \| ReactElement` | — | Custom link renderer |

**Data format**: `links` reference nodes by their array index in `nodes`:

```ts
const data: SankeyData = {
  nodes: [
    { name: 'Source A' },    // index 0
    { name: 'Source B' },    // index 1
    { name: 'Target' },      // index 2
  ],
  links: [
    { source: 0, target: 2, value: 100 },  // Source A -> Target
    { source: 1, target: 2, value: 200 },  // Source B -> Target
  ],
};
```

**Custom node colors**:

```tsx
<Sankey
  data={data}
  node={(props) => (
    <Rectangle {...props} fill={props.payload.color || '#8884d8'} />
  )}
/>
```

## FunnelChart

Displays conversion funnels with progressively narrowing trapezoids.

```tsx
import { FunnelChart, Funnel, Tooltip, LabelList } from 'recharts';

const data = [
  { value: 100, name: 'Visited', fill: '#8884d8' },
  { value: 80, name: 'Signed Up', fill: '#83a6ed' },
  { value: 50, name: 'Cart', fill: '#8dd1e1' },
  { value: 40, name: 'Checkout', fill: '#82ca9d' },
  { value: 26, name: 'Purchased', fill: '#a4de6c' },
];

<FunnelChart width={500} height={300}>
  <Tooltip />
  <Funnel dataKey="value" data={data} isAnimationActive>
    <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
  </Funnel>
</FunnelChart>
```

### Funnel Component Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `dataKey` | `string \| number` | required | Numeric field |
| `data` | `Array<object>` | — | Funnel-specific data |
| `nameKey` | `string` | `"name"` | Label field |
| `lastShapeType` | `"triangle" \| "rectangle"` | `"triangle"` | Bottom shape |
| `reversed` | `boolean` | `false` | Invert funnel (narrow at top) |
| `shape` | `function \| ReactElement` | — | Custom shape renderer |
| `activeShape` | `function \| ReactElement` | — | Hover state shape |
| `label` | `bool \| object \| function` | — | Labels |
| `legendType` | `string` | `"rect"` | Legend shape |
| `isAnimationActive` | `"auto" \| boolean` | `"auto"` | Animation |
| `animationDuration` | `number` | `1500` | Duration in ms |
| `animationBegin` | `number` | `400` | Delay |

**Reversed funnel** (pyramid):

```tsx
<Funnel dataKey="value" data={data} reversed />
```

## SunburstChart

Displays hierarchical data as concentric rings. Inner rings are parents, outer rings are children.

```tsx
import { SunburstChart, Tooltip, ResponsiveContainer } from 'recharts';

const data = {
  name: 'root',
  children: [
    {
      name: 'Frontend',
      children: [
        { name: 'React', value: 400 },
        { name: 'Vue', value: 200 },
      ],
    },
    {
      name: 'Backend',
      children: [
        { name: 'Node', value: 300 },
        { name: 'Python', value: 250 },
      ],
    },
  ],
};

<ResponsiveContainer width="100%" height={400}>
  <SunburstChart data={data}>
    <Tooltip />
  </SunburstChart>
</ResponsiveContainer>
```

### SunburstChart Props

| Prop | Type | Default | Description |
|:-----|:-----|:--------|:------------|
| `data` | `SunburstData` | — | Hierarchical data with `children` |
| `dataKey` | `string` | `"value"` | Numeric field |
| `nameKey` | `string` | `"name"` | Label field |
| `cx` | `number \| string` | center | Center x |
| `cy` | `number \| string` | center | Center y |
| `innerRadius` | `number` | `50` | Inner ring radius |
| `outerRadius` | `number` | calculated | Outer ring radius |
| `startAngle` | `number` | `0` | Start angle |
| `endAngle` | `number` | `360` | End angle |
| `padding` | `number` | `2` | Gap between sectors |
| `ringPadding` | `number` | `2` | Gap between rings |
| `fill` | `string` | `"#333"` | Default fill color |
| `stroke` | `string` | `"#FFF"` | Sector border color |
| `textOptions` | `object` | see below | SVG text styling |

**textOptions defaults**:

```ts
{
  fontWeight: "bold",
  paintOrder: "stroke fill",
  fontSize: ".75rem",
  stroke: "#FFF",
  fill: "black",
  pointerEvents: "none",
}
```

**Custom colors per level** — set `fill` on data nodes:

```ts
const data = {
  name: 'root',
  children: [
    { name: 'A', fill: '#8884d8', children: [
      { name: 'A1', value: 100, fill: '#a4a0e8' },
    ]},
  ],
};
```
