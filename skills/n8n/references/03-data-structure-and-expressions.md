# Data Structure and Expressions

> Source: https://docs.n8n.io/build/work-with-data/

## Table of Contents

- [Data Structure](#data-structure)
- [Items and JSON](#items-and-json)
- [Binary Data](#binary-data)
- [Expression Syntax](#expression-syntax)
- [Built-in Variables](#built-in-variables)
- [Data Transformation](#data-transformation)
- [Data Mapping](#data-mapping)
- [Item Linking](#item-linking)
- [Common Expressions](#common-expressions)
- [Common Pitfalls](#common-pitfalls)

## Data Structure

All data flowing between n8n nodes follows a consistent format: an **array of items**, where each item contains a `json` key (and optionally a `binary` key).

```json
[
  {
    "json": {
      "name": "Alice",
      "email": "alice@example.com",
      "age": 30
    }
  },
  {
    "json": {
      "name": "Bob",
      "email": "bob@example.com",
      "age": 25
    }
  }
]
```

### Key Rules

- Every piece of data is wrapped in `{ "json": { ... } }`
- Multiple data items form an array
- Most nodes process **each item independently** and sequentially
- The Code node auto-wraps plain objects in the `json` key (since v0.166.0)

## Items and JSON

An **item** is a single data object flowing through the workflow. When a node receives an array of items, it runs its operation once per item.

### How Nodes Process Items

```
HTTP Request returns 3 items:
  [{ json: { id: 1 } }, { json: { id: 2 } }, { json: { id: 3 } }]

Connected Gmail node sends 3 separate emails:
  Email 1 → id: 1
  Email 2 → id: 2
  Email 3 → id: 3
```

### Accessing Data in the Current Item

```javascript
// In expressions:
{{ $json.name }}           // Top-level field
{{ $json.address.city }}   // Nested field (dot notation)
{{ $json['field name'] }}  // Bracket notation (for special chars)
```

## Binary Data

Files and images use the `binary` key alongside `json`:

```json
{
  "json": {
    "filename": "report.pdf"
  },
  "binary": {
    "data": {
      "data": "base64-encoded-content...",
      "mimeType": "application/pdf",
      "fileExtension": "pdf",
      "fileName": "report.pdf"
    }
  }
}
```

### Working with Binary Data

| Node | Purpose |
|------|---------|
| **Read/Write File** | Read from or write to the filesystem |
| **Convert to File** | Convert JSON to CSV, HTML, XML, etc. |
| **Extract from File** | Parse CSV, spreadsheet, or PDF to JSON |
| **HTTP Request** | Download files from URLs |
| **Edit Image** | Resize, crop, blur images |

## Expression Syntax

Expressions use double curly braces `{{ }}` and evaluate JavaScript at runtime.

### Basic Syntax

```javascript
{{ $json.fieldName }}              // Current item field
{{ $json.nested.deep.value }}      // Nested access
{{ $json['field-with-dashes'] }}   // Bracket notation
```

### JavaScript in Expressions

```javascript
// Ternary
{{ $json.status === 'active' ? 'Yes' : 'No' }}

// String methods
{{ $json.name.toUpperCase() }}
{{ $json.email.split('@')[1] }}

// Math
{{ $json.price * $json.quantity }}
{{ Math.round($json.score * 100) / 100 }}

// Multi-statement (IIFE)
{{ (() => {
  const items = $json.items;
  return items.filter(i => i.active).length;
})() }}
```

## Built-in Variables

### Data Access Variables

| Variable | Description |
|----------|-------------|
| `$json` | Current item's JSON data |
| `$binary` | Current item's binary data |
| `$input` | Data from the previous node |
| `$input.first()` | First item from previous node |
| `$input.last()` | Last item from previous node |
| `$input.all()` | All items from previous node |
| `$input.item` | Current item being processed |
| `$('Node Name')` | Reference a specific node's output |
| `$('Node Name').all()` | All items from a named node |
| `$('Node Name').first()` | First item from a named node |
| `$('Node Name').item` | Paired item from a named node |

### Workflow & Execution Variables

| Variable | Description |
|----------|-------------|
| `$workflow.id` | Current workflow ID |
| `$workflow.name` | Current workflow name |
| `$workflow.active` | Whether workflow is published |
| `$execution.id` | Current execution ID |
| `$execution.mode` | "manual" or "trigger" |
| `$execution.resumeUrl` | URL to resume a waiting execution |
| `$execution.customData` | Custom metadata object |

### Date & Time Variables

| Variable | Description |
|----------|-------------|
| `$now` | Current timestamp (Luxon DateTime) |
| `$today` | Today at midnight (Luxon DateTime) |
| `$now.toISO()` | ISO 8601 string |
| `$today.minus(7, 'days')` | 7 days ago |
| `$now.toFormat('yyyy-MM-dd')` | Formatted date string |

### Environment & Instance Variables

| Variable | Description |
|----------|-------------|
| `$vars.variableName` | Custom instance variable |
| `$env.VARIABLE_NAME` | Environment variable (if allowed) |
| `$prevNode.name` | Name of the previous node |
| `$prevNode.outputIndex` | Output index used |
| `$runIndex` | Current run index (for loops) |
| `$itemIndex` | Index of current item (0-based) |
| `$position` | Position in the items array |
| `$pageCount` | Current page (pagination in HTTP Request) |

## Data Transformation

### Edit Fields (Set) Node

The primary node for reshaping data:

```
Operations:
  - Set: Add or overwrite fields
  - Rename: Change field names
  - Remove: Delete fields
  
  Include: Only specified fields | All fields plus additions
```

### Code Node Transformation

```javascript
// Run Once for All Items mode
const results = [];
for (const item of $input.all()) {
  results.push({
    json: {
      fullName: `${item.json.firstName} ${item.json.lastName}`,
      email: item.json.email.toLowerCase(),
      isActive: item.json.status === 'active'
    }
  });
}
return results;
```

### Expressions for Inline Transformation

```javascript
// In an Edit Fields node:
Full Name: {{ $json.firstName + ' ' + $json.lastName }}
Domain:    {{ $json.email.split('@')[1] }}
Year:      {{ $now.year }}
Slug:      {{ $json.title.toLowerCase().replace(/\s+/g, '-') }}
```

### Luxon Date Transformation

n8n uses [Luxon](https://moment.github.io/luxon/) for date handling:

```javascript
{{ $now.toISO() }}                         // 2026-07-27T14:30:00.000Z
{{ $today.plus({ days: 7 }).toISODate() }} // 2026-08-03
{{ $now.toFormat('dd/MM/yyyy HH:mm') }}    // 27/07/2026 14:30
{{ $now.diff($json.createdAt, 'days') }}   // days between dates
{{ DateTime.fromISO($json.date) }}         // parse ISO string
```

## Data Mapping

### Drag-and-Drop Mapping

In the node parameter panel:

1. Open the **Input** panel on the left
2. Drag a field from Input to a parameter field
3. n8n auto-creates the expression `{{ $json.fieldName }}`

### Mapping from Specific Nodes

```javascript
// Reference a node by name
{{ $('HTTP Request').item.json.data.id }}

// Check if a node has executed
{{ $('Previous Node').isExecuted }}

// Get all items from a specific node
{{ $('Fetch Users').all().length }}
```

## Item Linking

n8n tracks the relationship between input and output items through **item linking**. This enables referencing the corresponding item from a previous node even when items are filtered or transformed.

### Paired Items

```javascript
// Access the paired item from a named node
{{ $('Earlier Node').item.json.originalId }}
// Returns the item from 'Earlier Node' that corresponds
// to the current item being processed
```

### Preserving Links in Code Node

When generating output items in the Code node, preserve linking:

```javascript
// Each output item references which input item produced it
return $input.all().map((item, index) => ({
  json: { transformed: item.json.value * 2 },
  pairedItem: { item: index }
}));
```

## Common Expressions

```javascript
// Conditional default values
{{ $json.name ?? 'Unknown' }}
{{ $json.count || 0 }}

// Array operations
{{ $json.tags.join(', ') }}
{{ $json.items.length }}
{{ $json.items.map(i => i.name) }}
{{ $json.items.filter(i => i.active) }}

// Object operations
{{ Object.keys($json).length }}
{{ JSON.stringify($json.data) }}
{{ JSON.parse($json.rawJson) }}

// String operations
{{ $json.text.trim() }}
{{ $json.url.includes('https') }}
{{ $json.csv.split(',').map(s => s.trim()) }}

// Number formatting
{{ $json.price.toFixed(2) }}
{{ parseInt($json.stringNumber, 10) }}
```

## Common Pitfalls

- **Expressions evaluate per item** — `$json` refers to the current item, not all items
- **Dot vs bracket notation** — field names with spaces, hyphens, or special characters require bracket notation: `$json['field-name']`
- **Referencing unexecuted nodes** — expressions referencing a node that hasn't run in the current execution will error
- **Luxon vs native Date** — n8n uses Luxon for dates; avoid `new Date()` in expressions
- **Binary data not in $json** — file content lives in `$binary`, not `$json`
- **Empty items** — if a node produces no items, downstream nodes won't execute unless "Always Output Data" is enabled

## Related Topics

- Flow Logic → `04-flow-logic.md`
- Code Node → `05-code-node.md`
- HTTP Request → `06-http-request-and-apis.md`
