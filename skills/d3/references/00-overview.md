# D3.js Overview

> Source: [d3js.org](https://d3js.org) | [Getting Started](https://d3js.org/getting-started) | Version 7.9.0

## Table of Contents

- [What Is D3](#what-is-d3)
- [When to Use D3](#when-to-use-d3)
- [Core Philosophy](#core-philosophy)
- [Module Architecture](#module-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [TypeScript Support](#typescript-support)
- [Common Patterns](#common-patterns)

## What Is D3

D3 (Data-Driven Documents) is a JavaScript library for creating bespoke data visualizations using SVG, Canvas, and HTML. Unlike chart libraries that provide pre-built chart types, D3 provides low-level building blocks — selections, scales, shapes, axes, layouts, projections — that you compose into custom visualizations.

D3 has 113K+ GitHub stars and is the foundation that many higher-level charting libraries (Recharts, Vega, Observable Plot, Visx) are built upon.

**Key characteristics:**

- **Low-level primitives** — full control over every visual element
- **Data-driven** — bind data to DOM elements, then transform based on data
- **Modular** — import only the modules you need
- **Standards-based** — uses SVG, Canvas, CSS, and standard DOM APIs
- **No virtual DOM** — manipulates the real DOM directly

## When to Use D3

**Use D3 when:**

- You need a visualization that doesn't fit standard chart types
- You need fine-grained control over animations and transitions
- You're building interactive data exploration tools
- You need geographic map projections
- You need force-directed graph layouts
- You need hierarchical visualizations (treemaps, sunbursts, dendrograms)
- Performance matters and you want Canvas rendering

**Consider alternatives when:**

- Standard bar/line/pie charts suffice → use Recharts, Chart.js, or Observable Plot
- You want a declarative grammar of graphics → use Vega-Lite
- You want React components out of the box → use Recharts or Visx
- You need quick dashboards → use Grafana or Metabase

## Core Philosophy

D3 follows a "data join" paradigm:

1. **Select** — query DOM elements
2. **Bind** — associate data with elements
3. **Enter** — create elements for new data
4. **Update** — modify elements for changed data
5. **Exit** — remove elements for removed data

```javascript
// The classic D3 pattern
const circles = svg.selectAll("circle")
  .data(dataset)
  .join("circle")
    .attr("cx", d => xScale(d.x))
    .attr("cy", d => yScale(d.y))
    .attr("r", d => rScale(d.value))
    .attr("fill", d => colorScale(d.category));
```

## Module Architecture

D3 v7 is fully modular. The `d3` package re-exports all modules:

| Module | Purpose | Key Exports |
|:-------|:--------|:------------|
| `d3-selection` | DOM manipulation and data binding | `select`, `selectAll`, `create` |
| `d3-scale` | Map data to visual values | `scaleLinear`, `scaleBand`, `scaleTime` |
| `d3-axis` | Render reference marks for scales | `axisBottom`, `axisLeft` |
| `d3-shape` | Generate geometric primitives | `line`, `area`, `arc`, `pie`, `stack` |
| `d3-transition` | Animated transitions | `transition`, `active` |
| `d3-array` | Array statistics and transforms | `min`, `max`, `mean`, `group`, `bin` |
| `d3-hierarchy` | Hierarchical layouts | `tree`, `treemap`, `pack`, `partition` |
| `d3-force` | Force-directed simulation | `forceSimulation`, `forceLink` |
| `d3-geo` | Geographic projections and paths | `geoPath`, `geoMercator` |
| `d3-zoom` | Pan and zoom behavior | `zoom`, `zoomTransform` |
| `d3-brush` | Region selection | `brush`, `brushX`, `brushY` |
| `d3-drag` | Drag interaction | `drag` |
| `d3-color` | Color spaces and manipulation | `color`, `rgb`, `hsl`, `lab` |
| `d3-interpolate` | Value interpolation | `interpolate`, `interpolateRgb` |
| `d3-scale-chromatic` | Color schemes | `schemeCategory10`, `interpolateBlues` |
| `d3-format` | Number formatting | `format`, `formatPrefix` |
| `d3-time` | Calendar math | `timeDay`, `timeMonth`, `utcYear` |
| `d3-time-format` | Date formatting | `timeFormat`, `timeParse` |
| `d3-fetch` | Data loading | `csv`, `json`, `tsv` |
| `d3-dsv` | Delimiter-separated parsing | `csvParse`, `tsvParse` |
| `d3-contour` | Contour polygons | `contours`, `contourDensity` |
| `d3-voronoi` | Voronoi diagrams | `Delaunay` |
| `d3-path` | Canvas/SVG path serialization | `path` |
| `d3-polygon` | 2D polygon operations | `polygonArea`, `polygonHull` |
| `d3-quadtree` | Spatial indexing | `quadtree` |
| `d3-random` | Random number generators | `randomNormal`, `randomUniform` |

## Installation

### npm / yarn / pnpm

```bash
npm install d3        # Full library
npm install d3-scale  # Individual module
```

```javascript
import * as d3 from "d3";
// or import specific functions
import { scaleLinear, axisBottom } from "d3";
// or import from individual modules
import { mean, median } from "d3-array";
```

### CDN (ESM — recommended)

```html
<script type="module">
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
</script>
```

### CDN (UMD — global `d3`)

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
  // d3 is available globally
  const svg = d3.select("body").append("svg");
</script>
```

### Individual modules via CDN

```javascript
import { forceSimulation, forceCollide } from "https://cdn.jsdelivr.net/npm/d3-force@3/+esm";
```

## Quick Start

### Basic SVG Chart

```javascript
import * as d3 from "d3";

const data = [30, 80, 45, 60, 20, 90, 55];

const width = 640;
const height = 400;
const marginTop = 20;
const marginRight = 20;
const marginBottom = 30;
const marginLeft = 40;

// Create scales
const x = d3.scaleBand()
  .domain(data.map((_, i) => i))
  .range([marginLeft, width - marginRight])
  .padding(0.1);

const y = d3.scaleLinear()
  .domain([0, d3.max(data)])
  .range([height - marginBottom, marginTop]);

// Create SVG
const svg = d3.create("svg")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", [0, 0, width, height]);

// Draw bars
svg.selectAll("rect")
  .data(data)
  .join("rect")
    .attr("x", (_, i) => x(i))
    .attr("y", d => y(d))
    .attr("width", x.bandwidth())
    .attr("height", d => y(0) - y(d))
    .attr("fill", "steelblue");

// Add axes
svg.append("g")
  .attr("transform", `translate(0,${height - marginBottom})`)
  .call(d3.axisBottom(x));

svg.append("g")
  .attr("transform", `translate(${marginLeft},0)`)
  .call(d3.axisLeft(y));

// Append to page
document.getElementById("chart").append(svg.node());
```

### Loading Data

```javascript
// CSV
const data = await d3.csv("/data/sales.csv", d => ({
  date: new Date(d.date),
  value: +d.value
}));

// JSON
const topology = await d3.json("/data/us-states.json");

// TSV
const matrix = await d3.tsv("/data/matrix.tsv", d3.autoType);
```

## TypeScript Support

Install type definitions:

```bash
npm install --save-dev @types/d3
```

```typescript
import * as d3 from "d3";
import type { Selection, ScaleLinear, Axis } from "d3";

interface DataPoint {
  date: Date;
  value: number;
}

const xScale: ScaleLinear<number, number> = d3.scaleLinear()
  .domain([0, 100])
  .range([0, 640]);

const selection: Selection<SVGRectElement, DataPoint, SVGGElement, unknown> =
  svg.selectAll<SVGRectElement, DataPoint>("rect")
    .data(dataset);
```

## Common Patterns

### Margin Convention

```javascript
const margin = { top: 20, right: 30, bottom: 30, left: 40 };
const width = 928 - margin.left - margin.right;
const height = 500 - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
```

### Responsive SVG

```javascript
const svg = d3.select("#chart").append("svg")
  .attr("viewBox", [0, 0, width, height])
  .attr("style", "max-width: 100%; height: auto;");
```

### Accessor Pattern

```javascript
// Define accessors once, reuse everywhere
const xValue = d => d.date;
const yValue = d => d.value;

const x = d3.scaleTime()
  .domain(d3.extent(data, xValue))
  .range([marginLeft, width - marginRight]);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, yValue)])
  .range([height - marginBottom, marginTop]);

const line = d3.line()
  .x(d => x(xValue(d)))
  .y(d => y(yValue(d)));
```
