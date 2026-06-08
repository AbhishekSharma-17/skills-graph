# Temporal — Message Passing (Signals, Queries, Updates)

> Source: [docs.temporal.io/develop/python/message-passing](https://docs.temporal.io/develop/python/message-passing)

## Table of Contents

- [Overview](#overview)
- [Queries — Read State](#queries--read-state)
- [Signals — Modify State Asynchronously](#signals--modify-state-asynchronously)
- [Updates — Modify State Synchronously](#updates--modify-state-synchronously)
- [Sending Messages from Clients](#sending-messages-from-clients)
- [Signal-With-Start](#signal-with-start)
- [Update-With-Start](#update-with-start)
- [Wait Conditions](#wait-conditions)
- [Async Handlers with Concurrency Control](#async-handlers-with-concurrency-control)
- [Dynamic Handlers](#dynamic-handlers)
- [Handler Lifecycle](#handler-lifecycle)

## Overview

Workflows are stateful services that receive three message types:

| Message | Direction | Mutates State | Returns Value | Async Handlers |
|---------|-----------|--------------|---------------|----------------|
| **Query** | Read | No | Yes | No |
| **Signal** | Write | Yes | No | Yes |
| **Update** | Read/Write | Yes | Yes | Yes |

All handlers use decorators on workflow class methods. Parameters and return values must be serializable.

## Queries — Read State

Queries synchronously retrieve workflow state without mutating it:

```python
from dataclasses import dataclass
from temporalio import workflow

@dataclass
class GetLanguagesInput:
    include_unsupported: bool = False

@workflow.defn
class TranslationWorkflow:
    def __init__(self):
        self.translations: dict[str, str] = {}
        self.status = "initializing"

    @workflow.query
    def get_status(self) -> str:
        return self.status

    @workflow.query
    def get_translations(self, input: GetLanguagesInput) -> dict[str, str]:
        if input.include_unsupported:
            return self.translations
        return {k: v for k, v in self.translations.items() if v != "unsupported"}
```

Key rules:
- Must use `def` (not `async def`)
- Cannot perform async operations (no Activities, no sleeps)
- Do not add events to Event History
- Work on closed workflow executions within retention period

## Signals — Modify State Asynchronously

Signals asynchronously modify workflow state. The server accepts them immediately without waiting for processing:

```python
@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self.approved = False
        self.approver: str | None = None

    @workflow.signal
    def approve(self, approver_name: str) -> None:
        self.approved = True
        self.approver = approver_name

    @workflow.signal
    async def process_document(self, doc_id: str) -> None:
        # Async signals can execute activities
        await workflow.execute_activity(
            validate_document,
            doc_id,
            start_to_close_timeout=timedelta(seconds=10),
        )

    @workflow.run
    async def run(self) -> str:
        await workflow.wait_condition(lambda: self.approved)
        return f"Approved by {self.approver}"
```

Signals can be `async def`, enabling Activities, Child Workflows, timers, and wait conditions.

## Updates — Modify State Synchronously

Updates synchronously request state changes and return results. They can include validators:

```python
from enum import Enum

class Language(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    CHINESE = "zh"

@workflow.defn
class GreetingWorkflow:
    def __init__(self):
        self.language = Language.ENGLISH
        self.greetings = {
            Language.ENGLISH: "Hello",
            Language.SPANISH: "Hola",
        }

    @workflow.update
    def set_language(self, language: Language) -> Language:
        previous = self.language
        self.language = language
        return previous

    @set_language.validator
    def validate_language(self, language: Language) -> None:
        if language not in self.greetings:
            raise ValueError(f"{language.name} is not supported")
```

Validators reject updates before they're recorded in history. This means invalid updates never affect the workflow state.

### Async Updates

For long-running operations:

```python
@workflow.update
async def add_translation(self, language: Language) -> str:
    greeting = await workflow.execute_activity(
        fetch_translation,
        language,
        start_to_close_timeout=timedelta(seconds=10),
    )
    self.greetings[language] = greeting
    return greeting
```

## Sending Messages from Clients

### Sending Queries

```python
handle = client.get_workflow_handle_for(TranslationWorkflow.run, "wf-123")

status = await handle.query(TranslationWorkflow.get_status)
translations = await handle.query(
    TranslationWorkflow.get_translations,
    GetLanguagesInput(include_unsupported=True),
)
```

### Sending Signals

```python
await handle.signal(ApprovalWorkflow.approve, "manager@example.com")
```

The call returns when the server accepts the signal, not when it's processed.

### Sending Updates

```python
# Wait for completion
previous_lang = await handle.execute_update(
    GreetingWorkflow.set_language,
    Language.SPANISH,
)

# Start update without waiting for completion (async handlers)
update_handle = await handle.start_update(
    GreetingWorkflow.add_translation,
    Language.CHINESE,
)
result = await update_handle.result()
```

## Signal-With-Start

Atomically start a workflow and send a signal:

```python
await client.start_workflow(
    ShoppingCartWorkflow.run,
    id="cart-user-456",
    task_queue="carts",
    start_signal="add_item",
    start_signal_args=["product-789"],
)
```

If the workflow already exists, only the signal is sent. If it doesn't exist, both happen atomically.

## Update-With-Start

Send an update, creating the workflow if it doesn't exist:

```python
from temporalio.client import WithStartWorkflowOperation
from temporalio import common

start_op = WithStartWorkflowOperation(
    ShoppingCartWorkflow.run,
    id=f"cart-{user_id}",
    id_conflict_policy=common.WorkflowIDConflictPolicy.USE_EXISTING,
    task_queue="carts",
)

price = await client.execute_update_with_start_workflow(
    ShoppingCartWorkflow.add_item,
    ShoppingCartItem(sku="prod-123", quantity=2),
    start_workflow_operation=start_op,
)
```

## Wait Conditions

Block workflow execution until a condition becomes true:

```python
@workflow.defn
class BatchWorkflow:
    def __init__(self):
        self.items: list[str] = []
        self.sealed = False

    @workflow.signal
    def add_item(self, item: str) -> None:
        self.items.append(item)

    @workflow.signal
    def seal(self) -> None:
        self.sealed = True

    @workflow.run
    async def run(self) -> list[str]:
        # Wait for batch to fill or seal
        await workflow.wait_condition(
            lambda: len(self.items) >= 100 or self.sealed
        )
        return self.items
```

### Ensure All Handlers Complete

Before workflow completion, wait for all signal and update handlers to finish:

```python
@workflow.run
async def run(self) -> str:
    # ... main logic ...
    await workflow.wait_condition(workflow.all_handlers_finished)
    return "done"
```

## Async Handlers with Concurrency Control

Async signal/update handlers can race. Use locks to prevent concurrent modifications:

```python
import asyncio

@workflow.defn
class InventoryWorkflow:
    def __init__(self):
        self.stock = 0
        self.lock = asyncio.Lock()

    @workflow.update
    async def adjust_stock(self, delta: int) -> int:
        async with self.lock:
            current = await workflow.execute_activity(
                get_current_stock,
                start_to_close_timeout=timedelta(seconds=5),
            )
            self.stock = current + delta
            await workflow.execute_activity(
                set_stock,
                self.stock,
                start_to_close_timeout=timedelta(seconds=5),
            )
        return self.stock
```

## Dynamic Handlers

Handle unknown signal/query/update names by adding `dynamic=True`:

```python
from temporalio.common import RawValue

@workflow.signal(dynamic=True)
async def dynamic_signal(self, name: str, args: Sequence[RawValue]) -> None:
    payload = workflow.payload_converter().from_payload(
        args[0].payload, dict
    )
    self.events.append({"signal": name, "data": payload})

@workflow.query(dynamic=True)
def dynamic_query(self, name: str, args: Sequence[RawValue]) -> str:
    return f"Query {name} received"
```

## Handler Lifecycle

Signals and updates have an important lifecycle consideration: handlers might still be running when the main workflow method returns. Always wait for handlers to complete:

```python
@workflow.run
async def run(self) -> str:
    result = await self._do_main_work()

    # Critical: wait for in-flight handlers
    await workflow.wait_condition(workflow.all_handlers_finished)

    return result
```

If handlers are still running when the workflow completes, they are cancelled. This can lead to lost work if handlers perform important operations.
