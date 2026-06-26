# D3 Shapes

> Source: [d3-shape](https://d3js.org/d3-shape) | Module: `d3-shape`

## Table of Contents

- [Overview](#overview)
- [Lines](#lines)
- [Areas](#areas)
- [Arcs](#arcs)
- [Pies](#pies)
- [Stacks](#stacks)
- [Symbols](#symbols)
- [Links](#links)
- [Curves](#curves)
- [Canvas Rendering](#canvas-rendering)

## Overview

Shape generators produce SVG path data (`d` attribute) or render to a Canvas 2D context. They follow the accessor pattern — configure how data maps to visual properties, then pass data to generate the path.

```javascript
const line = d3.line()
  .x(d => xScale(d.date))
  .y(d => yScale(d.value));

path.datum(data).attr("d", line);
```

## Lines

### d3.line()

Generates a polyline/spline from an array of points.

```javascript
const line = d3.line()
  .x(d => x(d.date))
  .y(d => y(d.value));

svg.append("path")
  .datum(data)
  .attr("fill", "none")
  .attr("stroke", "steelblue")
  .attr("stroke-width", 1.5)
  .attr("d", line);
```

### Accessors

```javascript
// Default accessors (by index)
const line = d3.line()
  .x((d, i) => x(i))    // index-based
  .y(d => y(d));         // value-based

// With arrays of [x, y]
const line = d3.line()
  .x(d => xScale(d[0]))
  .y(d => yScale(d[1]));
```

### Handling missing data

```javascript
const line = d3.line()
  .defined(d => !isNaN(d.value) && d.value !== null)
  .x(d => x(d.date))
  .y(d => y(d.value));
// Gaps appear where defined() returns false
```

### Multi-line chart

```javascript
const series = ["revenue", "costs", "profit"];
const color = d3.scaleOrdinal(series, d3.schemeCategory10);

svg.selectAll("path")
  .data(series)
  .join("path")
    .attr("fill", "none")
    .attr("stroke", d => color(d))
    .attr("stroke-width", 1.5)
    .attr("d", key => d3.line()
      .x(d => x(d.date))
      .y(d => y(d[key]))
    (data));
```

## Areas

### d3.area()

Generates a region bounded by a topline and baseline.

```javascript
const area = d3.area()
  .x(d => x(d.date))
  .y0(y(0))                // baseline (bottom)
  .y1(d => y(d.value));    // topline

svg.append("path")
  .datum(data)
  .attr("fill", "steelblue")
  .attr("fill-opacity", 0.3)
  .attr("d", area);
```

### Area between two lines

```javascript
const area = d3.area()
  .x(d => x(d.date))
  .y0(d => y(d.low))      // lower bound
  .y1(d => y(d.high));    // upper bound
```

### Area with missing data

```javascript
const area = d3.area()
  .defined(d => !isNaN(d.value))
  .x(d => x(d.date))
  .y0(y(0))
  .y1(d => y(d.value));
```

### Vertical area

```javascript
const area = d3.area()
  .y(d => y(d.category))
  .x0(x(0))
  .x1(d => x(d.value));
```

## Arcs

### d3.arc()

Generates circular or annular sectors (for pie/donut charts).

```javascript
const arc = d3.arc()
  .innerRadius(0)        // 0 = pie, >0 = donut
  .outerRadius(200)
  .startAngle(0)         // in radians
  .endAngle(Math.PI);    // half circle

svg.append("path").attr("d", arc());
```

### Data-driven arcs (with pie)

```javascript
const arc = d3.arc()
  .innerRadius(80)       // donut hole
  .outerRadius(200)
  .padAngle(0.02)        // gap between slices
  .cornerRadius(4);      // rounded corners

// arc() expects { startAngle, endAngle } — usually from d3.pie()
pieData.forEach(d => {
  svg.append("path")
    .attr("d", arc(d))
    .attr("fill", color(d.data.name));
});
```

### Arc methods

```javascript
arc.centroid(d)  // [x, y] center point of arc — useful for labels

// Label positioning
svg.selectAll("text")
  .data(pieData)
  .join("text")
    .attr("transform", d => `translate(${arc.centroid(d)})`)
    .attr("text-anchor", "middle")
    .text(d => d.data.name);
```

## Pies

### d3.pie()

Computes arc angles from data values. Does not draw anything — produces data for d3.arc().

```javascript
const data = [
  { name: "A", value: 30 },
  { name: "B", value: 50 },
  { name: "C", value: 20 }
];

const pie = d3.pie()
  .value(d => d.value)     // accessor for value
  .sort(null)               // disable sorting (keep data order)
  .padAngle(0.02);          // gap between slices

const arcs = pie(data);
// Returns array of { startAngle, endAngle, data, value, index, padAngle }

const arc = d3.arc().innerRadius(0).outerRadius(200);

svg.selectAll("path")
  .data(arcs)
  .join("path")
    .attr("d", arc)
    .attr("fill", d => color(d.data.name))
    .attr("transform", `translate(${width/2},${height/2})`);
```

### Donut chart

```javascript
const arc = d3.arc()
  .innerRadius(radius * 0.6)  // donut hole
  .outerRadius(radius);

const labelArc = d3.arc()
  .innerRadius(radius * 0.8)
  .outerRadius(radius * 0.8);

// Labels at midpoint
arcs.forEach(d => {
  const [x, y] = labelArc.centroid(d);
  // position label at x, y
});
```

## Stacks

### d3.stack()

Computes a stacked layout from tabular data.

```javascript
const data = [
  { month: "Jan", apples: 100, bananas: 80, cherries: 40 },
  { month: "Feb", apples: 120, bananas: 90, cherries: 50 },
  { month: "Mar", apples: 90,  bananas: 70, cherries: 60 }
];

const stack = d3.stack()
  .keys(["apples", "bananas", "cherries"])
  .order(d3.stackOrderNone)
  .offset(d3.stackOffsetNone);

const series = stack(data);
// series[0] = apples:   [[0, 100], [0, 120], [0, 90]]
// series[1] = bananas:  [[100, 180], [120, 210], [90, 160]]
// series[2] = cherries: [[180, 220], [210, 260], [160, 220]]

// Each inner array: [y0, y1] (baseline, topline)
```

### Stacked area chart

```javascript
const area = d3.area()
  .x((d, i) => x(data[i].month))
  .y0(d => y(d[0]))
  .y1(d => y(d[1]));

svg.selectAll("path")
  .data(series)
  .join("path")
    .attr("fill", d => color(d.key))
    .attr("d", area);
```

### Stack offsets

```javascript
d3.stackOffsetNone       // zero baseline (default)
d3.stackOffsetExpand     // normalize to [0, 1] — percentage stacks
d3.stackOffsetDiverging  // positive above zero, negative below
d3.stackOffsetSilhouette // centered around zero
d3.stackOffsetWiggle     // minimizes weighted wiggle (streamgraph)
```

### Stack orders

```javascript
d3.stackOrderNone        // input order (default)
d3.stackOrderAscending   // smallest on bottom
d3.stackOrderDescending  // largest on bottom
d3.stackOrderInsideOut   // largest in middle (streamgraph)
d3.stackOrderReverse     // reverse input order
```

## Symbols

### d3.symbol()

Generates categorical symbol shapes for scatterplots.

```javascript
const symbol = d3.symbol()
  .type(d3.symbolCircle)
  .size(64);  // area in square pixels

svg.selectAll("path")
  .data(data)
  .join("path")
    .attr("d", d => symbol.type(symbolScale(d.category))())
    .attr("transform", d => `translate(${x(d.x)},${y(d.y)})`)
    .attr("fill", d => color(d.category));
```

### Built-in symbol types

```javascript
d3.symbolCircle      // filled circle
d3.symbolCross       // Greek cross
d3.symbolDiamond     // rhombus
d3.symbolSquare      // square
d3.symbolStar        // five-pointed star
d3.symbolTriangle    // upward triangle
d3.symbolWye         // Y-shape

// Symbol type scale
const symbolType = d3.scaleOrdinal()
  .domain(categories)
  .range(d3.symbolsFill);  // array of all fill symbols
```

## Links

### d3.linkHorizontal() / d3.linkVertical()

Smooth cubic Bezier curves connecting two points (for tree/network diagrams).

```javascript
const link = d3.linkHorizontal()
  .x(d => d.y)    // note: horizontal links swap x/y
  .y(d => d.x);

svg.selectAll("path")
  .data(root.links())
  .join("path")
    .attr("d", link)
    .attr("fill", "none")
    .attr("stroke", "#ccc");
```

## Curves

Curve interpolators control how points are connected in lines and areas.

```javascript
const line = d3.line()
  .x(d => x(d.date))
  .y(d => y(d.value))
  .curve(d3.curveMonotoneX);  // smooth, monotone interpolation
```

### Available curves

| Curve | Description | Use Case |
|:------|:-----------|:---------|
| `d3.curveLinear` | Straight segments (default) | General line charts |
| `d3.curveStep` | Horizontal then vertical | Discrete/categorical data |
| `d3.curveStepBefore` | Vertical then horizontal | Discrete data |
| `d3.curveStepAfter` | Horizontal then vertical | Discrete data |
| `d3.curveBasis` | Cubic B-spline (smoothed) | Smooth trends |
| `d3.curveBundle` | Straightened cubic B-spline | Hierarchical edge bundling |
| `d3.curveCardinal` | Cubic cardinal spline | Smooth with tension control |
| `d3.curveCatmullRom` | Centripetal Catmull-Rom | Smooth, passes through points |
| `d3.curveMonotoneX` | Monotone cubic (x) | Time series (no overshooting) |
| `d3.curveMonotoneY` | Monotone cubic (y) | Vertical time series |
| `d3.curveNatural` | Natural cubic spline | Smooth interpolation |
| `d3.curveBumpX` | Bumpy horizontal Bezier | Sankey-like connections |
| `d3.curveBumpY` | Bumpy vertical Bezier | Sankey-like connections |

### Closed curves (for polygons)

```javascript
d3.curveBasisClosed
d3.curveCardinalClosed
d3.curveCatmullRomClosed
d3.curveLinearClosed
```

## Canvas Rendering

All shapes support Canvas rendering via `.context()`:

```javascript
const canvas = document.getElementById("chart");
const context = canvas.getContext("2d");

const line = d3.line()
  .x(d => x(d.date))
  .y(d => y(d.value))
  .context(context);

context.beginPath();
line(data);
context.strokeStyle = "steelblue";
context.stroke();
```
