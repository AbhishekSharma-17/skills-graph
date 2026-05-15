# Performance & SSR

> Source: [recharts.org/en-US/guide/performance](https://recharts.org/en-US/guide/performance)

## Table of Contents

- [Performance Optimization](#performance-optimization)
- [Memoization](#memoization)
- [Large Datasets](#large-datasets)
- [Event Throttling](#event-throttling)
- [Next.js / SSR](#nextjs-ssr)
- [Common Performance Mistakes](#common-performance-mistakes)

## Performance Optimization

### 1. Isolate Components

Separate frequently-changing components from static ones. If a parent re-renders, all child charts re-render too.

```tsx
// BAD: timer forces chart to re-render every second
function Dashboard() {
  const [time, setTime] = useState(Date.now());
  useEffect(() => { const id = setInterval(() => setTime(Date.now()), 1000); return () => clearInterval(id); }, []);

  return (
    <div>
      <span>{new Date(time).toLocaleTimeString()}</span>
      <LineChart data={data}><Line dataKey="value" /></LineChart>
    </div>
  );
}

// GOOD: chart is isolated from timer
function Dashboard() {
  return (
    <div>
      <Clock />
      <Chart data={data} />
    </div>
  );
}

const Chart = React.memo(({ data }) => (
  <LineChart data={data}><Line dataKey="value" /></LineChart>
));
```

### 2. Stable References

Use `useMemo` and `useCallback` for objects and functions passed as props. Reference changes trigger full recalculation.

```tsx
// BAD: new object every render
<Line dot={{ r: 4, fill: '#8884d8' }} />

// GOOD: stable reference
const dotStyle = useMemo(() => ({ r: 4, fill: '#8884d8' }), []);
<Line dot={dotStyle} />
```

**Critical for `dataKey`**: if you pass a function as `dataKey`, it must be memoized. A new function reference forces a complete data recalculation.

```tsx
// BAD: inline function creates new reference every render
<Line dataKey={(entry) => entry.revenue - entry.cost} />

// GOOD: memoized
const profitKey = useCallback((entry) => entry.revenue - entry.cost, []);
<Line dataKey={profitKey} />
```

### 3. Memoize Data

```tsx
// BAD: new array reference every render
function Chart({ rawData }) {
  const data = rawData.map(d => ({ ...d, total: d.a + d.b }));
  return <LineChart data={data}>...</LineChart>;
}

// GOOD: memoized transformation
function Chart({ rawData }) {
  const data = useMemo(() => rawData.map(d => ({ ...d, total: d.a + d.b })), [rawData]);
  return <LineChart data={data}>...</LineChart>;
}
```

### 4. ESLint Plugin

Use `eslint-plugin-react-perf` to detect inline object and function creation in JSX:

```bash
npm install -D eslint-plugin-react-perf
```

## Memoization

### Chart Wrapper Pattern

```tsx
interface ChartProps {
  data: DataPoint[];
  width?: number;
  height?: number;
}

const MemoizedChart = React.memo<ChartProps>(({ data, width = 600, height = 300 }) => (
  <LineChart width={width} height={height} data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="value" stroke="#8884d8" />
  </LineChart>
));
```

### Props Stability Checklist

| Prop | Stable? | Fix |
|:-----|:--------|:----|
| `data={items}` | Only if `items` reference stable | `useMemo` |
| `margin={{ top: 5 }}` | No — inline object | Extract constant or `useMemo` |
| `dot={{ r: 4 }}` | No — inline object | Extract constant or `useMemo` |
| `dataKey="value"` | Yes — string literal | N/A |
| `dataKey={(d) => d.x}` | No — inline function | `useCallback` |
| `tickFormatter={fn}` | No if inline | `useCallback` |
| `onClick={handler}` | No if inline | `useCallback` |

## Large Datasets

### Data Reduction

Does your chart truly need 50,000 points? Consider:

- **Aggregation**: group by hour/day/week instead of showing every minute
- **Sampling**: take every Nth point
- **Binning**: use D3's `d3.bin()` to create histogram buckets
- **Summary statistics**: show mean/median/percentiles instead of raw data

```tsx
// Sample every 10th point
const sampled = useMemo(() => data.filter((_, i) => i % 10 === 0), [data]);
```

### Disable Animations

```tsx
<Line dataKey="value" isAnimationActive={false} />
<Bar dataKey="value" isAnimationActive={false} />
```

### Use Brush for Windowing

Instead of rendering all data, show a subset with Brush for navigation:

```tsx
<LineChart data={largeDataset}>
  <XAxis dataKey="date" />
  <YAxis />
  <Line dataKey="value" isAnimationActive={false} dot={false} />
  <Brush dataKey="date" height={30} />
</LineChart>
```

### Remove Dots

Dots are individual SVG elements — thousands of them hurt performance:

```tsx
<Line dataKey="value" dot={false} activeDot={{ r: 4 }} />
```

### Lazy Loading

Render charts only when visible:

```tsx
function LazyChart({ data }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        observer.disconnect();
      }
    });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} style={{ minHeight: 300 }}>
      {visible && (
        <ResponsiveContainer height={300}>
          <LineChart data={data}><Line dataKey="value" /></LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
```

## Event Throttling

v3 has built-in event throttling:

```tsx
// Default: requestAnimationFrame-based throttling
<LineChart data={data} throttleDelay="raf">
  ...
</LineChart>

// Custom delay (ms)
<LineChart data={data} throttleDelay={100}>
  ...
</LineChart>
```

| Value | Behavior |
|:------|:---------|
| `"raf"` | Throttle via `requestAnimationFrame` (default, ~16ms) |
| `number` | Fixed delay in milliseconds |

Throttled events (default): `mousemove`, `touchmove`, `pointermove`, `scroll`, `wheel`

## Next.js / SSR

### The Problem

Recharts uses browser APIs (SVG, DOM measurement). Without proper setup: `TypeError: Super expression must either be null or a function`

### Solution 1: "use client" Directive (Recommended)

```tsx
// components/RevenueChart.tsx
"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function RevenueChart({ data }: { data: DataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

```tsx
// app/dashboard/page.tsx (Server Component)
import { RevenueChart } from '@/components/RevenueChart';

export default async function DashboardPage() {
  const data = await fetchRevenueData();
  return <RevenueChart data={data} />;
}
```

### Solution 2: Dynamic Import with ssr: false

```tsx
// app/dashboard/page.tsx
import dynamic from 'next/dynamic';

const RevenueChart = dynamic(() => import('@/components/RevenueChart'), {
  ssr: false,
  loading: () => <div style={{ height: 400 }}>Loading chart...</div>,
});

export default function DashboardPage({ data }) {
  return <RevenueChart data={data} />;
}
```

### Data Fetching Pattern

Fetch data server-side, render chart client-side:

```tsx
// Server Component (fetches data)
async function Dashboard() {
  const data = await db.query('SELECT month, revenue FROM sales');
  return <ChartSection data={data} />;
}

// Client Component (renders chart)
"use client";
function ChartSection({ data }: { data: SalesData[] }) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data}>
        <Bar dataKey="revenue" fill="#8884d8" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

### Animation + SSR

`isAnimationActive="auto"` automatically disables animations during SSR, preventing hydration mismatches. No manual configuration needed.

## Common Performance Mistakes

| Mistake | Impact | Fix |
|:--------|:-------|:----|
| Inline objects as props | Re-render every cycle | Extract to constant or `useMemo` |
| Inline functions for `dataKey` | Full data recalculation | `useCallback` |
| New `data` array on each render | Complete chart rebuild | `useMemo` |
| Rendering 10K+ dots | SVG DOM explosion | `dot={false}` |
| Animations on large datasets | Jank during transitions | `isAnimationActive={false}` |
| ResponsiveContainer without parent height | Chart invisible / zero height | Set parent height |
| Using deprecated `Cell` per-item | Extra component overhead | Use `shape` prop |
| Not debouncing real-time updates | Continuous re-renders | Debounce data updates |
