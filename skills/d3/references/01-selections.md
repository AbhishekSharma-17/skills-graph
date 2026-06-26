# D3 Selections

> Source: [d3-selection](https://d3js.org/d3-selection) | Module: `d3-selection`

## Table of Contents

- [Overview](#overview)
- [Selecting Elements](#selecting-elements)
- [Modifying Elements](#modifying-elements)
- [Data Joins](#data-joins)
- [The join Method](#the-join-method)
- [Enter Update Exit](#enter-update-exit)
- [Event Handling](#event-handling)
- [Control Flow](#control-flow)
- [Common Pitfalls](#common-pitfalls)

## Overview

Selections are D3's mechanism for querying and manipulating DOM elements. A selection is an array of arrays of DOM elements, grouped by parent node. Selections drive D3's data binding — the enter/update/exit pattern that creates, updates, and removes elements based on data.

## Selecting Elements

### d3.select(selector)

Selects the first matching element. Returns a selection containing one element (or null).

```javascript
d3.select("body")           // by tag
d3.select("#chart")          // by id
d3.select(".bar")            // by class
d3.select("svg > g:first-child") // CSS selector

// Select a specific DOM node
d3.select(document.getElementById("chart"))
```

### d3.selectAll(selector)

Selects all matching elements. Returns a selection of all matches.

```javascript
d3.selectAll("circle")       // all circles
d3.selectAll(".data-point")  // all with class
d3.selectAll("svg rect")     // nested selector
```

### Chained selection (scoping)

```javascript
// Select within a parent
const svg = d3.select("#chart");
const circles = svg.selectAll("circle"); // only circles inside #chart
```

### d3.create(name)

Creates a detached element (not yet in DOM):

```javascript
const svg = d3.create("svg")
  .attr("width", 640)
  .attr("height", 400);

// Append to DOM when ready
document.body.append(svg.node());
```

### selection.select(selector) / selection.selectAll(selector)

Sub-select within each element of an existing selection:

```javascript
const groups = d3.selectAll("g");
const rects = groups.selectAll("rect"); // all rects in each g
```

Key difference: `.select()` propagates parent data to child; `.selectAll()` does not.

## Modifying Elements

### Attributes

```javascript
selection.attr("width", 100)               // set attribute
selection.attr("width")                     // get attribute
selection.attr("fill", d => colorScale(d.category)) // data-driven
selection.attr("transform", `translate(${x},${y})`)
```

### Styles

```javascript
selection.style("color", "red")            // set inline style
selection.style("opacity", 0.5)
selection.style("font-size", d => `${d.size}px`)
selection.style("display", null)           // remove style
```

### Classes

```javascript
selection.classed("active", true)          // add class
selection.classed("active", false)         // remove class
selection.classed("active")                // check class
selection.classed("foo bar", true)         // multiple classes
selection.classed("highlight", d => d.value > 50) // conditional
```

### Text and HTML

```javascript
selection.text("Hello")                    // set text content
selection.text(d => d.label)               // data-driven text
selection.html("<strong>Bold</strong>")    // set inner HTML
```

### Properties

```javascript
selection.property("checked", true)        // checkbox
selection.property("value", "hello")       // input value
selection.property("__data__")             // access bound data
```

### Append and Insert

```javascript
selection.append("circle")                 // append child element
selection.append("g")                      // append group

// Insert before a reference element
selection.insert("rect", ":first-child")
selection.insert("line", ".axis")
```

### Remove

```javascript
selection.remove()  // remove selected elements from DOM
```

## Data Joins

The `.data()` method binds an array of data to selected elements.

```javascript
const data = [10, 20, 30, 40, 50];

// Bind data to existing circles
const circles = svg.selectAll("circle")
  .data(data);

// circles is now the "update" selection
// circles.enter() — data without elements
// circles.exit()  — elements without data
```

### Key function

By default, data is joined by index. Use a key function for object identity:

```javascript
const data = [
  { id: "a", value: 10 },
  { id: "b", value: 20 },
  { id: "c", value: 30 }
];

svg.selectAll("circle")
  .data(data, d => d.id)  // join by id, not index
  .join("circle")
    .attr("r", d => d.value);
```

### selection.datum(value)

Binds a single datum to each element (no join):

```javascript
svg.datum(dataset)  // bind entire dataset to svg
  .append("path")
    .attr("d", line);
```

## The join Method

The modern `join()` method (D3 v5+) replaces the verbose enter/update/exit pattern:

### Simple join

```javascript
svg.selectAll("rect")
  .data(data)
  .join("rect")
    .attr("x", (d, i) => i * 25)
    .attr("y", d => height - d)
    .attr("width", 20)
    .attr("height", d => d)
    .attr("fill", "steelblue");
```

### join with enter/update/exit callbacks

```javascript
svg.selectAll("circle")
  .data(data, d => d.id)
  .join(
    enter => enter.append("circle")
      .attr("r", 0)
      .attr("fill", "green")
      .call(enter => enter.transition()
        .attr("r", d => d.radius)),

    update => update
      .attr("fill", "blue")
      .call(update => update.transition()
        .attr("r", d => d.radius)),

    exit => exit
      .attr("fill", "red")
      .call(exit => exit.transition()
        .attr("r", 0)
        .remove())
  );
```

## Enter Update Exit

The classic pattern (pre-join, still valid):

```javascript
const bars = svg.selectAll("rect")
  .data(data, d => d.id);

// ENTER: create elements for new data
bars.enter()
  .append("rect")
    .attr("x", d => x(d.name))
    .attr("y", d => y(d.value))
    .attr("width", x.bandwidth())
    .attr("height", d => height - y(d.value))
    .attr("fill", "steelblue");

// UPDATE: modify existing elements
bars
  .attr("y", d => y(d.value))
  .attr("height", d => height - y(d.value));

// EXIT: remove elements without data
bars.exit().remove();
```

### Merge (combining enter + update)

```javascript
const entered = bars.enter().append("rect");
bars.merge(entered)
  .attr("x", d => x(d.name))
  .attr("y", d => y(d.value))
  .attr("width", x.bandwidth())
  .attr("height", d => height - y(d.value));

bars.exit().remove();
```

## Event Handling

### selection.on(typenames, listener)

```javascript
// Mouse events
selection.on("click", function(event, d) {
  console.log("Clicked:", d);
  console.log("Element:", this);
  console.log("Mouse position:", d3.pointer(event));
});

selection.on("mouseover", (event, d) => {
  d3.select(event.currentTarget).attr("fill", "orange");
});

selection.on("mouseout", (event, d) => {
  d3.select(event.currentTarget).attr("fill", "steelblue");
});

// Multiple event types
selection.on("mouseover.highlight", highlightFn)
         .on("mouseover.tooltip", tooltipFn);

// Remove listener
selection.on("click", null);
```

### d3.pointer(event, target)

Returns [x, y] coordinates relative to the target element:

```javascript
svg.on("click", function(event) {
  const [x, y] = d3.pointer(event);
  svg.append("circle").attr("cx", x).attr("cy", y).attr("r", 5);
});
```

### d3.pointers(event, target)

Returns array of [x, y] for multi-touch:

```javascript
svg.on("touchmove", function(event) {
  const points = d3.pointers(event);
  // points is [[x1,y1], [x2,y2], ...]
});
```

## Control Flow

### selection.each(function)

Iterate over each element:

```javascript
selection.each(function(d, i) {
  const el = d3.select(this);
  if (d.value > 50) {
    el.attr("fill", "red");
  }
});
```

### selection.call(function, ...args)

Invoke a function with the selection (enables reusable components):

```javascript
function addTooltip(selection, text) {
  selection.append("title").text(text);
}

svg.selectAll("rect")
  .data(data)
  .join("rect")
    .call(addTooltip, d => d.label);
```

### selection.filter(filter)

```javascript
selection.filter(d => d.value > 50)
  .attr("fill", "red");

selection.filter(".special")
  .style("font-weight", "bold");
```

### selection.sort(comparator)

```javascript
selection.sort((a, b) => d3.ascending(a.value, b.value));
```

### selection.order() / selection.raise() / selection.lower()

```javascript
selection.raise()  // move to front (last child)
selection.lower()  // move to back (first child)
selection.order()  // reorder DOM to match data order
```

### selection.nodes() / selection.node()

```javascript
selection.node()   // first non-null element
selection.nodes()  // array of all elements
selection.size()   // number of elements
selection.empty()  // true if selection is empty
```

## Common Pitfalls

**1. Forgetting selectAll before data join:**
```javascript
// Wrong — selects first existing circle only
svg.select("circle").data(data);

// Right — selects all (even if none exist yet)
svg.selectAll("circle").data(data).join("circle");
```

**2. Arrow functions vs regular functions:**
```javascript
// 'this' refers to DOM element only in regular functions
selection.on("click", function(event, d) {
  d3.select(this).attr("fill", "red"); // works
});

// With arrow functions, use event.currentTarget
selection.on("click", (event, d) => {
  d3.select(event.currentTarget).attr("fill", "red");
});
```

**3. select vs selectAll propagation:**
```javascript
// .select() propagates parent datum to child
parent.select("text").text(d => d.name); // d is parent's datum

// .selectAll() does NOT propagate — need new data bind
parent.selectAll("rect").data(d => d.values).join("rect");
```

**4. Stale closures when updating:**
```javascript
// Use .join() with callbacks to handle enter/update separately
// instead of applying attrs to the merged selection when transitions
// should differ between entering and updating elements
```
