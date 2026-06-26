# D3 Interactions

> Source: [d3-zoom](https://d3js.org/d3-zoom) | [d3-brush](https://d3js.org/d3-brush) | [d3-drag](https://d3js.org/d3-drag)

## Table of Contents

- [Overview](#overview)
- [Zoom and Pan](#zoom-and-pan)
- [Brushing](#brushing)
- [Dragging](#dragging)
- [Tooltips](#tooltips)
- [Click and Hover](#click-and-hover)
- [Combining Behaviors](#combining-behaviors)

## Overview

D3 provides three reusable interaction behaviors that handle mouse, touch, and wheel events:

| Behavior | Module | Purpose |
|:---------|:-------|:--------|
| **Zoom** | `d3-zoom` | Pan and zoom with mouse wheel, drag, pinch |
| **Brush** | `d3-brush` | Select regions by click-and-drag |
| **Drag** | `d3-drag` | Drag individual elements |

Each behavior uses `.call()` to attach event listeners and `.on()` for custom event handling.

## Zoom and Pan

### Basic zoom

```javascript
const zoom = d3.zoom()
  .scaleExtent([1, 8])    // min/max zoom level
  .on("zoom", zoomed);

svg.call(zoom);

function zoomed(event) {
  g.attr("transform", event.transform);
}
```

### Zoom with constraints

```javascript
const zoom = d3.zoom()
  .scaleExtent([0.5, 10])
  .translateExtent([[0, 0], [width, height]])  // pan bounds
  .extent([[0, 0], [width, height]])            // viewport
  .on("zoom", zoomed);
```

### Zoom transforms

The transform object has: `k` (scale), `x` (translate x), `y` (translate y).

```javascript
function zoomed(event) {
  const { k, x, y } = event.transform;

  // Apply to a group element (SVG)
  g.attr("transform", event.transform);

  // Or rescale axes
  gx.call(xAxis.scale(event.transform.rescaleX(xScale)));
  gy.call(yAxis.scale(event.transform.rescaleY(yScale)));
}
```

### Programmatic zoom

```javascript
// Zoom to a specific level
svg.transition().duration(750).call(zoom.scaleTo, 4);

// Pan to a position
svg.transition().duration(750).call(zoom.translateTo, 200, 300);

// Reset zoom
svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);

// Zoom to fit a specific element
function zoomToFeature(feature) {
  const [[x0, y0], [x1, y1]] = path.bounds(feature);
  svg.transition().duration(750).call(
    zoom.transform,
    d3.zoomIdentity
      .translate(width / 2, height / 2)
      .scale(Math.min(8, 0.9 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
      .translate(-(x0 + x1) / 2, -(y0 + y1) / 2)
  );
}
```

### Zoom events

```javascript
zoom.on("start", (event) => {
  // gesture started
});

zoom.on("zoom", (event) => {
  // transform changed
  // event.transform — current transform
  // event.sourceEvent — underlying input event
});

zoom.on("end", (event) => {
  // gesture ended
});
```

### Disable specific zoom gestures

```javascript
// Disable wheel zoom
svg.call(zoom).on("wheel.zoom", null);

// Disable double-click zoom
svg.call(zoom).on("dblclick.zoom", null);

// Custom filter (e.g., only zoom with ctrl+wheel)
zoom.filter(event => event.ctrlKey || event.type !== "wheel");
```

### Semantic zoom (rescale elements, not just translate)

```javascript
function zoomed(event) {
  const t = event.transform;

  // Update circle positions AND radius
  circles
    .attr("cx", d => t.applyX(x(d.x)))
    .attr("cy", d => t.applyY(y(d.y)))
    .attr("r", 5 / t.k);  // keep visual size constant

  // Update stroke width
  paths.attr("stroke-width", 1 / t.k);
}
```

## Brushing

### One-dimensional brush

```javascript
const brush = d3.brushX()
  .extent([[marginLeft, marginTop], [width - marginRight, height - marginBottom]])
  .on("end", brushed);

svg.append("g").call(brush);

function brushed(event) {
  if (!event.selection) return;  // cleared
  const [x0, x1] = event.selection;

  // Map pixel range back to data domain
  const [d0, d1] = event.selection.map(xScale.invert);

  // Highlight selected points
  circles.classed("selected", d => d.date >= d0 && d.date <= d1);
}
```

### Two-dimensional brush

```javascript
const brush = d3.brush()
  .extent([[0, 0], [width, height]])
  .on("brush end", brushed);

svg.append("g").call(brush);

function brushed(event) {
  if (!event.selection) return;
  const [[x0, y0], [x1, y1]] = event.selection;

  circles.classed("selected", d =>
    x(d.x) >= x0 && x(d.x) <= x1 &&
    y(d.y) >= y0 && y(d.y) <= y1
  );
}
```

### Focus + context (overview + detail)

```javascript
// Overview brush
const brushX = d3.brushX()
  .extent([[marginLeft, 0], [width - marginRight, overviewHeight]])
  .on("brush end", brushed);

overview.append("g").call(brushX);

function brushed(event) {
  if (!event.selection) return;
  const [x0, x1] = event.selection.map(overviewX.invert);

  // Update focus view domain
  focusX.domain([x0, x1]);
  focusArea.attr("d", area);
  focusXAxis.call(d3.axisBottom(focusX));
}
```

### Programmatic brush

```javascript
// Set brush selection
svg.select(".brush").call(brush.move, [100, 300]);

// Clear brush
svg.select(".brush").call(brush.clear);
```

### Snap brush to values

```javascript
function brushed(event) {
  if (!event.sourceEvent) return;  // ignore programmatic moves
  const [x0, x1] = event.selection.map(d => {
    const date = xScale.invert(d);
    return xScale(d3.timeDay.round(date));  // snap to day
  });
  d3.select(this).call(brush.move, [x0, x1]);
}
```

## Dragging

### Basic drag

```javascript
const drag = d3.drag()
  .on("start", dragstarted)
  .on("drag", dragged)
  .on("end", dragended);

circles.call(drag);

function dragstarted(event, d) {
  d3.select(this).raise().attr("stroke", "black");
}

function dragged(event, d) {
  d3.select(this)
    .attr("cx", d.x = event.x)
    .attr("cy", d.y = event.y);
}

function dragended(event, d) {
  d3.select(this).attr("stroke", null);
}
```

### Drag events

| Property | Description |
|:---------|:------------|
| `event.x` | Current x position |
| `event.y` | Current y position |
| `event.dx` | Change in x since last event |
| `event.dy` | Change in y since last event |
| `event.subject` | The drag subject |
| `event.active` | Number of active drags |
| `event.sourceEvent` | Underlying input event |

### Drag with Canvas

```javascript
const drag = d3.drag()
  .subject(event => {
    // Find closest circle to pointer
    return simulation.find(event.x, event.y, 20);
  })
  .on("start", dragstarted)
  .on("drag", dragged)
  .on("end", dragended);

d3.select(canvas).call(drag);
```

### Constrained drag

```javascript
function dragged(event, d) {
  d3.select(this)
    .attr("cx", d.x = Math.max(0, Math.min(width, event.x)))  // clamp x
    .attr("cy", d.y = Math.max(0, Math.min(height, event.y))); // clamp y
}
```

## Tooltips

D3 doesn't have a built-in tooltip module, but the standard pattern uses HTML div elements:

### HTML tooltip

```javascript
const tooltip = d3.select("body").append("div")
  .attr("class", "tooltip")
  .style("position", "absolute")
  .style("visibility", "hidden")
  .style("background", "white")
  .style("border", "1px solid #ccc")
  .style("padding", "8px")
  .style("border-radius", "4px")
  .style("pointer-events", "none");

circles
  .on("mouseover", (event, d) => {
    tooltip
      .style("visibility", "visible")
      .html(`<strong>${d.name}</strong><br>Value: ${d.value}`);
  })
  .on("mousemove", (event) => {
    tooltip
      .style("top", (event.pageY - 10) + "px")
      .style("left", (event.pageX + 10) + "px");
  })
  .on("mouseout", () => {
    tooltip.style("visibility", "hidden");
  });
```

### SVG title tooltip (simple)

```javascript
circles.append("title")
  .text(d => `${d.name}: ${d.value}`);
```

## Click and Hover

### Highlight on hover

```javascript
circles
  .on("mouseover", function(event, d) {
    d3.select(this)
      .transition().duration(200)
      .attr("r", 8)
      .attr("fill", "orange");
  })
  .on("mouseout", function(event, d) {
    d3.select(this)
      .transition().duration(200)
      .attr("r", 5)
      .attr("fill", d => color(d.category));
  });
```

### Click to select

```javascript
let selected = null;

circles.on("click", function(event, d) {
  if (selected === d) {
    selected = null;
    d3.select(this).attr("stroke", null);
  } else {
    circles.attr("stroke", null);  // deselect all
    selected = d;
    d3.select(this).attr("stroke", "black").attr("stroke-width", 2);
  }
});
```

### Voronoi hover (for dense scatterplots)

```javascript
const delaunay = d3.Delaunay.from(data, d => x(d.x), d => y(d.y));
const voronoi = delaunay.voronoi([0, 0, width, height]);

svg.selectAll("path.voronoi")
  .data(data)
  .join("path")
    .attr("d", (d, i) => voronoi.renderCell(i))
    .attr("fill", "transparent")
    .on("mouseover", (event, d) => highlight(d))
    .on("mouseout", () => unhighlight());
```

## Combining Behaviors

### Zoom + brush (mutually exclusive)

```javascript
let mode = "zoom";

const zoom = d3.zoom().on("zoom", zoomed);
const brush = d3.brushX().on("end", brushed);

function setMode(newMode) {
  mode = newMode;
  if (mode === "zoom") {
    svg.select(".brush").remove();
    svg.call(zoom);
  } else {
    svg.on(".zoom", null);
    svg.append("g").attr("class", "brush").call(brush);
  }
}
```

### Drag + zoom (on different elements)

```javascript
// Zoom on the SVG background
svg.call(zoom);

// Drag on individual elements (stops zoom propagation)
circles.call(drag);
circles.on("mousedown.zoom", null); // prevent zoom during drag
```
