# Agno Workflow Patterns

Complete code examples for every workflow pattern. Each example is self-contained and runnable.

## Sub-References

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **Sequential & Parallel** | `workflow-patterns/sequential-parallel.md` | Sequential pipelines, parallel data gathering, parallel-to-sequential patterns |
| **Conditional, Loop & Router** | `workflow-patterns/conditional-loop-router.md` | If/else branching, iterative refinement loops, dynamic routing, early stopping |
| **Advanced Patterns** | `workflow-patterns/advanced-patterns.md` | Mixed execution (agents+teams+functions), background polling, conversational workflows, full production example, additional data, streaming events |

## Pattern Quick Reference

| Pattern | Class | Use When |
|---------|-------|----------|
| Sequential | `Workflow(steps=[...])` | Linear processes with clear phases |
| Parallel | `Parallel(...)` | Independent tasks that can run simultaneously |
| Conditional | `Condition(evaluator=...)` | Quality gates, adaptive pipelines |
| Loop | `Loop(end_condition=...)` | Iterative refinement, retry logic |
| Router | `Router(selector=...)` | Topic-specific routing, expertise selection |
| Mixed | Agent + Team + Function steps | Complex pipelines combining all types |
| Background | `workflow.arun(background=True)` | API/UI integration, long-running tasks |
| Conversational | `WorkflowAgent` | Multi-turn chat with workflow trigger |
