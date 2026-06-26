# D3 Transitions

> Source: [d3-transition](https://d3js.org/d3-transition) | [d3-ease](https://d3js.org/d3-ease) | Module: `d3-transition`

## Table of Contents

- [Overview](#overview)
- [Creating Transitions](#creating-transitions)
- [Modifying Elements](#modifying-elements)
- [Timing Control](#timing-control)
- [Easing Functions](#easing-functions)
- [Interpolation](#interpolation)
- [Chaining Transitions](#chaining-transitions)
- [Custom Tweens](#custom-tweens)
- [Events](#events)
- [Common Patterns](#common-patterns)

## Overview

A transition is a selection-like interface for animating changes to the DOM. Instead of applying changes instantaneously, transitions smoothly interpolate from the current state to the target state over a specified duration.

```javascript
d3.selectAll("circle")
  .transition()
  .duration(750)
  .attr("r", 30)
  .attr("fill", "orange");
```

D3 automatically detects and interpolates numbers, colors, strings with embedded numbers, transforms, and SVG paths.

## Creating Transitions

### selection.transition()

Creates a transition on the selection:

```javascript
const t = d3.selectAll("rect")
  .transition()
  .duration(500);
```

### Named transitions

Transitions can be named to allow concurrent independent animations:

```javascript
d3.selectAll("circle")
  .transition("position")
    .duration(500)
    .attr("cx", d => x(d.x))
  .transition("color")
    .duration(1000)
    .attr("fill", "red");
```

### d3.transition()

Create a standalone transition (for synchronizing):

```javascript
const t = d3.transition()
  .duration(750)
  .ease(d3.easeCubicInOut);

// Use on multiple selections (synchronized timing)
svg.selectAll("rect")
  .transition(t)
  .attr("height", d => y(d.value));

svg.selectAll("text")
  .transition(t)
  .attr("y", d => y(d.value) - 5);
```

## Modifying Elements

### transition.attr(name, value)

Animate attribute values:

```javascript
selection.transition()
  .attr("r", 50)           // number
  .attr("fill", "red")     // color
  .attr("transform", `translate(100,200) scale(2)`); // transform
```

### transition.style(name, value)

Animate CSS styles:

```javascript
selection.transition()
  .style("opacity", 0.5)
  .style("background-color", "blue")
  .style("font-size", "24px");
```

### transition.text(value)

Set text at the start of the transition:

```javascript
selection.transition()
  .text(d => d3.format(",.0f")(d.value));
```

### transition.remove()

Remove elements when transition ends:

```javascript
selection.transition()
  .duration(500)
  .style("opacity", 0)
  .remove();  // element removed after fade-out completes
```

## Timing Control

### transition.duration(ms)

Set animation duration in milliseconds (default: 250):

```javascript
selection.transition().duration(1000); // 1 second
```

### transition.delay(ms)

Set delay before animation starts:

```javascript
// Fixed delay
selection.transition().delay(200).duration(500);

// Staggered delay based on index
selection.transition()
  .delay((d, i) => i * 50)  // each element starts 50ms after previous
  .duration(500)
  .attr("r", 30);
```

### Staggered entrance pattern

```javascript
svg.selectAll("rect")
  .data(data)
  .join("rect")
    .attr("x", d => x(d.name))
    .attr("y", height)          // start at bottom
    .attr("height", 0)          // start with 0 height
    .attr("width", x.bandwidth())
    .attr("fill", "steelblue")
  .transition()
    .delay((d, i) => i * 100)   // stagger by 100ms
    .duration(750)
    .attr("y", d => y(d.value))
    .attr("height", d => height - y(d.value));
```

## Easing Functions

### transition.ease(easing)

Control acceleration profile (default: `d3.easeCubicInOut`):

```javascript
selection.transition()
  .ease(d3.easeLinear)      // constant speed
  .duration(1000)
  .attr("cx", 500);
```

### Available easing functions

| Function | In | Out | InOut | Description |
|:---------|:---|:----|:------|:------------|
| `easeLinear` | — | — | — | Constant speed |
| `easeQuad` | `easeQuadIn` | `easeQuadOut` | `easeQuadInOut` | Quadratic |
| `easeCubic` | `easeCubicIn` | `easeCubicOut` | `easeCubicInOut` | Cubic (default) |
| `easePoly` | `easePolyIn` | `easePolyOut` | `easePolyInOut` | Polynomial |
| `easeSin` | `easeSinIn` | `easeSinOut` | `easeSinInOut` | Sinusoidal |
| `easeExp` | `easeExpIn` | `easeExpOut` | `easeExpInOut` | Exponential |
| `easeCircle` | `easeCircleIn` | `easeCircleOut` | `easeCircleInOut` | Circular |
| `easeElastic` | `easeElasticIn` | `easeElasticOut` | `easeElasticInOut` | Spring |
| `easeBack` | `easeBackIn` | `easeBackOut` | `easeBackInOut` | Overshoot |
| `easeBounce` | `easeBounceIn` | `easeBounceOut` | `easeBounceInOut` | Bounce |

**In/Out/InOut variants:**
- **In** — starts slow, accelerates
- **Out** — starts fast, decelerates
- **InOut** — slow start and end, fast middle

```javascript
// Configurable easing
d3.easePoly.exponent(3)     // custom polynomial
d3.easeElastic.amplitude(1.5).period(0.4) // custom elastic
d3.easeBack.overshoot(2)   // custom overshoot
```

## Interpolation

D3 automatically selects interpolators based on value types:

### Automatic detection

```javascript
// Numbers → d3.interpolateNumber
.attr("r", 50)

// Colors → d3.interpolateRgb
.attr("fill", "red")
.style("background-color", "#ff0000")

// Strings with numbers → d3.interpolateString
.style("font-size", "24px")

// Transforms → d3.interpolateTransformSvg
.attr("transform", "translate(100,200) scale(2)")

// Paths → d3.interpolateString (matched segments)
.attr("d", newPathData)
```

### Custom interpolation

```javascript
// RGB color space (default for colors)
.attrTween("fill", function() {
  return d3.interpolateRgb("blue", "red");
})

// HCL color space (perceptually uniform)
.attrTween("fill", function() {
  return d3.interpolateHcl("blue", "red");
})

// HSL with longer hue arc
.attrTween("fill", function() {
  return d3.interpolateHslLong("blue", "red");
})
```

## Chaining Transitions

### Sequential transitions

```javascript
d3.select("circle")
  .transition()
    .duration(500)
    .attr("r", 50)
  .transition()             // starts after previous ends
    .duration(500)
    .attr("fill", "red")
  .transition()
    .duration(500)
    .attr("r", 10);
```

### Waiting for transitions

```javascript
selection.transition()
  .duration(500)
  .attr("r", 50)
  .end()                   // returns a Promise
  .then(() => {
    console.log("Transition complete");
  });

// async/await
await selection.transition().duration(500).attr("r", 50).end();
```

## Custom Tweens

### transition.attrTween(name, factory)

Full control over attribute interpolation:

```javascript
// Animate a number with formatting
selection.transition()
  .duration(1000)
  .attrTween("text", function() {
    const i = d3.interpolateNumber(0, 1000);
    return function(t) {
      return d3.format(",.0f")(i(t));
    };
  });
```

### transition.styleTween(name, factory)

```javascript
selection.transition()
  .styleTween("color", function() {
    return d3.interpolateRgb("blue", "red");
  });
```

### transition.tween(name, factory)

General-purpose tween for side effects:

```javascript
// Animate a counter
selection.transition()
  .duration(2000)
  .tween("counter", function() {
    const el = this;
    const i = d3.interpolateNumber(0, 100);
    return function(t) {
      el.textContent = Math.round(i(t));
    };
  });
```

## Events

### transition.on(type, listener)

Listen for transition lifecycle events:

```javascript
selection.transition()
  .duration(500)
  .attr("r", 50)
  .on("start", function() {
    d3.select(this).attr("fill", "orange");
  })
  .on("end", function() {
    d3.select(this).attr("fill", "green");
  })
  .on("interrupt", function() {
    console.log("Transition was interrupted");
  });
```

### d3.active(node, name)

Get the active transition on a node:

```javascript
function repeat() {
  d3.active(this)
    .attr("cx", width)
    .transition()
      .attr("cx", 0)
      .transition()
        .on("start", repeat);
}

circle.transition()
  .on("start", repeat)
  .attr("cx", width);
```

## Common Patterns

### Animated data updates

```javascript
function update(data) {
  const t = svg.transition().duration(750);

  svg.selectAll("rect")
    .data(data, d => d.id)
    .join(
      enter => enter.append("rect")
        .attr("fill", "green")
        .attr("x", d => x(d.name))
        .attr("y", height)
        .attr("height", 0)
        .attr("width", x.bandwidth())
        .call(enter => enter.transition(t)
          .attr("y", d => y(d.value))
          .attr("height", d => height - y(d.value))),
      update => update
        .attr("fill", "steelblue")
        .call(update => update.transition(t)
          .attr("y", d => y(d.value))
          .attr("height", d => height - y(d.value))),
      exit => exit
        .attr("fill", "red")
        .call(exit => exit.transition(t)
          .attr("y", height)
          .attr("height", 0)
          .remove())
    );
}
```

### Morph between shapes

```javascript
// Ensure both paths have same number of segments
selection.transition()
  .duration(1000)
  .attr("d", newPath);  // D3 interpolates path segments
```

### Interrupted transitions

When a new transition starts on an element that already has one running, the old transition is interrupted. This is intentional — it prevents animations from queuing up during rapid interactions.
