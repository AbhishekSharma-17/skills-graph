# D3 Axes

> Source: [d3-axis](https://d3js.org/d3-axis) | Module: `d3-axis`

## Table of Contents

- [Overview](#overview)
- [Axis Generators](#axis-generators)
- [Rendering Axes](#rendering-axes)
- [Tick Configuration](#tick-configuration)
- [Formatting Ticks](#formatting-ticks)
- [Styling Axes](#styling-axes)
- [Animated Axis Updates](#animated-axis-updates)
- [Common Patterns](#common-patterns)

## Overview

D3 axes render human-readable reference marks for scales. An axis generator produces SVG elements — a `<path>` for the domain line and `<g>` elements for each tick mark with a `<line>` and `<text>` label.

Axes work with any D3 scale that has `.ticks()` and `.tickFormat()` methods (linear, log, time, pow, band, etc.).

## Axis Generators

Four axis orientations, each positioning ticks relative to the domain line:

```javascript
d3.axisTop(scale)    // ticks above, horizontal line
d3.axisRight(scale)  // ticks right, vertical line
d3.axisBottom(scale) // ticks below, horizontal line (most common for x)
d3.axisLeft(scale)   // ticks left, vertical line (most common for y)
```

Each returns an axis generator function that renders into an SVG `<g>` element.

## Rendering Axes

### Basic axis rendering

```javascript
const x = d3.scaleLinear([0, 100], [marginLeft, width - marginRight]);
const y = d3.scaleLinear([0, 100], [height - marginBottom, marginTop]);

// X axis at bottom
svg.append("g")
  .attr("transform", `translate(0,${height - marginBottom})`)
  .call(d3.axisBottom(x));

// Y axis at left
svg.append("g")
  .attr("transform", `translate(${marginLeft},0)`)
  .call(d3.axisLeft(y));
```

### Generated SVG structure

```html
<g fill="none" font-size="10" font-family="sans-serif" text-anchor="middle">
  <path class="domain" stroke="currentColor" d="M0.5,6V0.5H800.5V6"></path>
  <g class="tick" opacity="1" transform="translate(0.5,0)">
    <line stroke="currentColor" y2="6"></line>
    <text fill="currentColor" y="9" dy="0.71em">0</text>
  </g>
  <g class="tick" opacity="1" transform="translate(200.5,0)">
    <line stroke="currentColor" y2="6"></line>
    <text fill="currentColor" y="9" dy="0.71em">25</text>
  </g>
  <!-- more ticks... -->
</g>
```

## Tick Configuration

### axis.ticks(count, specifier)

Suggest the number of ticks (actual count may vary for "nice" values):

```javascript
const xAxis = d3.axisBottom(x).ticks(5);    // ~5 ticks
const yAxis = d3.axisLeft(y).ticks(10);     // ~10 ticks

// With format specifier
const axis = d3.axisBottom(x).ticks(10, "s"); // SI-prefix (k, M, G)
```

### axis.tickValues(values)

Explicitly set which values get ticks:

```javascript
const axis = d3.axisBottom(x)
  .tickValues([0, 25, 50, 75, 100]);

// Fibonacci ticks
const axis = d3.axisBottom(x)
  .tickValues([1, 2, 3, 5, 8, 13, 21]);

// Reset to auto
axis.tickValues(null);
```

### axis.tickArguments(args)

Alternative to `.ticks()` — pass arguments as array:

```javascript
axis.tickArguments([20, "s"]);
// equivalent to axis.ticks(20, "s")
```

### axis.tickSize(size)

Set length of both inner and outer tick lines (default: 6):

```javascript
const axis = d3.axisBottom(x).tickSize(10);
```

### axis.tickSizeInner(size) / axis.tickSizeOuter(size)

```javascript
const axis = d3.axisBottom(x)
  .tickSizeInner(6)   // normal tick marks
  .tickSizeOuter(0);  // removes domain end caps
```

### axis.tickPadding(padding)

Spacing between tick line and label text (default: 3):

```javascript
const axis = d3.axisBottom(x).tickPadding(8);
```

### axis.offset(offset)

Pixel offset for crisp rendering (default: 0.5 on low-DPI, 0 on high-DPI):

```javascript
const axis = d3.axisBottom(x).offset(0);
```

## Formatting Ticks

### axis.tickFormat(format)

Custom tick label formatting:

```javascript
// Number formatting
d3.axisLeft(y).tickFormat(d3.format(",.0f"))   // "1,234"
d3.axisLeft(y).tickFormat(d3.format(".1%"))     // "50.0%"
d3.axisLeft(y).tickFormat(d3.format("$,.2f"))   // "$1,234.56"
d3.axisLeft(y).tickFormat(d3.format(".2s"))      // "1.2k"

// Custom function
d3.axisBottom(x).tickFormat(d => d >= 1000 ? `${d/1000}k` : d)

// Time formatting
d3.axisBottom(timeScale).tickFormat(d3.timeFormat("%b %d"))  // "Jan 15"
d3.axisBottom(timeScale).tickFormat(d3.timeFormat("%Y"))     // "2024"

// Multi-format for time (context-dependent)
d3.axisBottom(timeScale).tickFormat(d3.utcFormat("%b %-d"))

// Empty string to hide labels but keep tick marks
d3.axisBottom(x).tickFormat("")
```

### Common d3.format specifiers

| Specifier | Example | Description |
|:----------|:--------|:------------|
| `","` | 1,234,567 | Grouped thousands |
| `".2f"` | 3.14 | Fixed-point (2 decimals) |
| `".1%"` | 50.0% | Percentage |
| `".2s"` | 1.2k | SI-prefix |
| `"$,.0f"` | $1,235 | Currency |
| `"+.1f"` | +3.1 | Signed |
| `".3~s"` | 1.23k | SI-prefix, trim trailing zeros |

### Common d3.timeFormat tokens

| Token | Example | Description |
|:------|:--------|:------------|
| `%Y` | 2024 | 4-digit year |
| `%y` | 24 | 2-digit year |
| `%m` | 01 | Month (zero-padded) |
| `%b` | Jan | Abbreviated month |
| `%B` | January | Full month |
| `%d` | 05 | Day (zero-padded) |
| `%-d` | 5 | Day (no padding) |
| `%H` | 14 | Hour (24h) |
| `%I` | 02 | Hour (12h) |
| `%M` | 30 | Minute |
| `%p` | PM | AM/PM |

## Styling Axes

### CSS styling

```css
/* Domain line */
.domain {
  stroke: #ccc;
}

/* Tick lines */
.tick line {
  stroke: #ddd;
}

/* Tick labels */
.tick text {
  font-size: 12px;
  fill: #666;
}

/* Remove domain line entirely */
.domain {
  display: none;
}
```

### Inline styling with D3

```javascript
const gx = svg.append("g")
  .attr("transform", `translate(0,${height - marginBottom})`)
  .call(d3.axisBottom(x));

// Style after rendering
gx.select(".domain").attr("stroke", "#ccc");
gx.selectAll(".tick line").attr("stroke", "#ddd");
gx.selectAll(".tick text").attr("fill", "#666").attr("font-size", "12px");

// Remove domain line
gx.select(".domain").remove();
```

### Grid lines

Extend tick lines across the chart area:

```javascript
// Horizontal grid lines (extend y-axis ticks)
svg.append("g")
  .attr("transform", `translate(${marginLeft},0)`)
  .call(d3.axisLeft(y)
    .tickSize(-(width - marginLeft - marginRight))  // negative = extend right
    .tickFormat("")  // no labels for grid
  )
  .call(g => g.select(".domain").remove())
  .call(g => g.selectAll(".tick line").attr("stroke", "#eee"));

// Vertical grid lines (extend x-axis ticks)
svg.append("g")
  .attr("transform", `translate(0,${marginTop})`)
  .call(d3.axisTop(x)
    .tickSize(-(height - marginTop - marginBottom))
    .tickFormat("")
  )
  .call(g => g.select(".domain").remove())
  .call(g => g.selectAll(".tick line").attr("stroke", "#eee"));
```

## Animated Axis Updates

Axes animate smoothly when called on a transition:

```javascript
// Store axis group reference
const gx = svg.append("g")
  .attr("transform", `translate(0,${height - marginBottom})`);

// Initial render
gx.call(d3.axisBottom(x));

// Animate to new scale
x.domain([0, 200]);
gx.transition()
  .duration(750)
  .call(d3.axisBottom(x));
```

### Axis as a reusable function

```javascript
const xAxis = (g) => g
  .attr("transform", `translate(0,${height - marginBottom})`)
  .call(d3.axisBottom(x).ticks(width / 80))
  .call(g => g.select(".domain").remove());

// Render
svg.append("g").call(xAxis);

// Update with transition
svg.select("g").transition().call(xAxis);
```

## Common Patterns

### Rotated tick labels

```javascript
svg.append("g")
  .attr("transform", `translate(0,${height - marginBottom})`)
  .call(d3.axisBottom(x))
  .selectAll("text")
    .attr("transform", "rotate(-45)")
    .attr("text-anchor", "end")
    .attr("dx", "-0.8em")
    .attr("dy", "0.15em");
```

### Axis labels (title)

```javascript
// X-axis label
svg.append("text")
  .attr("x", width / 2)
  .attr("y", height - 5)
  .attr("text-anchor", "middle")
  .text("Time (months)");

// Y-axis label (rotated)
svg.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -height / 2)
  .attr("y", 15)
  .attr("text-anchor", "middle")
  .text("Revenue ($)");
```

### Band scale axis

```javascript
const x = d3.scaleBand()
  .domain(data.map(d => d.name))
  .range([marginLeft, width - marginRight])
  .padding(0.1);

svg.append("g")
  .attr("transform", `translate(0,${height - marginBottom})`)
  .call(d3.axisBottom(x))
  .selectAll("text")
    .attr("font-size", data.length > 20 ? "8px" : "10px");
```

### Log scale axis

```javascript
const y = d3.scaleLog()
  .domain([1, 10000])
  .range([height - marginBottom, marginTop]);

svg.append("g")
  .attr("transform", `translate(${marginLeft},0)`)
  .call(d3.axisLeft(y)
    .ticks(5)
    .tickFormat(d3.format(",d"))  // "1", "10", "100", "1,000"
  );
```
