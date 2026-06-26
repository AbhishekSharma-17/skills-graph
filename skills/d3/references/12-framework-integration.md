# D3 Framework Integration

> Source: [d3js.org/getting-started](https://d3js.org/getting-started) | React, Vue, Svelte, Next.js patterns

## Table of Contents

- [Overview](#overview)
- [Integration Strategies](#integration-strategies)
- [React Integration](#react-integration)
- [Next.js Integration](#nextjs-integration)
- [Vue Integration](#vue-integration)
- [Svelte Integration](#svelte-integration)
- [SSR Considerations](#ssr-considerations)
- [Performance Tips](#performance-tips)

## Overview

D3 manipulates the DOM directly. Modern frameworks (React, Vue, Svelte) use virtual DOMs or reactive systems to manage the DOM. This creates tension — two systems fighting over the same DOM elements. The key is deciding which system owns which parts.

## Integration Strategies

### Strategy 1: D3 for math, framework for DOM (recommended)

Use D3 modules that don't touch the DOM (scales, shapes, layouts, data utilities) and let the framework render everything. Best for simple charts.

```
D3 modules safe for this: d3-scale, d3-shape, d3-array, d3-hierarchy,
d3-format, d3-time, d3-time-format, d3-color, d3-interpolate, d3-geo
```

### Strategy 2: D3 owns a ref'd container

Give D3 full control over a DOM subtree using a ref. The framework creates the container; D3 manages everything inside. Best for complex interactive visualizations.

```
D3 modules that need DOM access: d3-selection, d3-transition,
d3-axis, d3-zoom, d3-brush, d3-drag
```

### Strategy 3: Hybrid

Framework renders static elements, D3 handles axes, transitions, and interactions via refs.

## React Integration

### Strategy 1: D3 for math only

```jsx
import * as d3 from "d3";

function BarChart({ data, width = 640, height = 400 }) {
  const margin = { top: 20, right: 20, bottom: 30, left: 40 };

  const x = d3.scaleBand()
    .domain(data.map(d => d.name))
    .range([margin.left, width - margin.right])
    .padding(0.1);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value)])
    .nice()
    .range([height - margin.bottom, margin.top]);

  return (
    <svg width={width} height={height}>
      {data.map(d => (
        <rect
          key={d.name}
          x={x(d.name)}
          y={y(d.value)}
          width={x.bandwidth()}
          height={y(0) - y(d.value)}
          fill="steelblue"
        />
      ))}
    </svg>
  );
}
```

### Strategy 2: D3 owns a ref

```jsx
import * as d3 from "d3";
import { useRef, useEffect } from "react";

function LineChart({ data, width = 640, height = 400 }) {
  const svgRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();  // clear previous render

    const margin = { top: 20, right: 20, bottom: 30, left: 40 };

    const x = d3.scaleUtc()
      .domain(d3.extent(data, d => d.date))
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value)])
      .nice()
      .range([height - margin.bottom, margin.top]);

    // Line
    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 1.5)
      .attr("d", d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value)));

    // X axis
    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x));

    // Y axis
    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y));

  }, [data, width, height]);

  return <svg ref={svgRef} width={width} height={height} />;
}
```

### Strategy 3: Hybrid (recommended for most cases)

React renders SVG elements, D3 handles axes via refs:

```jsx
import * as d3 from "d3";
import { useRef, useEffect, useMemo } from "react";

function ScatterPlot({ data, width = 640, height = 400 }) {
  const xAxisRef = useRef();
  const yAxisRef = useRef();

  const margin = { top: 20, right: 20, bottom: 30, left: 40 };

  const x = useMemo(() =>
    d3.scaleLinear()
      .domain(d3.extent(data, d => d.x))
      .nice()
      .range([margin.left, width - margin.right]),
    [data, width]
  );

  const y = useMemo(() =>
    d3.scaleLinear()
      .domain(d3.extent(data, d => d.y))
      .nice()
      .range([height - margin.bottom, margin.top]),
    [data, height]
  );

  const color = useMemo(() =>
    d3.scaleOrdinal(d3.schemeCategory10),
    []
  );

  // D3 renders axes only
  useEffect(() => {
    d3.select(xAxisRef.current).call(d3.axisBottom(x));
  }, [x]);

  useEffect(() => {
    d3.select(yAxisRef.current).call(d3.axisLeft(y));
  }, [y]);

  return (
    <svg width={width} height={height}>
      <g ref={xAxisRef} transform={`translate(0,${height - margin.bottom})`} />
      <g ref={yAxisRef} transform={`translate(${margin.left},0)`} />
      {data.map((d, i) => (
        <circle
          key={i}
          cx={x(d.x)}
          cy={y(d.y)}
          r={5}
          fill={color(d.category)}
        />
      ))}
    </svg>
  );
}
```

### Zoom in React

```jsx
import { useRef, useEffect } from "react";
import * as d3 from "d3";

function ZoomableChart({ children, width, height }) {
  const svgRef = useRef();
  const gRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const g = d3.select(gRef.current);

    const zoom = d3.zoom()
      .scaleExtent([0.5, 8])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    return () => svg.on(".zoom", null);  // cleanup
  }, []);

  return (
    <svg ref={svgRef} width={width} height={height}>
      <g ref={gRef}>{children}</g>
    </svg>
  );
}
```

### Animated transitions in React

```jsx
useEffect(() => {
  d3.select(svgRef.current)
    .selectAll("rect")
    .data(data)
    .join("rect")
    .transition()
    .duration(750)
    .attr("y", d => y(d.value))
    .attr("height", d => height - margin.bottom - y(d.value));
}, [data]);
```

## Next.js Integration

### Client-only rendering

D3 requires the DOM, so it must render client-side:

```jsx
"use client";

import dynamic from "next/dynamic";

// Option 1: "use client" directive (App Router)
export default function ChartPage() {
  return <LineChart data={data} />;
}

// Option 2: Dynamic import with no SSR
const Chart = dynamic(() => import("./Chart"), { ssr: false });
```

### Loading data in Next.js

```jsx
// Server component fetches data
async function ChartPage() {
  const data = await fetch("https://api.example.com/data").then(r => r.json());
  return <ChartClient data={data} />;
}

// Client component renders chart
"use client";
function ChartClient({ data }) {
  // D3 visualization here
}
```

## Vue Integration

### Composition API

```vue
<script setup>
import * as d3 from "d3";
import { ref, onMounted, watch } from "vue";

const props = defineProps({ data: Array });
const svgRef = ref(null);

function render() {
  const svg = d3.select(svgRef.value);
  svg.selectAll("*").remove();

  const x = d3.scaleBand()
    .domain(props.data.map(d => d.name))
    .range([40, 600])
    .padding(0.1);

  const y = d3.scaleLinear()
    .domain([0, d3.max(props.data, d => d.value)])
    .range([380, 20]);

  svg.selectAll("rect")
    .data(props.data)
    .join("rect")
      .attr("x", d => x(d.name))
      .attr("y", d => y(d.value))
      .attr("width", x.bandwidth())
      .attr("height", d => 380 - y(d.value))
      .attr("fill", "steelblue");

  svg.append("g")
    .attr("transform", "translate(0,380)")
    .call(d3.axisBottom(x));

  svg.append("g")
    .attr("transform", "translate(40,0)")
    .call(d3.axisLeft(y));
}

onMounted(render);
watch(() => props.data, render, { deep: true });
</script>

<template>
  <svg ref="svgRef" width="640" height="400" />
</template>
```

### D3 for math only (Vue template rendering)

```vue
<script setup>
import * as d3 from "d3";
import { computed } from "vue";

const props = defineProps({ data: Array });

const x = computed(() =>
  d3.scaleBand()
    .domain(props.data.map(d => d.name))
    .range([40, 600])
    .padding(0.1)
);

const y = computed(() =>
  d3.scaleLinear()
    .domain([0, d3.max(props.data, d => d.value)])
    .range([380, 20])
);
</script>

<template>
  <svg width="640" height="400">
    <rect v-for="d in data" :key="d.name"
      :x="x(d.name)" :y="y(d.value)"
      :width="x.bandwidth()" :height="380 - y(d.value)"
      fill="steelblue" />
  </svg>
</template>
```

## Svelte Integration

### Reactive D3 (recommended)

Svelte's reactivity works naturally with D3 computations:

```svelte
<script>
  import * as d3 from "d3";

  export let data;
  export let width = 640;
  export let height = 400;

  const margin = { top: 20, right: 20, bottom: 30, left: 40 };

  $: x = d3.scaleLinear()
    .domain(d3.extent(data, d => d.x))
    .range([margin.left, width - margin.right]);

  $: y = d3.scaleLinear()
    .domain(d3.extent(data, d => d.y))
    .range([height - margin.bottom, margin.top]);

  $: line = d3.line()
    .x(d => x(d.x))
    .y(d => y(d.y));
</script>

<svg {width} {height}>
  <path d={line(data)} fill="none" stroke="steelblue" stroke-width="1.5" />
  {#each data as d}
    <circle cx={x(d.x)} cy={y(d.y)} r="3" fill="steelblue" />
  {/each}
</svg>
```

### Axes via Svelte actions

```svelte
<script>
  import * as d3 from "d3";

  function xaxis(node, scale) {
    d3.select(node).call(d3.axisBottom(scale));
    return {
      update(scale) {
        d3.select(node).transition().duration(300).call(d3.axisBottom(scale));
      }
    };
  }
</script>

<g use:xaxis={x} transform="translate(0,{height - margin.bottom})" />
```

## SSR Considerations

D3 modules that access the DOM (`d3-selection`, `d3-transition`, `d3-axis`, `d3-zoom`, `d3-brush`, `d3-drag`) will fail during server-side rendering.

**Safe for SSR:** `d3-scale`, `d3-shape`, `d3-array`, `d3-format`, `d3-time`, `d3-color`, `d3-interpolate`, `d3-hierarchy`, `d3-geo`, `d3-force`.

**Strategies:**
1. Use `"use client"` (Next.js App Router)
2. Dynamic import with `ssr: false`
3. Guard DOM code with `typeof window !== "undefined"`
4. Use only DOM-free D3 modules during SSR, add interactivity client-side

## Performance Tips

- **Memoize scales** — `useMemo` in React, `computed` in Vue, `$:` in Svelte
- **Don't recreate D3 objects on every render** — cache line generators, color scales
- **Use Canvas for >1000 elements** — SVG performance degrades with many nodes
- **Debounce resize handlers** — recalculating on every pixel is wasteful
- **Use `requestAnimationFrame`** for custom animations outside D3 transitions
- **Clean up event listeners** — remove zoom/brush/drag handlers in cleanup functions
- **Avoid `selectAll("*").remove()`** when partial updates suffice — target specific elements
