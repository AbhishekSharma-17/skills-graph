# Code Node

> Source: https://docs.n8n.io/build/code-in-n8n/using-the-code-node/

## Table of Contents

- [Overview](#overview)
- [Execution Modes](#execution-modes)
- [JavaScript Mode](#javascript-mode)
- [Python Mode](#python-mode)
- [Built-in Variables](#built-in-variables)
- [Accessing Data from Other Nodes](#accessing-data-from-other-nodes)
- [Return Format](#return-format)
- [Available Modules](#available-modules)
- [Cookbook Recipes](#cookbook-recipes)
- [Common Pitfalls](#common-pitfalls)

## Overview

The Code node lets you write custom JavaScript or Python to transform data, implement complex logic, or perform operations that built-in nodes don't cover.

### When to Use the Code Node

- Complex data transformations beyond what the Edit Fields node can do
- Custom business logic (scoring, filtering, aggregation)
- String manipulation and formatting
- Date calculations beyond Luxon basics
- Working with deeply nested JSON structures
- Generating structured output from unstructured data

## Execution Modes

### Run Once for All Items (Default)

Code executes once, receiving all input items. Returns all output items at once.

```javascript
// JavaScript — Run Once for All Items
const items = $input.all();
const results = [];

for (const item of items) {
  results.push({
    json: {
      name: item.json.name.toUpperCase(),
      processed: true
    }
  });
}

return results;
```

### Run Once for Each Item

Code executes once per input item. Each execution handles a single item.

```javascript
// JavaScript — Run Once for Each Item
return {
  json: {
    name: $input.item.json.name.toUpperCase(),
    processed: true
  }
};
```

### Choosing the Right Mode

| Scenario | Mode |
|----------|------|
| Filter based on cross-item comparison | Run Once for All Items |
| Transform each item independently | Run Once for Each Item |
| Aggregate/summarize multiple items | Run Once for All Items |
| Simple field mapping per item | Run Once for Each Item |
| Sort or deduplicate | Run Once for All Items |

## JavaScript Mode

### Accessing Current Item Data

```javascript
// Run Once for Each Item mode
const name = $input.item.json.name;
const email = $input.item.json.email;
const tags = $input.item.json.tags || [];

return {
  json: {
    fullName: name,
    domain: email.split('@')[1],
    tagCount: tags.length
  }
};
```

### Processing All Items

```javascript
// Run Once for All Items mode
const allItems = $input.all();

// Filter
const active = allItems.filter(item => item.json.status === 'active');

// Map
const names = allItems.map(item => ({
  json: { name: item.json.name }
}));

// Reduce
const total = allItems.reduce((sum, item) => sum + item.json.amount, 0);

return [{ json: { total, activeCount: active.length } }];
```

### Async Operations

```javascript
// Promises are supported
const response = await fetch('https://api.example.com/data');
// Note: Direct HTTP requests are blocked in n8n Cloud
// Use the HTTP Request node instead
```

### Console Logging

```javascript
console.log('Debug value:', $json.someField);
// Output appears in the browser developer console (F12)
// Useful for debugging, not visible in execution history
```

## Python Mode

### Native Python (v1.111.0+)

```python
# Run Once for All Items mode
results = []
for item in _items:
    results.append({
        "json": {
            "name": item["json"]["name"].upper(),
            "processed": True
        }
    })
return results
```

### Per-Item Mode

```python
# Run Once for Each Item mode
name = _item["json"]["name"]
return {
    "json": {
        "upper_name": name.upper(),
        "length": len(name)
    }
}
```

### Python Syntax Differences

| JavaScript | Python |
|-----------|--------|
| `$input.all()` | `_items` |
| `$input.item` | `_item` |
| `$json.field` | `_item["json"]["field"]` |
| `$('Node').all()` | Not available in native Python |
| `console.log()` | `print()` |

### Python Limitations

- Native Python uses bracket notation only (`item["json"]["field"]`)
- External library imports blocked on n8n Cloud
- Self-hosted instances can enable external packages
- Insecure built-ins are denied by default
- Access to other nodes' data is limited compared to JavaScript

## Built-in Variables

### In JavaScript

```javascript
// Current item data
$json                          // Current item's JSON (shorthand for $input.item.json)
$binary                        // Current item's binary data
$input.item                    // Full current item object
$input.all()                   // All input items
$input.first()                 // First input item
$input.last()                  // Last input item

// Other nodes
$('Node Name').all()           // All items from a named node
$('Node Name').first()         // First item from a named node
$('Node Name').item            // Paired item from a named node

// Workflow context
$workflow.id                   // Workflow ID
$workflow.name                 // Workflow name
$execution.id                  // Execution ID
$execution.mode                // "manual" or "trigger"
$execution.customData          // Custom metadata

// Date/time
$now                           // Current Luxon DateTime
$today                         // Today at midnight (Luxon DateTime)

// Environment
$vars.myVariable               // Instance variable
$env.MY_ENV_VAR                // Environment variable (if allowed)
$runIndex                      // Current run index (loops)
$itemIndex                     // Current item index

// Workflow static data (persists between executions)
const staticData = $getWorkflowStaticData('global');
staticData.lastRunDate = $now.toISO();
```

### Workflow Static Data

Store persistent state between executions:

```javascript
// Read/write static data (persists across executions)
const staticData = $getWorkflowStaticData('global');

// First execution
if (!staticData.cursor) {
  staticData.cursor = 0;
}

// Use and update
const offset = staticData.cursor;
staticData.cursor = offset + 100;

return [{ json: { offset } }];
```

## Accessing Data from Other Nodes

```javascript
// Get all items from a specific node
const users = $('Fetch Users').all();

// Get first item
const config = $('Load Config').first().json;

// Get paired item (the item that corresponds to current item)
const original = $('Original Data').item.json;

// Check if a node executed
if ($('Optional Step').isExecuted) {
  // Use its data
}
```

## Return Format

### JavaScript — All Items Mode

Must return an array of items:

```javascript
return [
  { json: { id: 1, name: 'Alice' } },
  { json: { id: 2, name: 'Bob' } }
];
```

### JavaScript — Each Item Mode

Must return a single item:

```javascript
return { json: { processed: true, value: 42 } };
```

### Including Binary Data

```javascript
return [
  {
    json: { filename: 'output.txt' },
    binary: {
      data: await this.helpers.prepareBinaryData(
        Buffer.from('Hello World'),
        'output.txt',
        'text/plain'
      )
    }
  }
];
```

### Preserving Item Linking

```javascript
return $input.all().map((item, index) => ({
  json: { ...item.json, extra: 'field' },
  pairedItem: { item: index }
}));
```

## Available Modules

### Always Available

- `crypto` — Node.js crypto module
- `moment` — Date library (legacy; prefer Luxon via `$now`)
- Luxon — via `DateTime` (available in expressions)

### Self-Hosted Only

Enable external modules via environment variable:

```bash
NODE_FUNCTION_ALLOW_EXTERNAL=lodash,axios,cheerio
```

Then in the Code node:

```javascript
const _ = require('lodash');
const grouped = _.groupBy($input.all().map(i => i.json), 'category');
```

### n8n Cloud Restrictions

Cloud instances have limited module access. Use dedicated nodes (HTTP Request, etc.) instead of importing libraries.

## Cookbook Recipes

### Deduplicate Items

```javascript
const seen = new Set();
return $input.all().filter(item => {
  const key = item.json.email;
  if (seen.has(key)) return false;
  seen.add(key);
  return true;
});
```

### Flatten Nested Arrays

```javascript
return $input.all().flatMap(item =>
  item.json.orders.map(order => ({
    json: { customerId: item.json.id, ...order }
  }))
);
```

### Group and Aggregate

```javascript
const groups = {};
for (const item of $input.all()) {
  const key = item.json.category;
  if (!groups[key]) groups[key] = { count: 0, total: 0 };
  groups[key].count++;
  groups[key].total += item.json.amount;
}

return Object.entries(groups).map(([category, stats]) => ({
  json: { category, ...stats, average: stats.total / stats.count }
}));
```

### Generate Date Range

```javascript
const days = [];
let current = $today.minus({ days: 30 });
while (current <= $today) {
  days.push({ json: { date: current.toISODate() } });
  current = current.plus({ days: 1 });
}
return days;
```

## Common Pitfalls

- **Forgetting the json wrapper** — the Code node auto-wraps since v0.166, but explicit is safer
- **Returning nothing** — an empty return produces no output items; downstream nodes won't execute
- **Mutating input data** — modifying `$input.all()` items in-place can cause unexpected behavior; create new objects
- **File system access** — the Code node cannot read/write files; use Read/Write File nodes
- **HTTP requests** — direct HTTP calls are blocked on Cloud; use the HTTP Request node
- **Python node data access** — `$('Node Name')` syntax is not available in native Python
- **Static data limits** — workflow static data is stored in the database; don't store large payloads

## Related Topics

- Data Structure → `03-data-structure-and-expressions.md`
- Flow Logic → `04-flow-logic.md`
- HTTP Request → `06-http-request-and-apis.md`
