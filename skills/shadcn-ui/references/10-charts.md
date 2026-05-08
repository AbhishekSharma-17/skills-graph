# shadcn/ui — Charts

> Source: [ui.shadcn.com/charts](https://ui.shadcn.com/charts) | [ui.shadcn.com/docs/components/radix/chart](https://ui.shadcn.com/docs/components/radix/chart)

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Chart Config](#chart-config)
- [Area Chart](#area-chart)
- [Bar Chart](#bar-chart)
- [Line Chart](#line-chart)
- [Pie & Donut Charts](#pie--donut-charts)
- [Radar Chart](#radar-chart)
- [Tooltips](#tooltips)
- [Legends](#legends)
- [Responsive Charts](#responsive-charts)
- [Theming](#theming)
- [Common Patterns](#common-patterns)

## Overview

shadcn/ui charts are built on Recharts v3. The chart component wraps Recharts with:
- Semantic color tokens (uses `--chart-1` through `--chart-5`)
- Custom `ChartTooltip` and `ChartLegend` components
- Accessible defaults
- Dark mode support via CSS variables

The composable approach means you use Recharts components directly, adding shadcn/ui wrappers only where needed (tooltips, legends).

## Setup

```bash
npx shadcn@latest add chart
```

This installs the `ChartContainer`, `ChartTooltip`, `ChartTooltipContent`, `ChartLegend`, and `ChartLegendContent` components, plus the `recharts` dependency.

## Chart Config

Every chart needs a `chartConfig` object that maps data keys to labels and colors:

```tsx
import { type ChartConfig } from "@/components/ui/chart";

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-1)",
  },
  mobile: {
    label: "Mobile",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig;
```

The `ChartContainer` uses this config to set up CSS variables that Recharts references:

```tsx
import { ChartContainer } from "@/components/ui/chart";

<ChartContainer config={chartConfig} className="min-h-[200px] w-full">
  {/* Recharts components go here */}
</ChartContainer>
```

## Area Chart

```tsx
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

const data = [
  { month: "January", desktop: 186, mobile: 80 },
  { month: "February", desktop: 305, mobile: 200 },
  { month: "March", desktop: 237, mobile: 120 },
  { month: "April", desktop: 73, mobile: 190 },
  { month: "May", desktop: 209, mobile: 130 },
  { month: "June", desktop: 214, mobile: 140 },
];

<ChartContainer config={chartConfig} className="min-h-[300px] w-full">
  <AreaChart data={data}>
    <CartesianGrid vertical={false} />
    <XAxis dataKey="month" tickLine={false} tickMargin={10} axisLine={false}
      tickFormatter={(value) => value.slice(0, 3)} />
    <ChartTooltip content={<ChartTooltipContent />} />
    <Area dataKey="desktop" type="natural" fill="var(--color-desktop)"
      fillOpacity={0.4} stroke="var(--color-desktop)" />
    <Area dataKey="mobile" type="natural" fill="var(--color-mobile)"
      fillOpacity={0.4} stroke="var(--color-mobile)" />
  </AreaChart>
</ChartContainer>
```

### Stacked Area

```tsx
<Area dataKey="desktop" type="natural" fill="var(--color-desktop)"
  fillOpacity={0.4} stroke="var(--color-desktop)" stackId="a" />
<Area dataKey="mobile" type="natural" fill="var(--color-mobile)"
  fillOpacity={0.4} stroke="var(--color-mobile)" stackId="a" />
```

### Gradient Fill

```tsx
<defs>
  <linearGradient id="fillDesktop" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%" stopColor="var(--color-desktop)" stopOpacity={0.8} />
    <stop offset="95%" stopColor="var(--color-desktop)" stopOpacity={0.1} />
  </linearGradient>
</defs>
<Area dataKey="desktop" fill="url(#fillDesktop)" stroke="var(--color-desktop)" />
```

## Bar Chart

```tsx
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";

<ChartContainer config={chartConfig} className="min-h-[300px] w-full">
  <BarChart data={data}>
    <CartesianGrid vertical={false} />
    <XAxis dataKey="month" tickLine={false} tickMargin={10} axisLine={false}
      tickFormatter={(value) => value.slice(0, 3)} />
    <ChartTooltip content={<ChartTooltipContent />} />
    <Bar dataKey="desktop" fill="var(--color-desktop)" radius={4} />
    <Bar dataKey="mobile" fill="var(--color-mobile)" radius={4} />
  </BarChart>
</ChartContainer>
```

### Horizontal Bar

```tsx
<BarChart data={data} layout="vertical">
  <XAxis type="number" />
  <YAxis dataKey="month" type="category" tickLine={false} axisLine={false} />
  <Bar dataKey="desktop" fill="var(--color-desktop)" radius={4} />
</BarChart>
```

### Stacked Bar

```tsx
<Bar dataKey="desktop" stackId="a" fill="var(--color-desktop)" radius={[0, 0, 4, 4]} />
<Bar dataKey="mobile" stackId="a" fill="var(--color-mobile)" radius={[4, 4, 0, 0]} />
```

## Line Chart

```tsx
import { CartesianGrid, Line, LineChart, XAxis } from "recharts";

<ChartContainer config={chartConfig} className="min-h-[300px] w-full">
  <LineChart data={data}>
    <CartesianGrid vertical={false} />
    <XAxis dataKey="month" tickLine={false} axisLine={false}
      tickFormatter={(value) => value.slice(0, 3)} />
    <ChartTooltip content={<ChartTooltipContent />} />
    <Line dataKey="desktop" type="natural" stroke="var(--color-desktop)"
      strokeWidth={2} dot={false} />
    <Line dataKey="mobile" type="natural" stroke="var(--color-mobile)"
      strokeWidth={2} dot={false} />
  </LineChart>
</ChartContainer>
```

### With Dots

```tsx
<Line dataKey="desktop" type="natural" stroke="var(--color-desktop)"
  strokeWidth={2} dot={{ fill: "var(--color-desktop)", r: 4 }}
  activeDot={{ r: 6 }} />
```

## Pie & Donut Charts

```tsx
import { Pie, PieChart } from "recharts";

const pieData = [
  { browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
  { browser: "safari", visitors: 200, fill: "var(--color-safari)" },
  { browser: "firefox", visitors: 187, fill: "var(--color-firefox)" },
  { browser: "edge", visitors: 173, fill: "var(--color-edge)" },
  { browser: "other", visitors: 90, fill: "var(--color-other)" },
];

const pieConfig = {
  chrome: { label: "Chrome", color: "var(--chart-1)" },
  safari: { label: "Safari", color: "var(--chart-2)" },
  firefox: { label: "Firefox", color: "var(--chart-3)" },
  edge: { label: "Edge", color: "var(--chart-4)" },
  other: { label: "Other", color: "var(--chart-5)" },
} satisfies ChartConfig;

// Pie chart
<ChartContainer config={pieConfig} className="mx-auto aspect-square max-h-[250px]">
  <PieChart>
    <ChartTooltip content={<ChartTooltipContent hideLabel />} />
    <Pie data={pieData} dataKey="visitors" nameKey="browser" />
  </PieChart>
</ChartContainer>

// Donut chart
<Pie data={pieData} dataKey="visitors" nameKey="browser"
  innerRadius={60} outerRadius={80} />

// With center label
<Pie data={pieData} dataKey="visitors" nameKey="browser"
  innerRadius={60} outerRadius={80}>
  <Label
    content={({ viewBox }) => (
      <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle">
        <tspan className="fill-foreground text-3xl font-bold">925</tspan>
        <tspan x={viewBox.cx} y={viewBox.cy + 24} className="fill-muted-foreground">
          Visitors
        </tspan>
      </text>
    )}
  />
</Pie>
```

## Radar Chart

```tsx
import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from "recharts";

const radarData = [
  { month: "January", desktop: 186, mobile: 80 },
  { month: "February", desktop: 305, mobile: 200 },
  { month: "March", desktop: 237, mobile: 120 },
];

<ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-[250px]">
  <RadarChart data={radarData}>
    <ChartTooltip content={<ChartTooltipContent />} />
    <PolarAngleAxis dataKey="month" />
    <PolarGrid />
    <Radar dataKey="desktop" fill="var(--color-desktop)" fillOpacity={0.6} />
    <Radar dataKey="mobile" fill="var(--color-mobile)" fillOpacity={0.6} />
  </RadarChart>
</ChartContainer>
```

## Tooltips

```tsx
// Default tooltip
<ChartTooltip content={<ChartTooltipContent />} />

// Hide label
<ChartTooltip content={<ChartTooltipContent hideLabel />} />

// Custom indicator
<ChartTooltip content={<ChartTooltipContent indicator="line" />} />
<ChartTooltip content={<ChartTooltipContent indicator="dot" />} />
<ChartTooltip content={<ChartTooltipContent indicator="dashed" />} />

// Cursor highlight
<ChartTooltip cursor={false} content={<ChartTooltipContent />} />
```

## Legends

```tsx
import { ChartLegend, ChartLegendContent } from "@/components/ui/chart";

<ChartLegend content={<ChartLegendContent />} />
```

## Responsive Charts

```tsx
<ChartContainer config={chartConfig} className="h-[200px] sm:h-[300px] md:h-[400px] w-full">
  {/* Chart auto-sizes to container */}
</ChartContainer>
```

## Theming

Chart colors automatically adapt to dark mode via CSS variables:

```css
:root {
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
}

.dark {
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
}
```

## Common Patterns

### Dashboard KPI Card with Sparkline

```tsx
<Card>
  <CardHeader className="pb-2">
    <CardDescription>Total Revenue</CardDescription>
    <CardTitle className="text-4xl">$45,231.89</CardTitle>
  </CardHeader>
  <CardContent>
    <ChartContainer config={config} className="h-[80px] w-full">
      <AreaChart data={sparklineData}>
        <Area dataKey="revenue" type="natural" fill="var(--color-revenue)"
          fillOpacity={0.2} stroke="var(--color-revenue)" strokeWidth={2} />
      </AreaChart>
    </ChartContainer>
  </CardContent>
  <CardFooter>
    <p className="text-xs text-muted-foreground">+20.1% from last month</p>
  </CardFooter>
</Card>
```

### Interactive Chart with Period Selector

```tsx
const [period, setPeriod] = useState("7d");

<Card>
  <CardHeader className="flex flex-row items-center justify-between">
    <CardTitle>Analytics</CardTitle>
    <Select value={period} onValueChange={setPeriod}>
      <SelectTrigger className="w-[120px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="7d">Last 7 days</SelectItem>
        <SelectItem value="30d">Last 30 days</SelectItem>
        <SelectItem value="90d">Last 90 days</SelectItem>
      </SelectContent>
    </Select>
  </CardHeader>
  <CardContent>
    <ChartContainer config={config} className="h-[300px] w-full">
      <LineChart data={getDataForPeriod(period)}>
        {/* ... */}
      </LineChart>
    </ChartContainer>
  </CardContent>
</Card>
```
