# D3 Colors and Interpolation

> Source: [d3-color](https://d3js.org/d3-color) | [d3-interpolate](https://d3js.org/d3-interpolate) | [d3-scale-chromatic](https://d3js.org/d3-scale-chromatic)

## Table of Contents

- [Overview](#overview)
- [Color Parsing and Manipulation](#color-parsing-and-manipulation)
- [Color Spaces](#color-spaces)
- [Interpolation](#interpolation)
- [Color Schemes — Categorical](#color-schemes--categorical)
- [Color Schemes — Sequential](#color-schemes--sequential)
- [Color Schemes — Diverging](#color-schemes--diverging)
- [Choosing Color Schemes](#choosing-color-schemes)

## Overview

D3 provides three modules for working with color:

- **d3-color** — parse, convert, and manipulate colors across color spaces
- **d3-interpolate** — smoothly blend between values (numbers, colors, strings, arrays)
- **d3-scale-chromatic** — pre-built color schemes for data visualization

## Color Parsing and Manipulation

### d3.color(specifier)

Parse any CSS color string:

```javascript
d3.color("steelblue")           // rgb(70, 130, 180)
d3.color("#ff6600")              // rgb(255, 102, 0)
d3.color("rgb(255, 0, 0)")      // rgb(255, 0, 0)
d3.color("hsl(120, 50%, 50%)")  // rgb(64, 191, 64)
d3.color("rgba(0, 0, 0, 0.5)")  // rgba(0, 0, 0, 0.5)
d3.color("invalid")              // null
```

### Color methods

```javascript
const c = d3.color("steelblue");

c.brighter(1)      // lighter version (k=1 default)
c.darker(1)        // darker version
c.opacity           // 1
c.copy({ opacity: 0.5 })  // copy with overrides

c.displayable()     // true if in gamut
c.formatHex()       // "#4682b4"
c.formatHex8()      // "#4682b4ff"
c.formatRgb()       // "rgb(70, 130, 180)"
c.formatHsl()       // "hsl(207.3, 44.2%, 49%)"
c.toString()        // "rgb(70, 130, 180)"
c.rgb()             // convert to RGB
```

### Manipulating colors

```javascript
let c = d3.hsl("steelblue");
c.h += 90;          // rotate hue
c.s += 0.2;         // increase saturation
c.l = 0.6;          // set lightness
c.opacity = 0.8;
c.toString()         // CSS color string
```

## Color Spaces

### d3.rgb(r, g, b, opacity)

```javascript
d3.rgb(255, 0, 0)              // red
d3.rgb("steelblue")            // parse and convert
d3.rgb(300, 200, 100).clamp()  // clamp to valid range
```

### d3.hsl(h, s, l, opacity)

Hue (0-360°), Saturation (0-1), Lightness (0-1):

```javascript
d3.hsl(0, 1, 0.5)     // red
d3.hsl(120, 1, 0.5)   // green
d3.hsl(240, 1, 0.5)   // blue
d3.hsl("steelblue")   // convert

d3.hsl(0, 1, 0.5).clamp()  // clamp h to [0,360), s,l to [0,1]
```

### d3.lab(l, a, b, opacity)

CIELAB — perceptually uniform color space:

```javascript
d3.lab(50, 0, 0)       // neutral gray at L=50
d3.lab("steelblue")    // convert
d3.lab(60, -30, 40)    // custom L*a*b* values
```

### d3.hcl(h, c, l, opacity)

Cylindrical form of CIELAB (Hue, Chroma, Luminance):

```javascript
d3.hcl(0, 50, 50)     // red at chroma=50, luminance=50
d3.hcl("steelblue")   // convert
```

### d3.cubehelix(h, s, l, opacity)

Cubehelix — monotonically increasing luminance, good for sequential scales:

```javascript
d3.cubehelix(300, 0.5, 0.5)
```

### When to use each color space

| Space | Use Case |
|:------|:---------|
| RGB | Default, CSS compatibility |
| HSL | Intuitive hue rotation and saturation |
| Lab/HCL | Perceptually uniform gradients |
| Cubehelix | Sequential scales with monotonic luminance |

## Interpolation

### d3.interpolate(a, b)

Auto-detects value types and returns an interpolator function:

```javascript
const i = d3.interpolate("red", "blue");
i(0)   // "rgb(255, 0, 0)"
i(0.5) // "rgb(128, 0, 128)"
i(1)   // "rgb(0, 0, 255)"
```

### Number interpolation

```javascript
const i = d3.interpolateNumber(0, 100);
i(0.5) // 50

d3.interpolateRound(0, 100)(0.5) // 50 (rounded)
```

### Color interpolation

```javascript
// RGB (default for colors)
d3.interpolateRgb("red", "blue")(0.5)

// HSL (shorter hue arc)
d3.interpolateHsl("red", "blue")(0.5)

// HSL (longer hue arc — goes through more hues)
d3.interpolateHslLong("red", "blue")(0.5)

// Lab (perceptually uniform — recommended)
d3.interpolateLab("red", "blue")(0.5)

// HCL (perceptually uniform, cylindrical)
d3.interpolateHcl("red", "blue")(0.5)
d3.interpolateHclLong("red", "blue")(0.5)

// Cubehelix
d3.interpolateCubehelix("red", "blue")(0.5)
d3.interpolateCubehelixLong("red", "blue")(0.5)

// With gamma correction
d3.interpolateRgb.gamma(2.2)("red", "blue")(0.5)
d3.interpolateCubehelix.gamma(3)("red", "blue")(0.5)
```

### String interpolation

Interpolates numbers and colors embedded in strings:

```javascript
d3.interpolateString("10px", "20px")(0.5)  // "15px"
d3.interpolateString("translate(0,0)", "translate(100,50)")(0.5)
// "translate(50,25)"
```

### Array and object interpolation

```javascript
d3.interpolateArray([0, 0], [100, 200])(0.5)  // [50, 100]

d3.interpolateObject({ x: 0, y: 0 }, { x: 100, y: 200 })(0.5)
// { x: 50, y: 100 }
```

### Date interpolation

```javascript
d3.interpolateDate(new Date("2024-01-01"), new Date("2024-12-31"))(0.5)
// ~July 1, 2024
```

### Transform interpolation

```javascript
d3.interpolateTransformSvg(
  "translate(0,0) scale(1)",
  "translate(100,50) scale(2)"
)(0.5)
// "translate(50, 25) scale(1.5)"
```

### d3.piecewise(interpolate, values)

Multi-stop interpolation:

```javascript
const color = d3.piecewise(d3.interpolateHsl, ["red", "yellow", "green"]);
color(0)   // red
color(0.5) // yellow
color(1)   // green
```

### d3.quantize(interpolator, n)

Sample evenly-spaced values:

```javascript
d3.quantize(d3.interpolateRgb("red", "blue"), 5)
// ["rgb(255,0,0)", "rgb(191,0,64)", "rgb(128,0,128)", "rgb(64,0,191)", "rgb(0,0,255)"]
```

## Color Schemes — Categorical

Discrete color palettes for nominal data:

```javascript
d3.schemeCategory10     // 10 colors (classic D3)
d3.schemeObservable10   // 10 colors (Observable style)
d3.schemeTableau10      // 10 colors (Tableau)
d3.schemeAccent         // 8 colors
d3.schemeDark2          // 8 colors
d3.schemePaired         // 12 colors
d3.schemePastel1        // 9 colors
d3.schemePastel2        // 8 colors
d3.schemeSet1            // 9 colors
d3.schemeSet2            // 8 colors
d3.schemeSet3            // 12 colors
```

Usage with ordinal scale:

```javascript
const color = d3.scaleOrdinal(d3.schemeCategory10);
color("A") // first color
color("B") // second color
```

## Color Schemes — Sequential

Continuous gradients for ordered quantitative data:

### Single-hue

```javascript
d3.interpolateBlues      // light→dark blue
d3.interpolateGreens     // light→dark green
d3.interpolateGreys      // light→dark grey
d3.interpolateOranges    // light→dark orange
d3.interpolatePurples    // light→dark purple
d3.interpolateReds       // light→dark red
```

### Multi-hue

```javascript
d3.interpolateViridis    // purple→green→yellow (colorblind-safe)
d3.interpolatePlasma     // purple→orange→yellow
d3.interpolateInferno    // black→purple→yellow
d3.interpolateMagma      // black→purple→yellow
d3.interpolateCividis    // blue→yellow (colorblind-safe)
d3.interpolateTurbo      // rainbow-like
d3.interpolateWarm       // warm colors
d3.interpolateCool       // cool colors

// ColorBrewer multi-hue
d3.interpolateBuGn       // blue→green
d3.interpolateBuPu       // blue→purple
d3.interpolateGnBu       // green→blue
d3.interpolateOrRd       // orange→red
d3.interpolatePuBu       // purple→blue
d3.interpolatePuBuGn     // purple→blue→green
d3.interpolatePuRd       // purple→red
d3.interpolateRdPu       // red→purple
d3.interpolateYlGn       // yellow→green
d3.interpolateYlGnBu     // yellow→green→blue
d3.interpolateYlOrBr     // yellow→orange→brown
d3.interpolateYlOrRd     // yellow→orange→red
```

### Discrete versions (arrays of N colors)

```javascript
d3.schemeBlues[9]    // array of 9 blue shades
d3.schemeGreens[5]   // array of 5 green shades
// Available for all sequential schemes, N from 3 to 9
```

Usage:

```javascript
const color = d3.scaleSequential([0, 100], d3.interpolateViridis);
color(50)  // mid-viridis color

// Or with quantize for discrete steps
const color = d3.scaleQuantize([0, 100], d3.schemeBlues[5]);
```

## Color Schemes — Diverging

Two-color gradients with a neutral midpoint:

```javascript
d3.interpolateBrBG       // brown→white→blue-green
d3.interpolatePRGn       // purple→white→green
d3.interpolatePiYG       // pink→white→yellow-green
d3.interpolatePuOr       // purple→white→orange
d3.interpolateRdBu       // red→white→blue
d3.interpolateRdGy       // red→white→grey
d3.interpolateRdYlBu     // red→yellow→blue
d3.interpolateRdYlGn     // red→yellow→green
d3.interpolateSpectral   // red→yellow→blue (spectral)
```

Usage:

```javascript
const color = d3.scaleDiverging([-1, 0, 1], d3.interpolateRdBu);
color(-1)  // red
color(0)   // white
color(1)   // blue
```

### Cyclical schemes

```javascript
d3.interpolateRainbow    // full hue cycle
d3.interpolateSinebow    // sinusoidal rainbow
```

## Choosing Color Schemes

| Data Type | Scheme Type | Recommended |
|:----------|:-----------|:------------|
| Categories (≤10) | Categorical | `schemeCategory10`, `schemeTableau10` |
| Categories (≤12) | Categorical | `schemePaired`, `schemeSet3` |
| Ordered numbers | Sequential | `interpolateViridis` (colorblind-safe) |
| Hot/cold values | Sequential | `interpolateBlues`, `interpolateReds` |
| Positive/negative | Diverging | `interpolateRdBu`, `interpolateRdYlGn` |
| Percentages | Sequential | `interpolateYlGnBu` |
| Geographic maps | Sequential | `interpolateBlues`, `schemeBlues[9]` |

**Colorblind-safe options:** `interpolateViridis`, `interpolateCividis`, `interpolatePlasma`, `schemeDark2`, `schemeCategory10`
