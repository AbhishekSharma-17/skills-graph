# D3 Hierarchies

> Source: [d3-hierarchy](https://d3js.org/d3-hierarchy) | Module: `d3-hierarchy`

## Table of Contents

- [Overview](#overview)
- [Creating Hierarchies](#creating-hierarchies)
- [Node Methods](#node-methods)
- [Tree Layout](#tree-layout)
- [Treemap Layout](#treemap-layout)
- [Pack Layout](#pack-layout)
- [Partition Layout](#partition-layout)
- [Cluster Layout](#cluster-layout)
- [Stratify](#stratify)
- [Common Patterns](#common-patterns)

## Overview

The hierarchy module provides layout algorithms for visualizing tree-structured data. Five layout types produce coordinates from hierarchical data:

| Layout | Visualization | Key Property |
|:-------|:-------------|:-------------|
| **tree** | Node-link diagram (dendrogram) | Tidy arrangement |
| **treemap** | Nested rectangles | Area proportional to value |
| **pack** | Nested circles | Area proportional to value |
| **partition** | Adjacency diagram (icicle/sunburst) | Space-filling |
| **cluster** | Node-link with leaves aligned | Leaves at same depth |

## Creating Hierarchies

### d3.hierarchy(data, children)

Constructs a root node from nested data:

```javascript
const data = {
  name: "root",
  children: [
    {
      name: "A",
      children: [
        { name: "A1", value: 10 },
        { name: "A2", value: 20 }
      ]
    },
    {
      name: "B",
      children: [
        { name: "B1", value: 30 }
      ]
    }
  ]
};

const root = d3.hierarchy(data)
  .sum(d => d.value)     // compute cumulative values
  .sort((a, b) => b.value - a.value); // sort by value
```

### Custom children accessor

```javascript
const root = d3.hierarchy(data, d => d.items);
// uses d.items instead of d.children
```

## Node Methods

Each node in the hierarchy has:

| Property | Description |
|:---------|:------------|
| `node.data` | Original data object |
| `node.depth` | Distance from root (root = 0) |
| `node.height` | Distance to deepest leaf |
| `node.parent` | Parent node (null for root) |
| `node.children` | Array of child nodes |
| `node.value` | Aggregated value (after `.sum()`) |

### Traversal methods

```javascript
root.descendants()   // array of all nodes (pre-order)
root.ancestors()     // array from node to root
root.leaves()        // array of leaf nodes only
root.links()         // array of { source, target } objects
root.path(target)    // path from node to target

root.each(node => console.log(node.data.name))       // pre-order
root.eachBefore(node => console.log(node.data.name))  // pre-order
root.eachAfter(node => console.log(node.data.name))   // post-order
```

### Aggregation

```javascript
// Sum leaf values up the tree
root.sum(d => d.value);

// Count leaves
root.count();

// Sort children
root.sort((a, b) => b.height - a.height || b.value - a.value);
```

### Find

```javascript
root.find(node => node.data.name === "A1");
```

## Tree Layout

Produces a "tidy" node-link tree diagram with nodes at x, y coordinates.

```javascript
const root = d3.hierarchy(data).sort((a, b) => b.height - a.height);
const treeLayout = d3.tree().size([width, height]);
treeLayout(root);

// Now each node has .x and .y

// Draw links
svg.selectAll("path")
  .data(root.links())
  .join("path")
    .attr("d", d3.linkVertical()
      .x(d => d.x)
      .y(d => d.y))
    .attr("fill", "none")
    .attr("stroke", "#ccc");

// Draw nodes
svg.selectAll("circle")
  .data(root.descendants())
  .join("circle")
    .attr("cx", d => d.x)
    .attr("cy", d => d.y)
    .attr("r", 4)
    .attr("fill", d => d.children ? "#555" : "#999");

// Draw labels
svg.selectAll("text")
  .data(root.descendants())
  .join("text")
    .attr("x", d => d.x)
    .attr("y", d => d.y - 10)
    .attr("text-anchor", "middle")
    .text(d => d.data.name);
```

### Tree options

```javascript
d3.tree()
  .size([width, height])           // fit to dimensions
  .nodeSize([dx, dy])              // fixed node spacing
  .separation((a, b) =>            // space between nodes
    a.parent === b.parent ? 1 : 2
  );
```

### Horizontal tree (swap x/y)

```javascript
const treeLayout = d3.tree().size([height, width]);
treeLayout(root);

svg.selectAll("path")
  .data(root.links())
  .join("path")
    .attr("d", d3.linkHorizontal()
      .x(d => d.y)    // swap x and y
      .y(d => d.x))
    .attr("fill", "none")
    .attr("stroke", "#ccc");
```

## Treemap Layout

Subdivides a rectangle into nested rectangles proportional to value.

```javascript
const root = d3.hierarchy(data)
  .sum(d => d.value)
  .sort((a, b) => b.value - a.value);

const treemap = d3.treemap()
  .size([width, height])
  .padding(1)
  .round(true);

treemap(root);
// Each node now has: x0, y0, x1, y1

svg.selectAll("rect")
  .data(root.leaves())
  .join("rect")
    .attr("x", d => d.x0)
    .attr("y", d => d.y0)
    .attr("width", d => d.x1 - d.x0)
    .attr("height", d => d.y1 - d.y0)
    .attr("fill", d => color(d.parent.data.name));
```

### Treemap tiling algorithms

```javascript
d3.treemapBinary        // balanced binary (default)
d3.treemapDice          // horizontal subdivision
d3.treemapSlice         // vertical subdivision
d3.treemapSliceDice     // alternating slice/dice by depth
d3.treemapSquarify      // squarified — most square-like (best readability)
d3.treemapResquarify    // like squarify but stable on updates

treemap.tile(d3.treemapSquarify);
```

### Treemap options

```javascript
d3.treemap()
  .size([width, height])
  .padding(2)              // padding around groups
  .paddingInner(1)         // between siblings
  .paddingOuter(2)         // between parent boundary
  .paddingTop(20)          // space for group labels
  .round(true);            // integer coordinates
```

## Pack Layout

Enclosure diagram using nested circles.

```javascript
const root = d3.hierarchy(data)
  .sum(d => d.value)
  .sort((a, b) => b.value - a.value);

const pack = d3.pack()
  .size([width, height])
  .padding(3);

pack(root);
// Each node now has: x, y, r (center and radius)

svg.selectAll("circle")
  .data(root.descendants())
  .join("circle")
    .attr("cx", d => d.x)
    .attr("cy", d => d.y)
    .attr("r", d => d.r)
    .attr("fill", d => d.children ? "none" : color(d.data.name))
    .attr("stroke", d => d.children ? "#ccc" : "none");
```

## Partition Layout

Space-filling adjacency diagram (icicle chart, or sunburst when projected radially).

```javascript
const root = d3.hierarchy(data)
  .sum(d => d.value)
  .sort((a, b) => b.value - a.value);

const partition = d3.partition()
  .size([width, height])
  .padding(1)
  .round(true);

partition(root);
// Each node has: x0, y0, x1, y1

// Icicle chart
svg.selectAll("rect")
  .data(root.descendants())
  .join("rect")
    .attr("x", d => d.x0)
    .attr("y", d => d.y0)
    .attr("width", d => d.x1 - d.x0)
    .attr("height", d => d.y1 - d.y0)
    .attr("fill", d => color(d.data.name));
```

### Sunburst (radial partition)

```javascript
const partition = d3.partition()
  .size([2 * Math.PI, radius]);  // angular, radial

partition(root);

const arc = d3.arc()
  .startAngle(d => d.x0)
  .endAngle(d => d.x1)
  .innerRadius(d => d.y0)
  .outerRadius(d => d.y1);

svg.selectAll("path")
  .data(root.descendants())
  .join("path")
    .attr("d", arc)
    .attr("fill", d => color(d.data.name))
    .attr("transform", `translate(${width/2},${height/2})`);
```

## Cluster Layout

Like tree but all leaves are at the same depth.

```javascript
const cluster = d3.cluster()
  .size([width, height]);

const root = d3.hierarchy(data);
cluster(root);
// Same node.x, node.y as tree, but leaves aligned
```

## Stratify

Convert flat tabular data (with id/parent columns) into a hierarchy:

```javascript
const table = [
  { id: "root", parent: null },
  { id: "A",    parent: "root" },
  { id: "B",    parent: "root" },
  { id: "A1",   parent: "A", value: 10 },
  { id: "A2",   parent: "A", value: 20 },
  { id: "B1",   parent: "B", value: 30 }
];

const root = d3.stratify()
  .id(d => d.id)
  .parentId(d => d.parent)
(table);

root.sum(d => d.value);
// Now use with any layout
```

### From CSV

```javascript
const data = await d3.csv("categories.csv");
// CSV: id,parentId,value
//      root,,
//      fruits,root,
//      apple,fruits,10

const root = d3.stratify()(data);
```

## Common Patterns

### Zoomable treemap

```javascript
function zoom(event, d) {
  const x = d3.scaleLinear().domain([d.x0, d.x1]).range([0, width]);
  const y = d3.scaleLinear().domain([d.y0, d.y1]).range([0, height]);

  svg.selectAll("rect")
    .transition().duration(750)
    .attr("x", d => x(d.x0))
    .attr("y", d => y(d.y0))
    .attr("width", d => x(d.x1) - x(d.x0))
    .attr("height", d => y(d.y1) - y(d.y0));
}
```

### Breadcrumb trail

```javascript
function breadcrumb(node) {
  return node.ancestors().reverse().map(d => d.data.name).join(" > ");
}
```
