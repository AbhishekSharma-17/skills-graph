# D3 Data Utilities

> Source: [d3-array](https://d3js.org/d3-array) | [d3-fetch](https://d3js.org/d3-fetch) | [d3-format](https://d3js.org/d3-format) | [d3-time](https://d3js.org/d3-time)

## Table of Contents

- [Overview](#overview)
- [Statistics](#statistics)
- [Searching and Sorting](#searching-and-sorting)
- [Grouping and Aggregation](#grouping-and-aggregation)
- [Bins and Histograms](#bins-and-histograms)
- [Transformations](#transformations)
- [Data Loading](#data-loading)
- [Number Formatting](#number-formatting)
- [Time Utilities](#time-utilities)

## Overview

D3 provides a comprehensive suite of data manipulation utilities across several modules. These functions are useful standalone — they have no dependency on DOM rendering and work well with any data pipeline.

## Statistics

### Basic statistics

```javascript
const data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5];

d3.min(data)               // 1
d3.max(data)               // 9
d3.extent(data)            // [1, 9]
d3.sum(data)               // 44
d3.mean(data)              // 4
d3.median(data)            // 4
d3.mode(data)              // 5 (most frequent)
d3.variance(data)          // 5.4...
d3.deviation(data)         // 2.32... (standard deviation)
```

### With accessor functions

```javascript
const people = [
  { name: "Alice", age: 30 },
  { name: "Bob", age: 25 },
  { name: "Carol", age: 35 }
];

d3.min(people, d => d.age)        // 25
d3.max(people, d => d.age)        // 35
d3.extent(people, d => d.age)     // [25, 35]
d3.mean(people, d => d.age)       // 30
```

### Quantiles

```javascript
d3.quantile(sorted, 0.25)   // first quartile (Q1)
d3.quantile(sorted, 0.5)    // median (Q2)
d3.quantile(sorted, 0.75)   // third quartile (Q3)
d3.quantile(sorted, 0.95)   // 95th percentile
```

### Index-returning variants

```javascript
d3.minIndex(data)            // index of minimum
d3.maxIndex(data)            // index of maximum
d3.leastIndex(data, (a, b) => a.value - b.value) // index of least
d3.greatestIndex(data, (a, b) => a.value - b.value) // index of greatest
```

### least / greatest

```javascript
d3.least(people, d => d.age)      // { name: "Bob", age: 25 }
d3.greatest(people, d => d.age)   // { name: "Carol", age: 35 }

// With comparator
d3.least(people, (a, b) => a.age - b.age)
```

### Cumulative sum

```javascript
d3.cumsum([1, 2, 3, 4])  // Float64Array [1, 3, 6, 10]
```

## Searching and Sorting

### d3.bisect / d3.bisectLeft / d3.bisectRight

Binary search in a sorted array — find insertion index:

```javascript
const sorted = [10, 20, 30, 40, 50];

d3.bisect(sorted, 25)       // 2 (insert after 20)
d3.bisectLeft(sorted, 30)   // 2 (insert before 30)
d3.bisectRight(sorted, 30)  // 3 (insert after 30)
```

### d3.bisector(accessor)

Custom bisector for objects:

```javascript
const bisect = d3.bisector(d => d.date).left;

// Find insertion point for a date in sorted data
const i = bisect(data, new Date("2024-06-15"));
const closest = data[i];
```

### Sorting

```javascript
d3.ascending(a, b)    // comparator: a < b → -1, a > b → 1
d3.descending(a, b)   // comparator: a > b → -1, a < b → 1

data.sort(d3.ascending);
data.sort((a, b) => d3.ascending(a.value, b.value));

d3.sort(data, d => d.value)           // ascending by accessor
d3.sort(data, d => -d.value)          // descending by negation
d3.sort(data, (a, b) => a.age - b.age) // custom comparator
```

### d3.rank(iterable, comparator)

```javascript
d3.rank([40, 10, 30, 20])  // Float64Array [3, 0, 2, 1]
```

## Grouping and Aggregation

### d3.group(iterable, ...keys)

Groups into a Map (like SQL GROUP BY):

```javascript
const sales = [
  { product: "A", region: "East", value: 100 },
  { product: "A", region: "West", value: 150 },
  { product: "B", region: "East", value: 200 },
  { product: "B", region: "West", value: 120 }
];

// Group by one key
const byProduct = d3.group(sales, d => d.product);
// Map { "A" => [{...}, {...}], "B" => [{...}, {...}] }

// Group by multiple keys (nested)
const nested = d3.group(sales, d => d.product, d => d.region);
// Map { "A" => Map { "East" => [...], "West" => [...] }, ... }
```

### d3.rollup(iterable, reduce, ...keys)

Group and aggregate in one step:

```javascript
const totals = d3.rollup(sales, v => d3.sum(v, d => d.value), d => d.product);
// Map { "A" => 250, "B" => 320 }

// Nested rollup
const nested = d3.rollup(
  sales,
  v => d3.sum(v, d => d.value),
  d => d.region,
  d => d.product
);
// Map { "East" => Map { "A" => 100, "B" => 200 }, ... }
```

### d3.index(iterable, ...keys)

Like group but expects unique keys (one value per key):

```javascript
const lookup = d3.index(people, d => d.id);
lookup.get("abc"); // single person object
```

### d3.groups / d3.rollups / d3.flatGroup / d3.flatRollup

Array-returning variants (instead of Map):

```javascript
d3.groups(sales, d => d.product)
// [["A", [{...}, {...}]], ["B", [{...}, {...}]]]

d3.flatRollup(sales, v => d3.sum(v, d => d.value), d => d.region, d => d.product)
// [["East", "A", 100], ["East", "B", 200], ...]
```

## Bins and Histograms

### d3.bin()

Divides data into bins (for histograms):

```javascript
const data = [1, 3, 5, 7, 9, 12, 15, 18, 22, 25, 28, 30, 35, 40];

const bin = d3.bin()
  .domain([0, 50])     // range of data
  .thresholds(10);      // target number of bins

const bins = bin(data);
// Each bin: array of values with .x0 (start) and .x1 (end) properties

// Use in histogram
svg.selectAll("rect")
  .data(bins)
  .join("rect")
    .attr("x", d => x(d.x0) + 1)
    .attr("y", d => y(d.length))
    .attr("width", d => x(d.x1) - x(d.x0) - 1)
    .attr("height", d => y(0) - y(d.length));
```

### With accessor

```javascript
const bin = d3.bin()
  .value(d => d.age)
  .domain([0, 100])
  .thresholds([18, 30, 45, 60, 75]);  // explicit breakpoints
```

### Threshold generators

```javascript
d3.thresholdFreedmanDiaconis(values, min, max) // optimal bin width
d3.thresholdScott(values, min, max)            // Scott's rule
d3.thresholdSturges(values)                     // Sturges' formula
```

## Transformations

### d3.range(start, stop, step)

Generate evenly spaced numbers:

```javascript
d3.range(5)           // [0, 1, 2, 3, 4]
d3.range(1, 5)        // [1, 2, 3, 4]
d3.range(0, 1, 0.2)   // [0, 0.2, 0.4, 0.6, 0.8]
```

### d3.cross(a, b, reducer)

Cartesian product:

```javascript
d3.cross([1, 2], ["a", "b"])
// [[1,"a"], [1,"b"], [2,"a"], [2,"b"]]

d3.cross([1, 2], [3, 4], (a, b) => a + b)
// [4, 5, 5, 6]
```

### d3.pairs(array, reducer)

Adjacent element pairs:

```javascript
d3.pairs([1, 2, 3, 4])
// [[1,2], [2,3], [3,4]]

// Compute differences
d3.pairs(data, (a, b) => b.value - a.value)
```

### d3.merge(arrays)

Flatten one level:

```javascript
d3.merge([[1, 2], [3, 4], [5, 6]])  // [1, 2, 3, 4, 5, 6]
```

### d3.shuffle(array)

Fisher-Yates shuffle (in place):

```javascript
d3.shuffle([1, 2, 3, 4, 5])  // randomized order
```

### d3.ticks(start, stop, count)

Generate evenly spaced "nice" values:

```javascript
d3.ticks(0, 100, 5)   // [0, 20, 40, 60, 80, 100]
d3.ticks(0, 1, 4)      // [0, 0.2, 0.4, 0.6, 0.8, 1]
```

## Data Loading

### d3.csv(url, row)

```javascript
// Auto-typed
const data = await d3.csv("/data/sales.csv", d3.autoType);

// Custom row accessor
const data = await d3.csv("/data/sales.csv", d => ({
  date: new Date(d.date),
  value: +d.value,
  category: d.category
}));
```

### d3.json(url)

```javascript
const data = await d3.json("/api/data");
```

### d3.tsv(url, row)

```javascript
const data = await d3.tsv("/data/matrix.tsv", d3.autoType);
```

### d3.text(url) / d3.xml(url) / d3.html(url) / d3.svg(url)

```javascript
const text = await d3.text("/data/readme.txt");
const doc = await d3.xml("/data/config.xml");
```

### d3.dsv(delimiter, url, row)

Custom delimiter:

```javascript
const data = await d3.dsv(";", "/data/european.csv", d3.autoType);
```

## Number Formatting

### d3.format(specifier)

```javascript
const f = d3.format(",.2f");
f(1234567.89)  // "1,234,567.89"

d3.format(".0%")(0.123)      // "12%"
d3.format("$,.2f")(1234.5)   // "$1,234.50"
d3.format(".2s")(1500)        // "1.5k"
d3.format("+.1f")(3.14)       // "+3.1"
d3.format(",.0f")(1e6)        // "1,000,000"
d3.format(".3~s")(1234)       // "1.23k" (trimmed)
```

### d3.formatPrefix(specifier, value)

Format with fixed SI prefix:

```javascript
const f = d3.formatPrefix(",.0", 1e6);
f(1234567)   // "1M"
```

## Time Utilities

### Time intervals

```javascript
d3.timeDay         // calendar day
d3.timeWeek        // Sunday-based week
d3.timeMonth       // calendar month
d3.timeYear        // calendar year
d3.timeHour        // clock hour
d3.timeMinute      // clock minute

// UTC variants (recommended for data)
d3.utcDay, d3.utcWeek, d3.utcMonth, d3.utcYear
```

### Interval methods

```javascript
d3.timeDay.floor(new Date())   // start of today
d3.timeDay.ceil(new Date())    // start of tomorrow
d3.timeDay.round(new Date())   // nearest day boundary

d3.timeMonth.range(new Date("2024-01-01"), new Date("2024-06-01"))
// [Jan 1, Feb 1, Mar 1, Apr 1, May 1]

d3.timeDay.count(start, end)   // days between dates
d3.timeDay.every(7)             // every 7 days
```

### d3.timeFormat / d3.timeParse

```javascript
const format = d3.timeFormat("%B %d, %Y");
format(new Date()) // "June 27, 2026"

const parse = d3.timeParse("%Y-%m-%d");
parse("2024-06-15") // Date object

// UTC variants
d3.utcFormat("%Y-%m-%dT%H:%M:%SZ")
d3.utcParse("%Y-%m-%dT%H:%M:%SZ")
```
