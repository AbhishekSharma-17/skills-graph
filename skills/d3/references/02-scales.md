# D3 Scales

> Source: [d3-scale](https://d3js.org/d3-scale) | Module: `d3-scale`

## Table of Contents

- [Overview](#overview)
- [Continuous Scales](#continuous-scales)
- [Time Scales](#time-scales)
- [Sequential and Diverging Scales](#sequential-and-diverging-scales)
- [Quantize Quantile Threshold](#quantize-quantile-threshold)
- [Ordinal Scales](#ordinal-scales)
- [Band and Point Scales](#band-and-point-scales)
- [Common Methods](#common-methods)
- [Choosing a Scale](#choosing-a-scale)

## Overview

Scales map abstract data values (the **domain**) to visual values (the **range**). They are the foundation of every D3 visualization — encoding data as position, size, color, or opacity.

```javascript
// Domain: data space → Range: pixel space
const x = d3.scaleLinear()
  .domain([0, 100])    // data values
  .range([0, 640]);    // pixel values

x(0);   // 0
x(50);  // 320
x(100); // 640
```

## Continuous Scales

### scaleLinear

Maps a continuous quantitative domain to a continuous range with linear interpolation.

```javascript
const x = d3.scaleLinear()
  .domain([0, 100])
  .range([0, 800]);

x(50);        // 400
x.invert(400); // 50 — reverse mapping
```

**Shorthand (v7):**
```javascript
const x = d3.scaleLinear([0, 100], [0, 800]);
```

**With color range:**
```javascript
const color = d3.scaleLinear()
  .domain([0, 50, 100])
  .range(["green", "yellow", "red"]);

color(25); // interpolated between green and yellow
```

### scaleLog

Logarithmic scale — useful for data spanning orders of magnitude.

```javascript
const x = d3.scaleLog()
  .domain([1, 1000])  // domain must not include 0
  .range([0, 600])
  .base(10);           // default is 10

x(10);   // 200
x(100);  // 400
x(1000); // 600
```

### scalePow / scaleSqrt

Power scales — apply an exponent to the input.

```javascript
const area = d3.scalePow()
  .exponent(2)
  .domain([0, 100])
  .range([0, 500]);

// Shorthand for exponent(0.5)
const radius = d3.scaleSqrt()
  .domain([0, 100])
  .range([0, 30]);
```

### scaleSymlog

Symmetric log — handles zero and negative values (unlike scaleLog).

```javascript
const x = d3.scaleSymlog()
  .domain([-1000, 1000])
  .range([0, 800])
  .constant(1);  // determines linearity around zero
```

### Clamping

```javascript
const x = d3.scaleLinear([0, 100], [0, 800]).clamp(true);
x(150); // 800 (clamped, without clamp would be 1200)
x(-10); // 0   (clamped)
```

### Nice

Extends domain to round values:

```javascript
const x = d3.scaleLinear()
  .domain([0.241, 0.789])
  .nice();  // domain becomes [0.2, 0.8]
```

## Time Scales

Maps temporal domains (Date objects) to continuous ranges.

### scaleTime / scaleUtc

```javascript
const x = d3.scaleTime()
  .domain([new Date("2024-01-01"), new Date("2024-12-31")])
  .range([0, 800]);

x(new Date("2024-07-01")); // ~400

// UTC variant (avoids timezone issues — recommended)
const x = d3.scaleUtc()
  .domain([new Date("2024-01-01"), new Date("2024-12-31")])
  .range([0, 800]);
```

**Ticks with time intervals:**
```javascript
x.ticks(d3.timeMonth.every(1));  // tick per month
x.ticks(d3.timeWeek.every(2));   // tick every 2 weeks
x.tickFormat(d3.timeFormat("%b %Y")); // "Jan 2024"
```

## Sequential and Diverging Scales

For mapping data to color gradients.

### scaleSequential

Maps a continuous domain to an interpolated color range.

```javascript
const color = d3.scaleSequential()
  .domain([0, 100])
  .interpolator(d3.interpolateBlues);

color(0);   // light blue
color(50);  // medium blue
color(100); // dark blue
```

**Built-in interpolators:**
```javascript
d3.scaleSequential([0, 100], d3.interpolateViridis)
d3.scaleSequential([0, 100], d3.interpolatePlasma)
d3.scaleSequential([0, 100], d3.interpolateInferno)
d3.scaleSequential([0, 100], d3.interpolateWarm)
d3.scaleSequential([0, 100], d3.interpolateCool)
d3.scaleSequential([0, 100], d3.interpolateYlGnBu)
d3.scaleSequential([0, 100], d3.interpolateRdYlBu)
```

### scaleDiverging

For data with a meaningful midpoint (e.g., positive/negative).

```javascript
const color = d3.scaleDiverging()
  .domain([-1, 0, 1])  // three values: min, mid, max
  .interpolator(d3.interpolateRdBu);

color(-1); // red
color(0);  // white
color(1);  // blue
```

## Quantize Quantile Threshold

Discrete output scales — continuous input, discrete output.

### scaleQuantize

Divides domain into uniform segments, maps each to a discrete range value.

```javascript
const color = d3.scaleQuantize()
  .domain([0, 100])
  .range(["#fee", "#fcc", "#f99", "#f66", "#f00"]);

color(10);  // "#fee" (0-20 segment)
color(50);  // "#f99" (40-60 segment)
color(95);  // "#f00" (80-100 segment)
```

### scaleQuantile

Divides data into quantiles based on observed values.

```javascript
const color = d3.scaleQuantile()
  .domain([1, 2, 3, 4, 5, 100])  // actual data values
  .range(["low", "medium", "high"]);

// Thresholds based on distribution, not uniform intervals
color.quantiles(); // [2.5, 4.5]
```

### scaleThreshold

Maps values based on explicit thresholds.

```javascript
const color = d3.scaleThreshold()
  .domain([0, 50, 100])
  .range(["negative", "low", "medium", "high"]);

color(-10); // "negative"
color(25);  // "low"
color(75);  // "medium"
color(150); // "high"
```

## Ordinal Scales

Map discrete domains to discrete ranges.

### scaleOrdinal

```javascript
const color = d3.scaleOrdinal()
  .domain(["apple", "banana", "cherry"])
  .range(["red", "yellow", "darkred"]);

color("apple");  // "red"
color("banana"); // "yellow"
color("grape");  // "red" (cycles through range)
```

**Built-in categorical schemes:**
```javascript
const color = d3.scaleOrdinal(d3.schemeCategory10);
// 10 distinct colors for categories

const color = d3.scaleOrdinal(d3.schemeTableau10);
// Tableau-style 10 colors

// Other schemes: schemePaired, schemeSet1, schemeSet2, schemeSet3,
// schemeDark2, schemeAccent, schemeObservable10
```

## Band and Point Scales

For positioning categorical data (bar charts, dot plots).

### scaleBand

Divides range into uniform bands with optional padding.

```javascript
const x = d3.scaleBand()
  .domain(["A", "B", "C", "D"])
  .range([0, 400])
  .padding(0.1);        // fraction of step

x("A");          // left edge of band A
x.bandwidth();   // width of each band
x.step();        // distance between band starts

// Inner/outer padding separately
x.paddingInner(0.1);  // between bands
x.paddingOuter(0.05); // at edges
```

**Bar chart usage:**
```javascript
svg.selectAll("rect")
  .data(data)
  .join("rect")
    .attr("x", d => x(d.name))
    .attr("y", d => y(d.value))
    .attr("width", x.bandwidth())
    .attr("height", d => height - y(d.value));
```

### scalePoint

Like scaleBand but for points (zero bandwidth).

```javascript
const x = d3.scalePoint()
  .domain(["A", "B", "C", "D"])
  .range([0, 400])
  .padding(0.5);

x("A"); // point position for A
x.step(); // distance between points
```

## Common Methods

Methods shared across most scale types:

```javascript
// Domain and range
scale.domain()          // get domain
scale.domain([0, 100])  // set domain
scale.range()           // get range
scale.range([0, 800])   // set range

// Invert (continuous scales only)
scale.invert(400)       // range → domain value

// Ticks (continuous scales only)
scale.ticks(10)         // ~10 evenly spaced domain values
scale.tickFormat(10, ".0%") // format ticks as percentages

// Copy
const copy = scale.copy(); // independent copy
```

### Auto-domain from data

```javascript
const x = d3.scaleLinear()
  .domain(d3.extent(data, d => d.value))  // [min, max]
  .range([0, width]);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value)]) // [0, max]
  .range([height, 0])                       // inverted for SVG y-axis
  .nice();                                  // round to nice values
```

## Choosing a Scale

| Data Type | Visual Encoding | Scale |
|:----------|:---------------|:------|
| Continuous numbers | Position | `scaleLinear` |
| Numbers spanning orders of magnitude | Position | `scaleLog` |
| Data with zero and negatives (wide range) | Position | `scaleSymlog` |
| Dates/times | Position | `scaleUtc` / `scaleTime` |
| Continuous numbers | Sequential color | `scaleSequential` |
| Continuous numbers (with midpoint) | Diverging color | `scaleDiverging` |
| Continuous → discrete buckets | Color | `scaleQuantize` |
| Data distribution → buckets | Color | `scaleQuantile` |
| Explicit breakpoints → buckets | Color | `scaleThreshold` |
| Categories | Color | `scaleOrdinal` |
| Categories | Position (bars) | `scaleBand` |
| Categories | Position (dots) | `scalePoint` |
| Area/radius | Size | `scaleSqrt` |
