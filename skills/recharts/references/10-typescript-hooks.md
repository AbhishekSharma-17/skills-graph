# TypeScript & Hooks

> Source: [recharts.org/en-US/api](https://recharts.org/en-US/api)

## Table of Contents

- [TypeScript Setup](#typescript-setup)
- [Built-in Types](#built-in-types)
- [Component Prop Types](#component-prop-types)
- [Utility Types](#utility-types)
- [Generics (v3.8+)](#generics)
- [Hooks API](#hooks-api)
- [Common TypeScript Patterns](#common-typescript-patterns)

## TypeScript Setup

Recharts v3 ships its own TypeScript definitions. Do **not** install `@types/recharts` — it will conflict.

```bash
npm install recharts
# That's it. Types are included.
```

**Requirements**: TypeScript 5.x+, TS target ES6+

## Built-in Types

### Chart Props

```tsx
import type {
  // Cartesian chart props
  CartesianChartProps,
  // Polar chart props  
  PolarChartProps,
} from 'recharts';
```

`CartesianChartProps` — base for BarChart, LineChart, AreaChart, ComposedChart, ScatterChart, FunnelChart

`PolarChartProps` — base for PieChart, RadarChart, RadialBarChart

### Series Component Props

```tsx
import type {
  BarProps,
  LineProps,
  AreaProps,
  ScatterProps,
  PieProps,
  RadarProps,
  RadialBarProps,
  FunnelProps,
} from 'recharts';
```

### Axis Props

```tsx
import type {
  XAxisProps,
  YAxisProps,
  ZAxisProps,
  PolarAngleAxisProps,
  PolarRadiusAxisProps,
} from 'recharts';
```

### Other Component Props

```tsx
import type {
  TooltipProps,           // Tooltip component props
  TooltipContentProps,    // Custom tooltip content props (renamed from TooltipProps in v3)
  LegendProps,
  ResponsiveContainerProps,
  ReferenceLineProps,
  ReferenceAreaProps,
  ReferenceDotProps,
  BrushProps,
  CartesianGridProps,
  LabelProps,
  LabelListProps,
  ErrorBarProps,
} from 'recharts';
```

**Important**: In v3, `TooltipProps` refers to the `<Tooltip>` component props. For custom tooltip content, use `TooltipContentProps` (was `TooltipProps` in v2).

## Component Prop Types

### Internal Path Imports

For types not re-exported from the root:

```tsx
import type { AreaProps } from 'recharts/types/cartesian/Area';
import type { SankeyData } from 'recharts/types/util/types';
```

## Utility Types

```tsx
import type {
  // Coordinate types
  Coordinate,          // { x: number, y: number }
  PolarCoordinate,     // { cx, cy, radius, angle }
  
  // Layout types
  Margin,              // { top, bottom, left, right }
  PlotArea,            // { x, y, width, height }
  
  // Axis types
  AxisDomainItem,      // number | string | 'auto' | 'dataMin' | 'dataMax' | Function
  AxisInterval,        // number | 'preserveStart' | 'preserveEnd' | 'preserveStartEnd'
  AxisRange,           // [number, number]
  
  // Data types
  DataKey,             // string | number
  
  // Shape types
  SymbolType,          // 'circle' | 'cross' | 'diamond' | 'square' | 'star' | 'triangle' | 'wye'
  
  // Reference types
  IfOverflow,          // 'extendDomain' | 'hidden' | 'discard' | 'visible'
  
  // Scale types
  ScaleFunction,
  InverseScaleFunction,
  CustomScaleDefinition,
  
  // Tooltip types
  TooltipPayloadEntry, // { name, value, color, dataKey, payload, chartType }
  
  // Tick types
  TickItem,            // { value, index, coordinate, offset }
} from 'recharts';
```

## Generics

v3.8 added generics for type-safe `data` and `dataKey`:

```tsx
interface SalesData {
  month: string;
  revenue: number;
  orders: number;
  growth: number;
}

const data: SalesData[] = [
  { month: 'Jan', revenue: 4000, orders: 240, growth: 12 },
  { month: 'Feb', revenue: 3000, orders: 139, growth: -8 },
];

// Type-safe: dataKey must be keyof SalesData
<LineChart<SalesData> data={data}>
  <XAxis dataKey="month" />
  <YAxis />
  <Line dataKey="revenue" />   {/* OK */}
  <Line dataKey="orders" />    {/* OK */}
  <Line dataKey="invalid" />   {/* TS Error: not in SalesData */}
</LineChart>
```

This catches typos in `dataKey` at compile time.

## Hooks API

v3 introduced hooks for accessing chart internals from custom components placed directly as chart children.

### Dimension Hooks

```tsx
import { useChartWidth, useChartHeight, usePlotArea, useMargin, useOffset } from 'recharts';

function ChartOverlay() {
  const width = useChartWidth();    // number | undefined
  const height = useChartHeight();  // number | undefined
  const plotArea = usePlotArea();   // { x, y, width, height } | undefined (v3.1+)
  const margin = useMargin();       // Margin
  const offset = useOffset();       // offset values

  if (!plotArea) return null;
  return <rect x={plotArea.x} y={plotArea.y} width={plotArea.width} height={plotArea.height} fill="none" stroke="red" />;
}
```

### Layout Hook

```tsx
import { useChartLayout, useCartesianChartLayout, usePolarChartLayout } from 'recharts';

function LayoutAware() {
  const layout = useChartLayout();  // chart layout state
  return null;
}
```

### Tooltip Hooks

```tsx
import {
  useIsTooltipActive,           // boolean (v3.7+)
  useActiveTooltipCoordinate,   // Coordinate | undefined (v3.7+)
  useActiveTooltipDataPoints,   // Array<T> | undefined
  useActiveTooltipLabel,        // number | string | undefined (v3.0+)
} from 'recharts';

function TooltipIndicator() {
  const isActive = useIsTooltipActive();
  const coord = useActiveTooltipCoordinate();
  const label = useActiveTooltipLabel();
  const points = useActiveTooltipDataPoints();

  if (!isActive || !coord) return null;
  return <circle cx={coord.x} cy={coord.y} r={4} fill="red" />;
}
```

### Axis Hooks

```tsx
import {
  // Domain hooks
  useXAxisDomain,   // axis domain values
  useYAxisDomain,
  
  // Tick hooks
  useXAxisTicks,    // tick items array
  useYAxisTicks,
  
  // Scale hooks (v3.8+)
  useXAxisScale,              // ScaleFunction
  useYAxisScale,
  useXAxisInverseScale,       // InverseScaleFunction
  useYAxisInverseScale,
  
  // Snap scale hooks (v3.8+)
  useXAxisInverseDataSnapScale,
  useYAxisInverseDataSnapScale,
  useXAxisInverseTickSnapScale,
  useYAxisInverseTickSnapScale,
  
  // Cartesian scale
  useCartesianScale,
} from 'recharts';
```

### Scale Hooks Example

```tsx
function DataAnnotation({ targetValue }: { targetValue: number }) {
  const yScale = useYAxisScale();
  const plotArea = usePlotArea();
  
  if (!yScale || !plotArea) return null;
  
  const yPixel = yScale(targetValue);
  return (
    <line
      x1={plotArea.x}
      y1={yPixel}
      x2={plotArea.x + plotArea.width}
      y2={yPixel}
      stroke="red"
      strokeDasharray="4 4"
    />
  );
}

<LineChart data={data}>
  <YAxis />
  <Line dataKey="value" />
  <DataAnnotation targetValue={75} />
</LineChart>
```

## Common TypeScript Patterns

### Typed Custom Tooltip

```tsx
import type { TooltipProps } from 'recharts';
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';

function CustomTooltip({ active, payload, label }: TooltipProps<ValueType, NameType>) {
  if (!active || !payload?.length) return null;
  return (
    <div>
      <p>{label}</p>
      {payload.map((p, i) => (
        <p key={i}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
}
```

### Typed Custom Dot

```tsx
interface DotProps {
  cx: number;
  cy: number;
  value: number;
  index: number;
  payload: Record<string, unknown>;
}

function TypedDot({ cx, cy, value }: DotProps) {
  return <circle cx={cx} cy={cy} r={value > 100 ? 6 : 3} fill="#8884d8" />;
}
```

### Typed Event Handlers

```tsx
import type { CategoricalChartFunc } from 'recharts/types/chart/generateCategoricalChart';

const handleClick: CategoricalChartFunc = (state, event) => {
  if (state?.activePayload) {
    console.log(state.activePayload[0].payload);
  }
};

<LineChart data={data} onClick={handleClick}>
  <Line dataKey="value" />
</LineChart>
```

### Typed Data Helper

```tsx
function createChartData<T extends Record<string, unknown>>(data: T[]) {
  return data;
}

const data = createChartData([
  { month: 'Jan', revenue: 4000 },
  { month: 'Feb', revenue: 3000 },
]);
```
