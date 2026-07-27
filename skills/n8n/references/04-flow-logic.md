# Flow Logic

> Source: https://docs.n8n.io/build/flow-logic/

## Table of Contents

- [Branching with Conditionals](#branching-with-conditionals)
- [Merging Data](#merging-data)
- [Looping](#looping)
- [Wait and Pause](#wait-and-pause)
- [Sub-Workflows](#sub-workflows)
- [Execution Order](#execution-order)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Branching with Conditionals

### If Node

Binary branching — splits execution into True and False paths based on a condition.

```
If Node Configuration:
  Condition: {{ $json.status }} equals "active"
  
  Output 1 (True)  → Process active items
  Output 2 (False) → Handle inactive items
```

#### Condition Types

| Type | Operators |
|------|-----------|
| **String** | equals, not equals, contains, starts with, ends with, regex match |
| **Number** | equals, not equals, greater than, less than, between |
| **Boolean** | is true, is false |
| **Date/Time** | before, after, between |
| **Array** | contains, length equals |
| **Object** | exists, not exists |

#### Multiple Conditions

```
Combine With: AND | OR

Condition 1: $json.age > 18
AND
Condition 2: $json.country === 'US'
```

### Switch Node

Multi-path branching — route items to different outputs based on value matching.

```
Switch Node Configuration:
  Mode: Rules | Expression
  
  Rules mode:
    Output 0: $json.priority === 'high'   → Urgent handling
    Output 1: $json.priority === 'medium' → Normal queue
    Output 2: $json.priority === 'low'    → Batch later
    Fallback: None of the above            → Default path
```

### Filter Node

Remove items that don't match criteria (single output, no branching):

```
Filter Node:
  Condition: $json.amount > 100
  → Only items with amount > 100 pass through
```

## Merging Data

### Merge Node

Combine data from two or more inputs:

| Mode | Behavior |
|------|----------|
| **Append** | Concatenate all items from all inputs |
| **Combine** | Match items between inputs (like SQL JOIN) |
| **Choose Branch** | Select items from only one input branch |

#### Combine Sub-Modes

```
Merge by Position:
  Input 1: [A, B, C]
  Input 2: [1, 2, 3]
  Result:  [A+1, B+2, C+3]

Merge by Fields:
  Input 1: [{ id: 1, name: 'Alice' }]
  Input 2: [{ id: 1, email: 'alice@ex.com' }]
  Match field: id
  Result:  [{ id: 1, name: 'Alice', email: 'alice@ex.com' }]

Multiplex:
  Input 1: [A, B]
  Input 2: [1, 2]
  Result:  [A+1, A+2, B+1, B+2]  (cartesian product)
```

### Compare Datasets Node

Find differences between two data sets:

```
Operations:
  - Items in A but not B
  - Items in B but not A
  - Items in both A and B
  - Items different between A and B
```

## Looping

### Loop Over Items (Split In Batches)

Process items in configurable batch sizes:

```
Loop Over Items Configuration:
  Batch Size: 10
  
  → Processes 10 items per iteration
  → Loops back to process next batch
  → Completes when all items processed
```

Use cases:
- Rate-limited API calls (process 10 at a time with a Wait node between batches)
- Memory management for large datasets
- Progress tracking across batches

### Loop with If Node

Create custom loops by connecting the If node's output back to an earlier node:

```
Set counter = 0
  → Process step
  → Increment counter
  → If counter < 10 → Loop back to Process step
  → If counter >= 10 → Continue to next node
```

### Looping with Code Node

```javascript
// Process in custom batches
const allItems = $input.all();
const batchSize = 50;
const results = [];

for (let i = 0; i < allItems.length; i += batchSize) {
  const batch = allItems.slice(i, i + batchSize);
  // Process batch...
  results.push(...batch);
}

return results;
```

## Wait and Pause

### Wait Node

Pause execution for a specified time or until an external event:

```
Wait Mode: After Time Interval
  Amount: 5
  Unit: Seconds | Minutes | Hours | Days

Wait Mode: On Webhook Call
  → Pauses until an external HTTP call resumes execution
  → Provides a resume URL via $execution.resumeUrl

Wait Mode: At Specified Time
  → Resume at a specific date/time
```

### Human-in-the-Loop Pattern

```
Process data
  → Send approval request (email/Slack with resume URL)
  → Wait node (On Webhook Call)
  → [User clicks approve/reject link]
  → If approved → Continue processing
  → If rejected → Notify and stop
```

## Sub-Workflows

### Execute Workflow Node

Call another workflow as a sub-step:

```
Execute Workflow Configuration:
  Source: Database | Parameter | URL
  Workflow: Select from saved workflows
  Mode: Normal | Each Item

  → Passes data to the called workflow
  → Receives the called workflow's output
  → Parent execution includes sub-workflow duration
```

### Execute Workflow Trigger

Place this trigger in the called workflow to receive data from the parent:

```
Parent Workflow:
  ... → Execute Workflow (calls "Process Order")

Called Workflow ("Process Order"):
  Execute Workflow Trigger → Validate → Save → Return result
```

### When to Use Sub-Workflows

- **Reusability** — share common logic across multiple workflows
- **Organization** — break complex workflows into manageable pieces
- **Error isolation** — sub-workflow errors don't crash the parent
- **Team collaboration** — different teams maintain different sub-workflows

### Caller Policy

Control which workflows can call this workflow as a sub-workflow:

| Policy | Access Level |
|--------|-------------|
| **Workflows from same owner** | Only your own workflows |
| **Any workflow** | Any workflow in the instance |
| **None** | Cannot be called as sub-workflow |

## Execution Order

### Default Order

Nodes execute left-to-right following connections. When a node has multiple outputs (like If), each branch executes independently.

### Multiple Inputs

When a node receives connections from multiple nodes:

1. The node waits for **all** connected inputs to complete
2. Data from each input is available on separate input indices
3. Use the Merge node for explicit control over how inputs combine

### Parallel Branches

After a branching node (If, Switch), each branch executes in sequence, not in parallel. The branches run one after another in top-to-bottom order.

## Common Patterns

### Retry with Backoff

```
HTTP Request (to flaky API)
  → If ($json.error exists)
    → True: Wait (exponential backoff) → Loop back to HTTP Request
    → False: Continue processing
```

### Data Pipeline

```
Schedule Trigger (daily)
  → HTTP Request (fetch raw data)
  → Code node (transform and clean)
  → Filter (remove invalid records)
  → Split In Batches (10 at a time)
  → HTTP Request (POST to destination API)
  → Wait (1 second between batches)
  → Loop back for next batch
```

### Fan-Out / Fan-In

```
Trigger
  → Split Out (one item per record)
  → HTTP Request (enrich each record individually)
  → Aggregate (recombine all results)
  → Output
```

## Common Pitfalls

- **Infinite loops** — always ensure loop exit conditions are reachable; use a counter as a safety valve
- **Branch execution order** — branches run sequentially (top-to-bottom), not in parallel
- **Merge node timing** — the Merge node waits for both inputs; if one branch filters out all items, the Merge node may hang unless configured with "Choose Branch" or "Always Output Data" is set on the filtering node
- **Sub-workflow data passing** — ensure the called workflow has an Execute Workflow Trigger to receive data
- **Wait node limitations** — waiting executions consume resources; excessive waits can exhaust execution limits
- **Batch processing** — Loop Over Items always returns to the same node; complex loops require careful connection routing

## Related Topics

- Data Structure → `03-data-structure-and-expressions.md`
- Error Handling → `08-error-handling.md`
- Code Node → `05-code-node.md`
