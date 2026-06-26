# D3 Force Simulations

> Source: [d3-force](https://d3js.org/d3-force) | Module: `d3-force`

## Table of Contents

- [Overview](#overview)
- [Creating a Simulation](#creating-a-simulation)
- [Force Types](#force-types)
- [Simulation Control](#simulation-control)
- [Nodes and Links Data](#nodes-and-links-data)
- [Event Handling](#event-handling)
- [Interactive Force Graphs](#interactive-force-graphs)
- [Performance Tips](#performance-tips)

## Overview

The force module implements a velocity Verlet numerical integrator for simulating physical forces on particles. Forces can push nodes together or apart, attract nodes toward a center, keep nodes within bounds, or maintain link distances.

Primary use cases: network graphs, collision detection, bubble charts, constraint-based layouts.

## Creating a Simulation

### d3.forceSimulation(nodes)

Creates a simulation with the given nodes:

```javascript
const nodes = [
  { id: "A" },
  { id: "B" },
  { id: "C" }
];

const simulation = d3.forceSimulation(nodes)
  .force("charge", d3.forceManyBody())
  .force("center", d3.forceCenter(width / 2, height / 2))
  .on("tick", ticked);

function ticked() {
  // Update positions — nodes now have .x and .y
  svg.selectAll("circle")
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);
}
```

The simulation automatically starts and runs for ~300 ticks, cooling down via alpha decay.

## Force Types

### forceCenter(x, y)

Moves nodes toward the center of gravity (does not change relative positions):

```javascript
d3.forceCenter(width / 2, height / 2)
  .strength(0.1)  // default: 1
```

### forceManyBody()

N-body charge force — positive attracts, negative repels:

```javascript
d3.forceManyBody()
  .strength(-30)           // negative = repulsion (default: -30)
  .distanceMin(1)          // minimum distance
  .distanceMax(Infinity)   // maximum distance
  .theta(0.9)              // Barnes-Hut approximation (lower = more accurate)
```

### forceLink(links)

Spring force between connected nodes:

```javascript
const links = [
  { source: "A", target: "B" },
  { source: "B", target: "C" }
];

d3.forceLink(links)
  .id(d => d.id)           // node identity accessor
  .distance(50)            // target link length (default: 30)
  .strength(1)             // spring strength (0-1)
  .iterations(1)           // constraint iterations per tick
```

### forceCollide(radius)

Prevents node overlap by treating nodes as circles:

```javascript
d3.forceCollide()
  .radius(d => d.radius + 2)  // collision radius
  .strength(0.7)               // force strength (0-1)
  .iterations(2)               // iterations per tick
```

### forceX(x) / forceY(y)

Position forces that push nodes toward target coordinates:

```javascript
d3.forceX(width / 2).strength(0.1)   // pull toward x center
d3.forceY(height / 2).strength(0.1)  // pull toward y center

// Cluster by category
d3.forceX(d => clusterX(d.category)).strength(0.5)
d3.forceY(d => clusterY(d.category)).strength(0.5)
```

### forceRadial(radius, x, y)

Push nodes toward a circle of given radius:

```javascript
d3.forceRadial(200, width / 2, height / 2)
  .strength(0.8)

// Different radii by group
d3.forceRadial(d => d.group === "inner" ? 100 : 300, cx, cy)
```

## Simulation Control

### Alpha (cooling parameter)

Alpha controls how much the simulation moves on each tick. It starts at 1 and decays toward alphaMin (default: 0.001), at which point the simulation stops.

```javascript
simulation.alpha()              // get current alpha (0-1)
simulation.alpha(1)             // set alpha (restarts motion)
simulation.alphaMin(0.001)      // stop threshold (default)
simulation.alphaDecay(0.0228)   // decay rate per tick (default)
simulation.alphaTarget(0)       // target alpha (default: 0)
```

### Velocity decay

Friction-like parameter:

```javascript
simulation.velocityDecay(0.4)   // 0 = no friction, 1 = frozen (default: 0.4)
```

### Start / stop

```javascript
simulation.restart()   // restart (set alpha to alphaTarget)
simulation.stop()      // stop the simulation timer
simulation.tick()      // advance one tick manually
simulation.tick(100)   // advance 100 ticks (for static layout)
```

### Reheat the simulation

```javascript
// When data changes, reheat to re-run layout
simulation.alpha(0.3).restart();

// When adding/removing forces
simulation.force("charge", d3.forceManyBody().strength(-50));
simulation.alpha(1).restart();
```

## Nodes and Links Data

### Node properties

The simulation adds these mutable properties to each node:

| Property | Description |
|:---------|:------------|
| `x` | Current x position |
| `y` | Current y position |
| `vx` | Current x velocity |
| `vy` | Current y velocity |
| `fx` | Fixed x position (if set) |
| `fy` | Fixed y position (if set) |
| `index` | Node index in array |

### Fixing node positions

```javascript
// Pin a node to specific coordinates
node.fx = 200;
node.fy = 300;

// Unpin
node.fx = null;
node.fy = null;
```

### Updating nodes

```javascript
simulation.nodes(newNodes);  // update node array
simulation.alpha(0.3).restart();
```

### Updating links

```javascript
simulation.force("link").links(newLinks);
simulation.alpha(0.3).restart();
```

## Event Handling

### simulation.on(typenames, listener)

```javascript
simulation.on("tick", () => {
  // Called every simulation tick
  nodeElements.attr("cx", d => d.x).attr("cy", d => d.y);
  linkElements
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
});

simulation.on("end", () => {
  console.log("Simulation finished");
});
```

## Interactive Force Graphs

### Complete force-directed graph

```javascript
const nodes = [
  { id: "A", group: 1 },
  { id: "B", group: 1 },
  { id: "C", group: 2 },
  { id: "D", group: 2 }
];

const links = [
  { source: "A", target: "B" },
  { source: "B", target: "C" },
  { source: "C", target: "D" },
  { source: "A", target: "D" }
];

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(20));

// Draw links
const link = svg.selectAll("line")
  .data(links)
  .join("line")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6);

// Draw nodes
const node = svg.selectAll("circle")
  .data(nodes)
  .join("circle")
    .attr("r", 10)
    .attr("fill", d => color(d.group));

simulation.on("tick", () => {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);
});
```

### Drag behavior on force nodes

```javascript
function drag(simulation) {
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;  // unpin after drag
    d.fy = null;
  }

  return d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended);
}

// Apply to nodes
node.call(drag(simulation));
```

### Bounding box constraint

```javascript
simulation.on("tick", () => {
  node
    .attr("cx", d => d.x = Math.max(r, Math.min(width - r, d.x)))
    .attr("cy", d => d.y = Math.max(r, Math.min(height - r, d.y)));
});
```

## Performance Tips

- **Use Canvas for large graphs** (>500 nodes) — SVG becomes slow
- **Increase alphaDecay** for faster convergence: `simulation.alphaDecay(0.05)`
- **Reduce iterations** on forceCollide and forceLink for speed
- **Use theta(0.9)** on forceManyBody for Barnes-Hut approximation
- **Stop simulation** when not visible: `simulation.stop()`
- **Pre-compute layout** for static graphs:
  ```javascript
  simulation.stop();
  for (let i = 0; i < 300; i++) simulation.tick();
  // Render once with final positions
  ```
