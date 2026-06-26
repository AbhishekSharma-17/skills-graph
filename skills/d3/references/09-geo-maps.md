# D3 Geographic Maps

> Source: [d3-geo](https://d3js.org/d3-geo) | Module: `d3-geo`

## Table of Contents

- [Overview](#overview)
- [Projections](#projections)
- [Common Projections](#common-projections)
- [Projection Methods](#projection-methods)
- [GeoPath Generator](#geopath-generator)
- [Graticule and Shapes](#graticule-and-shapes)
- [Spherical Math](#spherical-math)
- [Working with GeoJSON and TopoJSON](#working-with-geojson-and-topojson)
- [Complete Map Example](#complete-map-example)

## Overview

D3-geo provides tools for rendering geographic data using map projections. It transforms spherical coordinates (longitude, latitude) to planar coordinates (x, y) with adaptive sampling that accurately renders geodesic arcs.

Key concepts:
- **Projections** — transform lat/lon to screen coordinates
- **GeoPath** — generates SVG path strings from GeoJSON features
- **Graticule** — coordinate grid (meridians and parallels)
- **Spherical math** — area, centroid, distance on a sphere

## Projections

A projection is a function that maps [longitude, latitude] → [x, y]:

```javascript
const projection = d3.geoMercator()
  .center([0, 0])
  .scale(100)
  .translate([width / 2, height / 2]);

projection([0, 0])        // [width/2, height/2] — the center
projection([-122.4, 37.8]) // San Francisco in pixels
projection.invert([400, 300]) // pixel → [lon, lat]
```

## Common Projections

### d3.geoMercator()

Conformal cylindrical — preserves angles, distorts area near poles. Web mapping standard (Google Maps, Mapbox).

```javascript
const projection = d3.geoMercator()
  .fitSize([width, height], geojson);
```

### d3.geoAlbers()

Equal-area conic — preserves area. Default centered on the US.

```javascript
const projection = d3.geoAlbers()
  .center([0, 38])
  .rotate([96, 0])
  .parallels([29.5, 45.5])
  .fitSize([width, height], geojson);
```

### d3.geoAlbersUsa()

Composite projection with Alaska and Hawaii repositioned:

```javascript
const projection = d3.geoAlbersUsa()
  .fitSize([width, height], usGeoJson);
```

### d3.geoEquirectangular()

Simple plate carrée — lon → x, lat → y. Good for data overlays.

```javascript
const projection = d3.geoEquirectangular()
  .fitSize([width, height], geojson);
```

### d3.geoOrthographic()

Globe view from space:

```javascript
const projection = d3.geoOrthographic()
  .rotate([-longitude, -latitude])  // center on point
  .clipAngle(90)                    // clip back hemisphere
  .fitSize([width, height], { type: "Sphere" });
```

### d3.geoNaturalEarth1()

Pseudocylindrical — visually pleasing for world maps:

```javascript
const projection = d3.geoNaturalEarth1()
  .fitSize([width, height], { type: "Sphere" });
```

### d3.geoConicEqualArea() / d3.geoConicConformal()

```javascript
d3.geoConicEqualArea().parallels([30, 60])
d3.geoConicConformal().parallels([30, 60])
```

### d3.geoStereographic() / d3.geoGnomonic() / d3.geoTransverseMercator()

Azimuthal projections for special use cases.

### Extended projections

The `d3-geo-projection` package adds 30+ additional projections:

```bash
npm install d3-geo-projection
```

```javascript
import { geoRobinson, geoMollweide, geoWinkel3 } from "d3-geo-projection";
```

## Projection Methods

### Centering and positioning

```javascript
projection
  .center([longitude, latitude])    // projection center
  .rotate([lambda, phi, gamma])     // three-axis rotation
  .translate([tx, ty])              // pixel offset
  .scale(k)                        // zoom level
```

### Clipping

```javascript
projection
  .clipAngle(90)                    // clip to cone (for globe)
  .clipExtent([[0, 0], [width, height]]) // clip to viewport
```

### Fit to data

```javascript
// Fit projection so GeoJSON fills the given dimensions
projection.fitSize([width, height], geojson)

// Fit with specific margins
projection.fitExtent(
  [[marginLeft, marginTop], [width - marginRight, height - marginBottom]],
  geojson
)

// Fit to a specific width (height auto)
projection.fitWidth(width, geojson)
projection.fitHeight(height, geojson)
```

### Inversion

```javascript
projection([lon, lat])        // [lon, lat] → [x, y]
projection.invert([x, y])     // [x, y] → [lon, lat]
```

## GeoPath Generator

### d3.geoPath(projection)

Creates a path generator that renders GeoJSON as SVG paths:

```javascript
const path = d3.geoPath(projection);

// Render features
svg.selectAll("path")
  .data(geojson.features)
  .join("path")
    .attr("d", path)
    .attr("fill", "#ccc")
    .attr("stroke", "#333");
```

### Path measurements

```javascript
path.area(feature)       // projected area in square pixels
path.bounds(feature)     // [[x0, y0], [x1, y1]] bounding box
path.centroid(feature)   // [x, y] centroid
path.measure(feature)    // path length in pixels
```

### Canvas rendering

```javascript
const context = canvas.getContext("2d");
const path = d3.geoPath(projection, context);

context.beginPath();
path(geojson);
context.fillStyle = "#ccc";
context.fill();
context.strokeStyle = "#333";
context.stroke();
```

### Null projection (pre-projected data)

```javascript
const path = d3.geoPath(); // no projection — identity transform
```

## Graticule and Shapes

### d3.geoGraticule()

Generates a coordinate grid:

```javascript
const graticule = d3.geoGraticule()
  .step([10, 10]);    // grid spacing in degrees

svg.append("path")
  .datum(graticule())
  .attr("d", path)
  .attr("fill", "none")
  .attr("stroke", "#ddd")
  .attr("stroke-width", 0.5);
```

### d3.geoGraticule10()

Quick shorthand for 10-degree graticule:

```javascript
svg.append("path")
  .datum(d3.geoGraticule10())
  .attr("d", path)
  .attr("fill", "none")
  .attr("stroke", "#eee");
```

### Outline (sphere)

```javascript
svg.append("path")
  .datum({ type: "Sphere" })
  .attr("d", path)
  .attr("fill", "#f0f8ff")
  .attr("stroke", "#333");
```

### d3.geoCircle()

Generate a circle on the sphere:

```javascript
const circle = d3.geoCircle()
  .center([-122.4, 37.8])  // San Francisco
  .radius(5);               // 5 degrees

svg.append("path")
  .datum(circle())
  .attr("d", path)
  .attr("fill", "rgba(255,0,0,0.2)");
```

## Spherical Math

```javascript
d3.geoArea(feature)        // area in steradians
d3.geoBounds(feature)      // [[lon0, lat0], [lon1, lat1]]
d3.geoCentroid(feature)    // [lon, lat] centroid
d3.geoDistance(a, b)       // great-circle distance in radians
d3.geoLength(feature)      // total length in radians
d3.geoContains(feature, point) // point-in-polygon test
d3.geoInterpolate(a, b)   // great-circle interpolator
```

### Distance calculation

```javascript
const sf = [-122.4, 37.8];
const ny = [-74.0, 40.7];

const radians = d3.geoDistance(sf, ny);
const km = radians * 6371; // Earth radius in km
// ~4130 km
```

## Working with GeoJSON and TopoJSON

### GeoJSON

Standard format for geographic features:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "California", "population": 39538223 },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[...], ...]]
      }
    }
  ]
}
```

### TopoJSON

Compact topology-aware format. Convert to GeoJSON for rendering:

```bash
npm install topojson-client
```

```javascript
import * as topojson from "topojson-client";

const us = await d3.json("us-10m.json");

// Extract features
const states = topojson.feature(us, us.objects.states);
// GeoJSON FeatureCollection

// Extract mesh (shared borders)
const stateBorders = topojson.mesh(us, us.objects.states, (a, b) => a !== b);

svg.selectAll("path")
  .data(states.features)
  .join("path")
    .attr("d", path)
    .attr("fill", d => color(d.properties.population));

svg.append("path")
  .datum(stateBorders)
  .attr("d", path)
  .attr("fill", "none")
  .attr("stroke", "#fff");
```

## Complete Map Example

### US Choropleth

```javascript
const us = await d3.json("us-10m.json");
const data = await d3.csv("population.csv", d3.autoType);

const population = new Map(data.map(d => [d.fips, d.population]));

const projection = d3.geoAlbersUsa().fitSize([width, height],
  topojson.feature(us, us.objects.states));
const path = d3.geoPath(projection);

const color = d3.scaleQuantize()
  .domain(d3.extent(data, d => d.population))
  .range(d3.schemeBlues[9]);

svg.selectAll("path")
  .data(topojson.feature(us, us.objects.states).features)
  .join("path")
    .attr("d", path)
    .attr("fill", d => color(population.get(d.id)))
    .attr("stroke", "#fff")
    .attr("stroke-width", 0.5);

// State borders
svg.append("path")
  .datum(topojson.mesh(us, us.objects.states, (a, b) => a !== b))
  .attr("d", path)
  .attr("fill", "none")
  .attr("stroke", "#fff")
  .attr("stroke-width", 1);
```

### World map with rotation

```javascript
const world = await d3.json("world-110m.json");
const land = topojson.feature(world, world.objects.land);

const projection = d3.geoOrthographic()
  .rotate([-30, -30])
  .fitSize([width, height], { type: "Sphere" });

const path = d3.geoPath(projection);

// Ocean
svg.append("path")
  .datum({ type: "Sphere" })
  .attr("d", path)
  .attr("fill", "#e8f4f8");

// Graticule
svg.append("path")
  .datum(d3.geoGraticule10())
  .attr("d", path)
  .attr("fill", "none")
  .attr("stroke", "#ddd");

// Land
svg.append("path")
  .datum(land)
  .attr("d", path)
  .attr("fill", "#a8d5a2");
```
