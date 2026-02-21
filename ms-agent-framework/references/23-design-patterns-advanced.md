# Design Patterns: Advanced Patterns

Advanced design patterns for the Microsoft Agent Framework provide sophisticated patterns for building robust, scalable, and maintainable agent-based workflows. This reference covers eight essential patterns used in production systems.

## 1. Circuit Breaker Pattern

The Circuit Breaker pattern prevents cascading failures by monitoring agent and LLM call success rates. It implements a state machine with three states: CLOSED (normal operation), OPEN (failing, stop calls), and HALF_OPEN (testing recovery).

### When to Use

Use the Circuit Breaker pattern when:
- Calling external LLM APIs that may become temporarily unavailable
- Protecting downstream services from overload
- Need graceful degradation with fallback strategies
- Want to distinguish between transient and permanent failures
- Implementing timeout-based recovery mechanisms
- Building resilient multi-agent systems with interdependencies

### Architecture

The Circuit Breaker maintains state across multiple calls and transitions between states based on success/failure thresholds:

```
CLOSED (Normal)
  ↓ (failure_threshold reached)
OPEN (Failing - reject calls)
  ↓ (after timeout)
HALF_OPEN (Testing)
  ↓ (success) → CLOSED
  ↓ (failure) → OPEN
```

### Implementation

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass, field
from agent_framework import WorkflowContext, handler, executor, Executor
import asyncio
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close from half_open
    timeout_seconds: int = 60   # Time before transitioning from open to half_open

class CircuitBreakerExecutor(Executor):
    """
    Executor that implements the Circuit Breaker pattern for fault tolerance.
    Monitors success/failure rates and prevents cascading failures.
    """

    def __init__(
        self,
        executor: Executor,
        config: CircuitBreakerConfig,
        fallback_strategy: str = "cached_response",
        fallback_value: Any = None
    ):
        self.executor = executor
        self.config = config
        self.fallback_strategy = fallback_strategy
        self.fallback_value = fallback_value

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_successful_response: Optional[Any] = None
        self.call_history: Dict[str, Any] = {}

    def _is_transient_error(self, error: Exception) -> bool:
        """Determine if error is transient (retry-able) or permanent."""
        transient_errors = (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        )
        error_message = str(error).lower()
        transient_messages = ["timeout", "connection", "temporary", "unavailable"]

        return isinstance(error, transient_errors) or any(
            msg in error_message for msg in transient_messages
        )

    def _should_attempt_call(self) -> bool:
        """Determine if we should attempt the call based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return False
            elapsed = datetime.now() - self.last_failure_time
            if elapsed.total_seconds() >= self.config.timeout_seconds:
                logger.info("Circuit transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _handle_fallback(self, context: WorkflowContext) -> Any:
        """Execute fallback strategy when circuit is open."""
        if self.fallback_strategy == "cached_response":
            if self.last_successful_response is not None:
                logger.info("Using cached response due to open circuit")
                return self.last_successful_response
            return None

        elif self.fallback_strategy == "default":
            logger.info("Using default fallback value")
            return self.fallback_value

        elif self.fallback_strategy == "error":
            raise RuntimeError(
                f"Circuit breaker is {self.state.value}. Service unavailable."
            )

        return None

    async def execute(self, context: WorkflowContext) -> Any:
        """Execute with circuit breaker protection."""
        if not self._should_attempt_call():
            logger.warning(
                f"Circuit breaker OPEN. Returning fallback. "
                f"Failures: {self.failure_count}"
            )
            return self._handle_fallback(context)

        try:
            logger.debug(f"Circuit state: {self.state.value}")
            result = await self.executor.execute(context)

            # Success handling
            self.failure_count = 0
            self.last_successful_response = result

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    logger.info("Circuit transitioning to CLOSED")
                    self.state = CircuitState.CLOSED
                    self.success_count = 0

            return result

        except Exception as error:
            is_transient = self._is_transient_error(error)

            self.failure_count += 1
            self.last_failure_time = datetime.now()

            logger.warning(
                f"Executor failed. Transient: {is_transient}. "
                f"Failures: {self.failure_count}/{self.config.failure_threshold}"
            )

            if self.state == CircuitState.HALF_OPEN:
                logger.error("Circuit reopening due to failure in HALF_OPEN state")
                self.state = CircuitState.OPEN

            elif self.failure_count >= self.config.failure_threshold:
                logger.error("Circuit breaker opening due to failure threshold")
                self.state = CircuitState.OPEN

            if self.state == CircuitState.OPEN:
                return self._handle_fallback(context)

            raise error

@handler
async def llm_call_handler(
    context: WorkflowContext,
    prompt: str,
    use_circuit_breaker: bool = True
) -> str:
    """Handler that uses circuit breaker for LLM calls."""

    async def inner_executor(ctx: WorkflowContext) -> str:
        # Simulate LLM call
        logger.info(f"Making LLM call with prompt: {prompt[:50]}...")
        if len(prompt) < 10:
            raise TimeoutError("Simulated timeout")
        return f"Response to: {prompt}"

    if use_circuit_breaker:
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=30
        )
        breaker = CircuitBreakerExecutor(
            executor=inner_executor,
            config=config,
            fallback_strategy="cached_response"
        )
        return await breaker.execute(context)
    else:
        return await inner_executor(context)
```

### Key Considerations

- **Timeout Configuration**: Set timeout_seconds appropriately for your use case. Too short causes rapid state transitions, too long leaves circuit open too long.
- **Distinguishing Failures**: Implement `_is_transient_error()` to differentiate between recoverable (timeout) and permanent (auth) failures.
- **Fallback Strategy**: Choose between cached responses (returns last known good), default values, or raising errors. Cached responses are safest for read operations.
- **Thresholds**: Tune failure_threshold and success_threshold based on traffic patterns and acceptable error rates.
- **Monitoring**: Log state transitions and failure counts for observability and debugging.

### Complete Workflow Example

```python
from agent_framework import WorkflowBuilder, WorkflowContext

async def circuit_breaker_workflow():
    builder = WorkflowBuilder("CircuitBreakerDemo")

    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=60
    )

    breaker_executor = CircuitBreakerExecutor(
        executor=llm_call_handler,
        config=config,
        fallback_strategy="cached_response"
    )

    # Add task with circuit breaker
    builder.add_task(
        name="protected_llm_call",
        executor=breaker_executor,
        inputs={
            "prompt": "What is machine learning?",
            "use_circuit_breaker": True
        }
    )

    # Add recovery task after circuit opens
    builder.add_task(
        name="fallback_handler",
        executor=llm_call_handler,
        inputs={
            "prompt": "Simple response",
            "use_circuit_breaker": False
        },
        depends_on=["protected_llm_call"]
    )

    context = WorkflowContext()
    result = await builder.execute(context)
    return result
```

---

## 2. Load Balancing Pattern

The Load Balancing pattern distributes agent work across multiple instances using strategies like round-robin, least-loaded, or weighted distribution. This improves throughput and prevents any single agent from becoming a bottleneck.

### When to Use

Use the Load Balancing pattern when:
- Running multiple agent instances with different capabilities
- Need to distribute high volume of requests evenly
- Some agents are faster or more reliable than others
- Want to scale agents horizontally
- Need health checking and dynamic weight adjustment
- Building systems with heterogeneous agents (different models, capabilities)

### Architecture

```
LoadBalancerExecutor
  ├── Agent 1 (weight: 1.0)
  ├── Agent 2 (weight: 1.0)
  └── Agent 3 (weight: 0.5)

Strategy:
  - Round-robin: Sequential distribution
  - Least-loaded: Route to agent with fewest pending tasks
  - Weighted: Distribute based on assigned weights
```

### Implementation

```python
from enum import Enum
from typing import List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from agent_framework import Executor, WorkflowContext, handler
import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"

@dataclass
class AgentHealth:
    agent_id: str
    healthy: bool = True
    pending_tasks: int = 0
    success_count: int = 0
    failure_count: int = 0
    response_time_ms: float = 0.0
    weight: float = 1.0

class LoadBalancerExecutor(Executor):
    """
    Executor that distributes work across multiple agent instances
    using various load balancing strategies.
    """

    def __init__(
        self,
        agents: List[Executor],
        agent_ids: Optional[List[str]] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        health_check_interval_seconds: int = 30,
        enable_sticky_sessions: bool = False
    ):
        self.agents = agents
        self.agent_ids = agent_ids or [f"agent_{i}" for i in range(len(agents))]
        self.strategy = strategy
        self.health_check_interval = health_check_interval_seconds
        self.enable_sticky_sessions = enable_sticky_sessions

        # Health tracking
        self.health: Dict[str, AgentHealth] = {
            aid: AgentHealth(agent_id=aid) for aid in self.agent_ids
        }

        # Load tracking
        self.current_index = 0  # For round-robin
        self.pending_tasks: Dict[str, int] = defaultdict(int)
        self.session_affinity: Dict[str, str] = {}  # context_id -> agent_id

    async def _check_agent_health(self, agent_id: str, agent: Executor) -> bool:
        """Health check by sending a lightweight test."""
        try:
            context = WorkflowContext()
            await asyncio.wait_for(
                agent.execute(context),
                timeout=5.0
            )
            self.health[agent_id].healthy = True
            return True
        except Exception as error:
            logger.warning(f"Health check failed for {agent_id}: {error}")
            self.health[agent_id].healthy = False
            return False

    def _select_agent_round_robin(self) -> Tuple[str, Executor]:
        """Round-robin selection without health check."""
        agent_id = self.agent_ids[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agent_ids)
        agent = self.agents[self.agent_ids.index(agent_id)]
        return agent_id, agent

    def _select_agent_least_loaded(self) -> Tuple[str, Executor]:
        """Select agent with fewest pending tasks."""
        healthy_agents = [
            aid for aid in self.agent_ids
            if self.health[aid].healthy
        ]

        if not healthy_agents:
            logger.warning("No healthy agents available, using round-robin")
            return self._select_agent_round_robin()

        agent_id = min(
            healthy_agents,
            key=lambda aid: self.pending_tasks[aid]
        )
        agent = self.agents[self.agent_ids.index(agent_id)]
        return agent_id, agent

    def _select_agent_weighted(self) -> Tuple[str, Executor]:
        """Select based on assigned weights and load."""
        healthy_agents = [
            aid for aid in self.agent_ids
            if self.health[aid].healthy
        ]

        if not healthy_agents:
            return self._select_agent_round_robin()

        # Score: weight / (pending_tasks + 1)
        scores = {}
        for aid in healthy_agents:
            weight = self.health[aid].weight
            pending = self.pending_tasks[aid] + 1
            scores[aid] = weight / pending

        agent_id = max(scores, key=scores.get)
        agent = self.agents[self.agent_ids.index(agent_id)]
        return agent_id, agent

    def _select_agent(self, context: WorkflowContext) -> Tuple[str, Executor]:
        """Select agent based on strategy."""
        # Check for sticky session
        if self.enable_sticky_sessions and context.request_id in self.session_affinity:
            agent_id = self.session_affinity[context.request_id]
            if self.health[agent_id].healthy:
                agent = self.agents[self.agent_ids.index(agent_id)]
                return agent_id, agent

        # Select based on strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            agent_id, agent = self._select_agent_round_robin()
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            agent_id, agent = self._select_agent_least_loaded()
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            agent_id, agent = self._select_agent_weighted()
        else:
            agent_id, agent = self._select_agent_round_robin()

        # Store sticky session if enabled
        if self.enable_sticky_sessions:
            self.session_affinity[context.request_id] = agent_id

        return agent_id, agent

    async def execute(self, context: WorkflowContext) -> Any:
        """Execute on selected agent."""
        agent_id, agent = self._select_agent(context)

        self.pending_tasks[agent_id] += 1
        self.health[agent_id].pending_tasks = self.pending_tasks[agent_id]

        try:
            logger.info(f"Routing to {agent_id} (strategy: {self.strategy.value})")
            result = await agent.execute(context)

            self.health[agent_id].success_count += 1
            self.health[agent_id].healthy = True
            return result

        except Exception as error:
            logger.error(f"Agent {agent_id} failed: {error}")
            self.health[agent_id].failure_count += 1

            # Mark unhealthy after 3 consecutive failures
            if self.health[agent_id].failure_count >= 3:
                self.health[agent_id].healthy = False

            raise error

        finally:
            self.pending_tasks[agent_id] -= 1
            self.health[agent_id].pending_tasks = self.pending_tasks[agent_id]

    def adjust_weight(self, agent_id: str, new_weight: float) -> None:
        """Dynamically adjust agent weight based on performance."""
        if agent_id not in self.health:
            raise ValueError(f"Unknown agent: {agent_id}")
        self.health[agent_id].weight = new_weight
        logger.info(f"Adjusted weight for {agent_id} to {new_weight}")

    def get_health_status(self) -> Dict[str, AgentHealth]:
        """Get current health status of all agents."""
        return dict(self.health)
```

### Key Considerations

- **Sticky Sessions**: For stateful operations, enable sticky sessions to route requests from the same client to the same agent.
- **Health Checking**: Implement lightweight health checks without impacting throughput.
- **Weight Adjustment**: Dynamically adjust weights based on response times, reliability, or capacity.
- **Overhead**: Load balancing adds minimal overhead but avoid checking health on every request.
- **Fairness**: Round-robin ensures fairness; weighted strategies account for heterogeneous agents.

### Complete Workflow Example

```python
async def load_balancer_workflow():
    # Create multiple agent executors
    agent_executors = [
        LLMAgentExecutor("gpt-4", model_args={"temperature": 0.7}),
        LLMAgentExecutor("gpt-3.5-turbo", model_args={"temperature": 0.5}),
        LLMAgentExecutor("gpt-4", model_args={"temperature": 0.9}),
    ]

    # Create load balancer
    lb = LoadBalancerExecutor(
        agents=agent_executors,
        agent_ids=["premium_agent", "fast_agent", "creative_agent"],
        strategy=LoadBalancingStrategy.WEIGHTED,
        enable_sticky_sessions=True
    )

    # Adjust weights based on preferences
    lb.adjust_weight("fast_agent", 1.5)  # Prefer faster agent
    lb.adjust_weight("creative_agent", 0.8)

    # Execute across agents
    context = WorkflowContext()
    results = []

    for prompt in ["Tell me a story", "Solve this math problem", "Create a poem"]:
        result = await lb.execute(context)
        results.append(result)

    # Check health status
    health_status = lb.get_health_status()
    for agent_id, health in health_status.items():
        logger.info(
            f"{agent_id}: healthy={health.healthy}, "
            f"pending={health.pending_tasks}, "
            f"success={health.success_count}"
        )

    return results
```

---

## 3. Batch Processing Pattern

The Batch Processing pattern processes large datasets in parallel batches with configurable concurrency limits. This improves throughput while maintaining control over resource consumption.

### When to Use

Use the Batch Processing pattern when:
- Processing large datasets (thousands or millions of items)
- Need to respect API rate limits and concurrency constraints
- Want to parallelize independent work
- Need to aggregate results from parallel processing
- Processing items with dependencies or ordering requirements
- Building ETL pipelines and data processing workflows

### Architecture

```
Input Data (1000 items)
  ↓
BatchCollectorExecutor (create batches of 100)
  ↓
[Batch 1] [Batch 2] ... [Batch 10] (parallel processing)
  ↓
BatchProcessorExecutor (limit concurrency to 3)
  ↓
BatchAggregatorExecutor (merge results)
  ↓
Output (processed results)
```

### Implementation

```python
from typing import List, Any, Callable, Optional, Coroutine
from dataclasses import dataclass
from agent_framework import Executor, WorkflowContext, handler, WorkflowBuilder
import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    batch_size: int = 100
    max_concurrency: int = 5
    timeout_per_batch_seconds: int = 300
    fail_fast: bool = False  # Stop on first error or collect all errors
    ordered: bool = True     # Preserve item order in results

class BatchCollectorExecutor(Executor):
    """
    Executor that collects input items into batches of specified size.
    Outputs list of batches ready for parallel processing.
    """

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    async def execute(self, context: WorkflowContext) -> List[List[Any]]:
        """Collect input items and create batches."""
        items = context.get_input("items", [])

        if not items:
            logger.warning("No items provided for batching")
            return []

        batches = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batches.append(batch)

        logger.info(
            f"Created {len(batches)} batches "
            f"from {len(items)} items "
            f"(batch_size={self.batch_size})"
        )

        return batches

class BatchProcessorExecutor(Executor):
    """
    Executor that processes batches in parallel with concurrency limiting.
    Uses semaphore to control resource usage.
    """

    def __init__(
        self,
        processor_func: Callable[[List[Any]], Coroutine[Any, Any, List[Any]]],
        config: BatchConfig
    ):
        self.processor_func = processor_func
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrency)
        self.batch_results = defaultdict(list)
        self.errors = defaultdict(list)

    async def _process_batch_with_semaphore(
        self,
        batch_id: int,
        batch: List[Any]
    ) -> Tuple[int, List[Any], Optional[Exception]]:
        """Process single batch with semaphore limiting."""
        async with self.semaphore:
            try:
                logger.debug(f"Processing batch {batch_id} ({len(batch)} items)")
                result = await asyncio.wait_for(
                    self.processor_func(batch),
                    timeout=self.config.timeout_per_batch_seconds
                )
                logger.debug(f"Batch {batch_id} completed")
                return batch_id, result, None

            except asyncio.TimeoutError as error:
                logger.error(f"Batch {batch_id} timed out")
                return batch_id, [], error

            except Exception as error:
                logger.error(f"Batch {batch_id} failed: {error}")
                return batch_id, [], error

    async def execute(self, context: WorkflowContext) -> dict:
        """Process all batches in parallel."""
        batches = context.get_input("batches", [])

        if not batches:
            logger.warning("No batches provided")
            return {"results": [], "errors": []}

        # Create tasks for all batches
        tasks = [
            self._process_batch_with_semaphore(i, batch)
            for i, batch in enumerate(batches)
        ]

        logger.info(
            f"Starting parallel batch processing "
            f"({len(batches)} batches, "
            f"max_concurrency={self.config.max_concurrency})"
        )

        # Process batches
        if self.config.fail_fast:
            results = await asyncio.gather(*tasks)
        else:
            results = await asyncio.gather(*tasks, return_exceptions=False)

        # Organize results
        processed_results = [None] * len(batches)
        batch_errors = []

        for batch_id, result, error in results:
            if error:
                batch_errors.append({
                    "batch_id": batch_id,
                    "error": str(error)
                })
                if self.config.fail_fast:
                    raise error
            else:
                processed_results[batch_id] = result

        logger.info(
            f"Batch processing completed. "
            f"Errors: {len(batch_errors)}"
        )

        return {
            "batch_results": processed_results,
            "errors": batch_errors,
            "batch_count": len(batches),
            "error_count": len(batch_errors)
        }

class BatchAggregatorExecutor(Executor):
    """
    Executor that merges results from parallel batch processing.
    Handles ordering and error aggregation.
    """

    def __init__(self, config: BatchConfig):
        self.config = config

    async def execute(self, context: WorkflowContext) -> dict:
        """Aggregate batch results into final output."""
        processor_result = context.get_input("processor_result", {})

        batch_results = processor_result.get("batch_results", [])
        batch_errors = processor_result.get("errors", [])

        # Flatten results
        aggregated_results = []
        for batch_result in batch_results:
            if batch_result:
                aggregated_results.extend(batch_result)

        logger.info(
            f"Aggregated {len(aggregated_results)} items "
            f"with {len(batch_errors)} errors"
        )

        return {
            "items": aggregated_results,
            "total_count": len(aggregated_results),
            "error_count": len(batch_errors),
            "errors": batch_errors,
            "success": len(batch_errors) == 0
        }

async def example_processor(batch: List[Any]) -> List[Any]:
    """Example processor function for demonstration."""
    # Simulate processing
    await asyncio.sleep(0.1)
    return [f"processed_{item}" for item in batch]
```

### Key Considerations

- **Batch Size Tuning**: Smaller batches (10-50) for quick processing, larger batches (100-500) for throughput optimization.
- **Ordering**: Preserve original order with indexed batch results for applications requiring ordered output.
- **Partial Failures**: Use fail_fast=False to collect all errors; enables better error reporting and recovery.
- **Concurrency Limits**: Match max_concurrency to available resources and API rate limits.
- **Timeout Handling**: Set appropriate timeout_per_batch_seconds based on processor complexity.

### Complete Workflow Example

```python
async def batch_processing_workflow():
    builder = WorkflowBuilder("BatchProcessingDemo")

    config = BatchConfig(
        batch_size=100,
        max_concurrency=3,
        timeout_per_batch_seconds=300,
        fail_fast=False,
        ordered=True
    )

    # Task 1: Collect items into batches
    builder.add_task(
        name="collect_batches",
        executor=BatchCollectorExecutor(batch_size=config.batch_size),
        inputs={
            "items": list(range(1000))
        }
    )

    # Task 2: Process batches in parallel
    processor = BatchProcessorExecutor(
        processor_func=example_processor,
        config=config
    )

    builder.add_task(
        name="process_batches",
        executor=processor,
        depends_on=["collect_batches"]
    )

    # Task 3: Aggregate results
    aggregator = BatchAggregatorExecutor(config)

    builder.add_task(
        name="aggregate_results",
        executor=aggregator,
        depends_on=["process_batches"]
    )

    context = WorkflowContext()
    context.set_input("items", list(range(1000)))

    result = await builder.execute(context)
    return result
```

---

## 4. Mock Agent Testing Pattern

The Mock Agent Testing pattern enables unit testing of agents without external LLM calls. It provides deterministic responses, enables testing of error handling and state transitions, and improves CI/CD integration.

### When to Use

Use the Mock Agent Testing pattern when:
- Writing unit tests for agent workflows
- Need deterministic behavior for testing
- Want to avoid API costs during testing
- Testing error handling and edge cases
- Testing reflection loops and state transitions
- Running tests in CI/CD pipelines without external dependencies

### Architecture

```
Test Code
  ↓
MockChatCompletionClient (provides predefined responses)
  ↓
Agent Workflow (executes with mocked LLM)
  ↓
Assert Results (verify behavior)
```

### Implementation

```python
from typing import List, Dict, Any, Optional, Pattern
import re
from agent_framework import (
    WorkflowContext,
    handler,
    executor,
    Executor
)
import pytest
import logging

logger = logging.getLogger(__name__)

class MockResponse:
    """Represents a mock LLM response."""
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.metadata = metadata or {}

class MockChatCompletionClient:
    """
    Mock client for chat completion that returns predefined responses
    in sequence, useful for deterministic testing.
    """

    def __init__(self, responses: List[str]):
        self.responses = responses
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        **kwargs
    ) -> Dict[str, Any]:
        """Return next predefined response."""
        if self.call_count >= len(self.responses):
            raise RuntimeError(
                f"Mock client exhausted: "
                f"{self.call_count} calls made, "
                f"only {len(self.responses)} responses available"
            )

        response_text = self.responses[self.call_count]
        self.call_count += 1

        # Record call history
        self.call_history.append({
            "messages": messages,
            "model": model,
            "kwargs": kwargs,
            "response": response_text
        })

        return {
            "choices": [
                {
                    "message": {
                        "content": response_text,
                        "role": "assistant"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": len(response_text.split()),
                "total_tokens": 10 + len(response_text.split())
            }
        }

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of all calls made."""
        return self.call_history

class ParameterizedMockClient:
    """
    Advanced mock client that uses pattern matching
    to return responses based on input patterns.
    """

    def __init__(self, patterns: Dict[Pattern, str]):
        self.patterns = {
            re.compile(p): response
            for p, response in patterns.items()
        }
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Return response matching input pattern."""
        # Get last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            raise ValueError("No user message found")

        # Find matching pattern
        response_text = None
        for pattern, response in self.patterns.items():
            if pattern.search(user_message):
                response_text = response
                break

        if not response_text:
            raise ValueError(
                f"No pattern matched for: {user_message}"
            )

        self.call_count += 1
        self.call_history.append({
            "user_message": user_message,
            "response": response_text
        })

        return {
            "choices": [{"message": {"content": response_text}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

# Pytest fixtures for common mock setups

@pytest.fixture
def mock_greeting_client():
    """Fixture providing a simple greeting mock client."""
    return MockChatCompletionClient([
        "Hello! How can I help?",
        "I'm ready to assist.",
        "What would you like to know?"
    ])

@pytest.fixture
def mock_math_client():
    """Fixture for math problem solving tests."""
    patterns = {
        r"(\d+)\s*\+\s*(\d+)": "The sum is 10",
        r"(\d+)\s*\*\s*(\d+)": "The product is 25",
        r"what is": "The answer depends on the context",
    }
    return ParameterizedMockClient(patterns)

@pytest.fixture
def mock_error_client():
    """Fixture simulating error responses."""
    return MockChatCompletionClient([
        '{"error": "Rate limit exceeded"}',
        '{"error": "Invalid request"}',
        "Error occurred"
    ])

# Example test functions

class TestMockAgentBehavior:
    """Test suite for agent behavior with mocks."""

    @pytest.mark.asyncio
    async def test_agent_greeting(self, mock_greeting_client):
        """Test agent returns expected greeting."""
        # Create agent with mock
        agent = MockAgentExecutor(mock_greeting_client)

        context = WorkflowContext()
        result = await agent.execute(context)

        assert "Hello" in result
        assert mock_greeting_client.call_count == 1

    @pytest.mark.asyncio
    async def test_agent_multiple_turns(self, mock_greeting_client):
        """Test agent handles multiple conversation turns."""
        agent = MockAgentExecutor(mock_greeting_client)
        context = WorkflowContext()

        # Multiple turns
        for i in range(3):
            result = await agent.execute(context)
            assert len(result) > 0

        assert mock_greeting_client.call_count == 3

    @pytest.mark.asyncio
    async def test_agent_pattern_matching(self, mock_math_client):
        """Test agent with pattern-based responses."""
        agent = MockAgentExecutor(mock_math_client)
        context = WorkflowContext()
        context.set_input("prompt", "What is 3 + 7?")

        result = await agent.execute(context)
        assert "sum" in result.lower()

    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_error_client):
        """Test agent handles error responses gracefully."""
        agent = MockAgentExecutor(mock_error_client)
        context = WorkflowContext()

        with pytest.raises(Exception):
            await agent.execute(context)

    @pytest.mark.asyncio
    async def test_reflection_loop(self, mock_greeting_client):
        """Test agent reflection loop with mock."""
        agent = MockAgentWithReflection(mock_greeting_client)
        context = WorkflowContext()

        result = await agent.execute(context)
        assert "reflection" in result or len(result) > 0

    def test_call_history(self, mock_greeting_client):
        """Test we can inspect call history."""
        history = mock_greeting_client.get_call_history()
        assert isinstance(history, list)

class MockAgentExecutor(Executor):
    """Example agent executor using mock client."""

    def __init__(self, mock_client):
        self.mock_client = mock_client

    async def execute(self, context: WorkflowContext) -> str:
        """Execute agent with mock client."""
        prompt = context.get_input("prompt", "Hello")

        response = await self.mock_client.create_chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )

        return response["choices"][0]["message"]["content"]

class MockAgentWithReflection(Executor):
    """Example agent with reflection loop using mock."""

    def __init__(self, mock_client):
        self.mock_client = mock_client

    async def execute(self, context: WorkflowContext) -> str:
        """Execute with reflection loop."""
        # Initial response
        response1 = await self.mock_client.create_chat_completion(
            messages=[{"role": "user", "content": "Initial prompt"}]
        )

        # Reflection
        response2 = await self.mock_client.create_chat_completion(
            messages=[
                {"role": "user", "content": "Initial prompt"},
                {"role": "assistant", "content": response1["choices"][0]["message"]["content"]},
                {"role": "user", "content": "Reflect on this response"}
            ]
        )

        return response2["choices"][0]["message"]["content"]
```

### Key Considerations

- **Determinism**: Mock responses are deterministic, enabling reliable testing.
- **Maintenance**: Update mock responses when agent behavior changes.
- **Coverage**: Test success paths, error handling, and edge cases.
- **CI/CD Integration**: Mock clients enable fast test execution without rate limiting.
- **Pattern Matching**: Use ParameterizedMockClient for complex scenarios with multiple input types.

### Complete Workflow Example

```python
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complete workflow with mocks."""
    mock_client = MockChatCompletionClient([
        "Analysis complete: Problem is clear",
        "Solution proposed: Use pattern X",
        "Implementation ready"
    ])

    builder = WorkflowBuilder("MockTestWorkflow")

    # Add tasks with mock executor
    builder.add_task(
        name="analyze",
        executor=MockAgentExecutor(mock_client),
        inputs={"prompt": "Analyze this problem"}
    )

    builder.add_task(
        name="propose",
        executor=MockAgentExecutor(mock_client),
        inputs={"prompt": "Propose solution"},
        depends_on=["analyze"]
    )

    context = WorkflowContext()
    result = await builder.execute(context)

    assert mock_client.call_count == 2
    assert len(mock_client.get_call_history()) == 2
```

---

## 5. Time-Travel Debugging Pattern

The Time-Travel Debugging pattern enables inspection of workflow execution history, replay of steps, and comparison of execution states. This is invaluable for understanding agent behavior and debugging complex workflows.

### When to Use

Use the Time-Travel Debugging pattern when:
- Debugging complex multi-step agent workflows
- Need to understand decision points and state transitions
- Want to compare execution paths
- Investigating unexpected agent behavior
- Analyzing performance bottlenecks
- Building audit trails for regulated systems

### Architecture

```
Workflow Execution
  ↓
ExecutionTracer (record checkpoints)
  ↓
DebugableExecutor (wrap executors)
  ↓
WorkflowDebugger (inspect, compare, replay)
  ↓
Analysis (divergence detection, step inspection)
```

### Implementation

```python
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from agent_framework import Executor, WorkflowContext
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExecutionCheckpoint:
    """Represents a single point in workflow execution."""
    step_id: str
    executor_name: str
    timestamp: datetime
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ExecutionTracer:
    """Records checkpoints during workflow execution."""

    def __init__(self):
        self.checkpoints: List[ExecutionCheckpoint] = []
        self.enabled = True

    def record_checkpoint(
        self,
        step_id: str,
        executor_name: str,
        input_state: Dict[str, Any],
        output_state: Dict[str, Any],
        execution_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a checkpoint during execution."""
        if not self.enabled:
            return

        checkpoint = ExecutionCheckpoint(
            step_id=step_id,
            executor_name=executor_name,
            timestamp=datetime.now(),
            input_state=input_state,
            output_state=output_state,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )

        self.checkpoints.append(checkpoint)
        logger.debug(
            f"Recorded checkpoint {step_id}: "
            f"{execution_time_ms:.1f}ms"
        )

    def get_checkpoints(self) -> List[ExecutionCheckpoint]:
        """Get all recorded checkpoints."""
        return self.checkpoints

    def get_checkpoint(self, step_id: str) -> Optional[ExecutionCheckpoint]:
        """Get specific checkpoint by step ID."""
        for cp in self.checkpoints:
            if cp.step_id == step_id:
                return cp
        return None

    def clear(self) -> None:
        """Clear all checkpoints."""
        self.checkpoints.clear()

    def export_json(self) -> str:
        """Export checkpoints as JSON."""
        data = {
            "checkpoints": [
                {
                    **asdict(cp),
                    "timestamp": cp.timestamp.isoformat()
                }
                for cp in self.checkpoints
            ],
            "total_steps": len(self.checkpoints),
            "total_time_ms": sum(cp.execution_time_ms for cp in self.checkpoints)
        }
        return json.dumps(data, indent=2, default=str)

class DebugableExecutor(Executor):
    """Wraps an executor and records execution traces."""

    def __init__(
        self,
        executor: Executor,
        step_id: str,
        tracer: ExecutionTracer
    ):
        self.executor = executor
        self.step_id = step_id
        self.tracer = tracer

    async def execute(self, context: WorkflowContext) -> Any:
        """Execute with tracing."""
        import time

        start_time = time.time()
        input_state = dict(context.state) if hasattr(context, 'state') else {}

        try:
            result = await self.executor.execute(context)

            output_state = dict(context.state) if hasattr(context, 'state') else {}
            execution_time = (time.time() - start_time) * 1000

            self.tracer.record_checkpoint(
                step_id=self.step_id,
                executor_name=self.executor.__class__.__name__,
                input_state=input_state,
                output_state=output_state,
                execution_time_ms=execution_time,
                success=True,
                metadata={"result_type": type(result).__name__}
            )

            return result

        except Exception as error:
            execution_time = (time.time() - start_time) * 1000
            output_state = dict(context.state) if hasattr(context, 'state') else {}

            self.tracer.record_checkpoint(
                step_id=self.step_id,
                executor_name=self.executor.__class__.__name__,
                input_state=input_state,
                output_state=output_state,
                execution_time_ms=execution_time,
                success=False,
                error_message=str(error)
            )

            raise error

class WorkflowDebugger:
    """Analyzes and debugs workflow execution using traces."""

    def __init__(self, tracer: ExecutionTracer):
        self.tracer = tracer

    def inspect_step(self, step_id: str) -> Dict[str, Any]:
        """Inspect a single step in detail."""
        cp = self.tracer.get_checkpoint(step_id)
        if not cp:
            raise ValueError(f"No checkpoint found for step: {step_id}")

        return {
            "step_id": cp.step_id,
            "executor": cp.executor_name,
            "timestamp": cp.timestamp.isoformat(),
            "execution_time_ms": cp.execution_time_ms,
            "success": cp.success,
            "error": cp.error_message,
            "input_keys": list(cp.input_state.keys()),
            "output_keys": list(cp.output_state.keys()),
            "state_changes": self._detect_state_changes(cp)
        }

    def _detect_state_changes(
        self,
        checkpoint: ExecutionCheckpoint
    ) -> Dict[str, Any]:
        """Detect what changed between input and output."""
        changes = {}

        # Find new keys
        new_keys = set(checkpoint.output_state.keys()) - set(checkpoint.input_state.keys())
        if new_keys:
            changes["added_keys"] = list(new_keys)

        # Find removed keys
        removed_keys = set(checkpoint.input_state.keys()) - set(checkpoint.output_state.keys())
        if removed_keys:
            changes["removed_keys"] = list(removed_keys)

        # Find modified values
        modified = {}
        for key in checkpoint.input_state:
            if key in checkpoint.output_state:
                if checkpoint.input_state[key] != checkpoint.output_state[key]:
                    modified[key] = {
                        "before": str(checkpoint.input_state[key])[:100],
                        "after": str(checkpoint.output_state[key])[:100]
                    }

        if modified:
            changes["modified_keys"] = modified

        return changes

    def find_divergences(
        self,
        trace1: List[ExecutionCheckpoint],
        trace2: List[ExecutionCheckpoint]
    ) -> Dict[str, Any]:
        """Compare two execution traces and find divergence points."""
        divergences = []

        min_steps = min(len(trace1), len(trace2))

        for i in range(min_steps):
            cp1, cp2 = trace1[i], trace2[i]

            if cp1.output_state != cp2.output_state:
                divergences.append({
                    "step_index": i,
                    "step_id": cp1.step_id,
                    "trace1_output": str(cp1.output_state)[:200],
                    "trace2_output": str(cp2.output_state)[:200]
                })

        return {
            "divergence_count": len(divergences),
            "divergences": divergences,
            "trace1_steps": len(trace1),
            "trace2_steps": len(trace2)
        }

    def get_execution_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of execution."""
        return [
            {
                "step": i,
                "step_id": cp.step_id,
                "executor": cp.executor_name,
                "time_ms": cp.execution_time_ms,
                "cumulative_ms": sum(
                    self.tracer.checkpoints[j].execution_time_ms
                    for j in range(i + 1)
                ),
                "success": cp.success
            }
            for i, cp in enumerate(self.tracer.checkpoints)
        ]

    def get_bottleneck_analysis(self) -> Dict[str, Any]:
        """Identify slowest steps in workflow."""
        checkpoints = self.tracer.checkpoints
        if not checkpoints:
            return {"message": "No execution data"}

        sorted_by_time = sorted(
            checkpoints,
            key=lambda cp: cp.execution_time_ms,
            reverse=True
        )

        return {
            "slowest_steps": [
                {
                    "step_id": cp.step_id,
                    "executor": cp.executor_name,
                    "time_ms": cp.execution_time_ms
                }
                for cp in sorted_by_time[:5]
            ],
            "total_time_ms": sum(cp.execution_time_ms for cp in checkpoints),
            "average_step_time_ms": sum(
                cp.execution_time_ms for cp in checkpoints
            ) / len(checkpoints)
        }

    def export_for_analysis(self) -> str:
        """Export trace for external analysis."""
        return self.tracer.export_json()
```

### Key Considerations

- **Storage Overhead**: Traces consume memory; consider periodic archival for long-running workflows.
- **Privacy**: Sanitize sensitive data before exporting traces.
- **Replay Fidelity**: Replaying requires same input state and non-deterministic components.
- **Performance**: Tracing adds overhead; consider disabling in high-performance scenarios.

### Complete Workflow Example

```python
async def time_travel_debugging_example():
    tracer = ExecutionTracer()
    debugger = WorkflowDebugger(tracer)

    # Simulate workflow with tracing
    async def step1(context):
        context.set_state({"result": "step1_output"})
        return "step1_output"

    async def step2(context):
        prev = context.get_state("result")
        context.set_state({"result": f"{prev}_step2"})
        return f"{prev}_step2"

    # Wrap with debuggable executors
    context = WorkflowContext()

    # Execute with tracing
    exec1 = DebugableExecutor(step1, "step_1", tracer)
    result1 = await exec1.execute(context)

    exec2 = DebugableExecutor(step2, "step_2", tracer)
    result2 = await exec2.execute(context)

    # Analyze
    timeline = debugger.get_execution_timeline()
    bottlenecks = debugger.get_bottleneck_analysis()
    step1_details = debugger.inspect_step("step_1")

    logger.info(f"Timeline: {timeline}")
    logger.info(f"Bottlenecks: {bottlenecks}")
    logger.info(f"Step 1: {step1_details}")
```

---

## 6. Caching Pattern

The Caching pattern reduces cost and latency by caching LLM responses. It supports in-memory caching, hash-based key generation, TTL-based expiry, and optional semantic similarity caching.

### When to Use

Use the Caching pattern when:
- LLM calls are expensive (cost or latency)
- Same or similar prompts are used repeatedly
- Want to improve response times
- Need to reduce API usage
- Building interactive systems with cached responses
- Have resource constraints limiting API rate

### Architecture

```
Prompt Input
  ↓
CachingExecutor
  ├─ Generate cache key (hash)
  ├─ Check cache (in-memory dict)
  ├─ If hit → return cached response
  └─ If miss → call LLM → store → return
```

### Implementation

```python
from typing import Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from agent_framework import Executor, WorkflowContext
import hashlib
import json
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Single cache entry with expiry."""
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: Optional[int] = None
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds

class CachingExecutor(Executor):
    """
    Executor that caches LLM responses to reduce cost and latency.
    Supports in-memory caching, TTL-based expiry, and hit tracking.
    """

    def __init__(
        self,
        executor: Executor,
        ttl_seconds: Optional[int] = 3600,  # 1 hour default
        max_cache_size: int = 1000,
        cache_key_generator: Optional[Callable] = None
    ):
        self.executor = executor
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        self.cache_key_generator = cache_key_generator or self._default_key_generator

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def _default_key_generator(self, context: WorkflowContext) -> str:
        """Generate cache key from context (hash-based)."""
        # Include relevant context data
        key_data = {
            "prompt": context.get_input("prompt", ""),
            "model": context.get_input("model", ""),
            "temperature": context.get_input("temperature", 0.7),
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _evict_oldest(self) -> None:
        """Remove oldest entry when cache is full."""
        if len(self.cache) >= self.max_cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
            logger.debug(f"Evicted cache entry: {oldest_key}")

    async def execute(self, context: WorkflowContext) -> Any:
        """Execute with caching."""
        cache_key = self.cache_key_generator(context)

        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]

            if not entry.is_expired():
                entry.hit_count += 1
                self.stats["hits"] += 1
                logger.debug(
                    f"Cache hit (key={cache_key[:8]}..., "
                    f"hits={entry.hit_count})"
                )
                # Move to end (LRU)
                self.cache.move_to_end(cache_key)
                return entry.value
            else:
                # Expired entry
                del self.cache[cache_key]
                logger.debug(f"Cache entry expired: {cache_key[:8]}...")

        # Cache miss - execute and cache
        self.stats["misses"] += 1
        logger.debug(f"Cache miss (key={cache_key[:8]}...)")

        result = await self.executor.execute(context)

        # Store in cache
        self._evict_oldest()
        self.cache[cache_key] = CacheEntry(
            key=cache_key,
            value=result,
            created_at=datetime.now(),
            ttl_seconds=self.ttl_seconds
        )

        return result

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests
            if total_requests > 0 else 0
        )

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
            "size": len(self.cache),
            "evictions": self.stats["evictions"],
            "max_size": self.max_cache_size
        }

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Cache cleared")

    def clear_expired(self) -> int:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]

        logger.info(f"Cleared {len(expired_keys)} expired entries")
        return len(expired_keys)

class SemanticCachingExecutor(Executor):
    """
    Advanced caching using semantic similarity.
    Useful for matching similar (not identical) prompts.
    """

    def __init__(
        self,
        executor: Executor,
        similarity_threshold: float = 0.95,
        embedding_func: Optional[Callable] = None
    ):
        self.executor = executor
        self.similarity_threshold = similarity_threshold
        self.embedding_func = embedding_func or self._default_embedding

        self.cache: Dict[str, Any] = {}
        self.embeddings: Dict[str, list] = {}

    def _default_embedding(self, text: str) -> list:
        """Simple embedding using character n-grams."""
        # Production would use actual embedding model
        n = 3
        grams = [text[i:i+n] for i in range(len(text)-n+1)]
        return grams

    def _cosine_similarity(self, v1: list, v2: list) -> float:
        """Calculate cosine similarity between vectors."""
        # Simplified for demonstration
        common = len(set(v1) & set(v2))
        return common / max(len(set(v1) | set(v2)), 1)

    async def execute(self, context: WorkflowContext) -> Any:
        """Execute with semantic caching."""
        prompt = context.get_input("prompt", "")

        # Check semantic similarity with cached prompts
        prompt_embedding = self._default_embedding(prompt)

        for cached_prompt, (embedding, result) in self.embeddings.items():
            similarity = self._cosine_similarity(
                prompt_embedding,
                embedding
            )

            if similarity >= self.similarity_threshold:
                logger.info(
                    f"Semantic cache hit "
                    f"(similarity={similarity:.2%})"
                )
                return result

        # No match - execute and cache
        result = await self.executor.execute(context)

        self.embeddings[prompt] = (prompt_embedding, result)
        logger.debug(f"Cached semantic result for prompt")

        return result
```

### Key Considerations

- **Cache Invalidation**: Use TTL-based expiry for automatic invalidation; implement manual clearing for version changes.
- **Storage Limits**: Use max_cache_size to prevent unbounded growth; implement LRU eviction.
- **Cache Hit Monitoring**: Track hit ratio to measure cache effectiveness.
- **Semantic Caching**: Use for fuzzy matching when exact cache hits are rare.

### Complete Workflow Example

```python
async def caching_workflow_example():
    async def llm_executor(context: WorkflowContext) -> str:
        prompt = context.get_input("prompt")
        # Simulate LLM call
        return f"Response to: {prompt}"

    # Create caching layer
    cached_executor = CachingExecutor(
        executor=llm_executor,
        ttl_seconds=3600,
        max_cache_size=1000
    )

    context = WorkflowContext()

    # First call - cache miss
    context.set_input("prompt", "What is AI?")
    result1 = await cached_executor.execute(context)

    # Second call - cache hit
    result2 = await cached_executor.execute(context)

    # Different prompt - cache miss
    context.set_input("prompt", "What is ML?")
    result3 = await cached_executor.execute(context)

    # View stats
    stats = cached_executor.get_cache_stats()
    logger.info(f"Cache stats: {stats}")
```

---

## 7. Event-Driven Agent Pattern

The Event-Driven Agent pattern enables agents to be triggered by external events (queues, webhooks). This pattern is essential for reactive, scalable systems that respond to real-time data.

### When to Use

Use the Event-Driven Agent pattern when:
- Building reactive systems triggered by external events
- Integrating with message queues (Azure Service Bus, RabbitMQ)
- Need to handle webhooks or event streams
- Want asynchronous, decoupled workflows
- Processing events from IoT devices or data streams
- Implementing event sourcing architectures

### Architecture

```
Event Source (Service Bus, Webhooks, etc.)
  ↓
EventListenerExecutor (listen for events)
  ↓
Event Routing (route to appropriate workflow)
  ↓
Agent Workflow (process event)
  ↓
Dead Letter Queue (handle failures)
```

### Implementation

```python
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum
from agent_framework import Executor, WorkflowContext
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventType(Enum):
    USER_MESSAGE = "user_message"
    SYSTEM_ALERT = "system_alert"
    DATA_UPDATE = "data_update"
    WEBHOOK = "webhook"
    CUSTOM = "custom"

@dataclass
class Event:
    """Represents an external event."""
    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: datetime
    source: str
    routing_key: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class EventQueue:
    """Simple in-memory event queue."""

    def __init__(self, maxsize: int = 1000):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self.dead_letter_queue: List[Event] = []

    async def put(self, event: Event) -> None:
        """Add event to queue."""
        await self.queue.put(event)
        logger.debug(f"Event queued: {event.event_id}")

    async def get(self, timeout: Optional[float] = None) -> Optional[Event]:
        """Get next event from queue."""
        try:
            if timeout:
                return await asyncio.wait_for(
                    self.queue.get(),
                    timeout=timeout
                )
            return await self.queue.get()
        except asyncio.TimeoutError:
            return None

    async def add_to_dlq(self, event: Event, reason: str) -> None:
        """Add event to dead letter queue."""
        self.dead_letter_queue.append(event)
        logger.warning(
            f"Event moved to DLQ: {event.event_id} "
            f"(reason: {reason})"
        )

    def get_dlq_messages(self) -> List[Event]:
        """Get messages from dead letter queue."""
        return self.dead_letter_queue.copy()

class EventListenerExecutor(Executor):
    """
    Executor that listens for events from a queue
    and routes them to workflow instances.
    """

    def __init__(
        self,
        event_queue: EventQueue,
        route_handler: Callable[[Event], str],  # Returns workflow type
        workflow_factory: Callable[[str], Executor],  # Factory for workflows
        enable_idempotency: bool = True
    ):
        self.event_queue = event_queue
        self.route_handler = route_handler
        self.workflow_factory = workflow_factory
        self.enable_idempotency = enable_idempotency

        self.processed_events: set = set()
        self.active_workflows: Dict[str, asyncio.Task] = {}

    async def _is_duplicate(self, event_id: str) -> bool:
        """Check if event was already processed (idempotency)."""
        if not self.enable_idempotency:
            return False
        return event_id in self.processed_events

    async def _process_event(self, event: Event) -> bool:
        """Process a single event."""
        try:
            # Idempotency check
            if await self._is_duplicate(event.event_id):
                logger.info(f"Duplicate event ignored: {event.event_id}")
                return True

            # Route event
            workflow_type = self.route_handler(event)
            logger.info(
                f"Routing event {event.event_id} "
                f"to workflow: {workflow_type}"
            )

            # Get workflow
            workflow = self.workflow_factory(workflow_type)

            # Execute workflow with event
            context = WorkflowContext()
            context.set_input("event", event)
            context.set_input("event_payload", event.payload)

            result = await workflow.execute(context)

            # Mark as processed
            self.processed_events.add(event.event_id)

            logger.info(f"Event processed: {event.event_id}")
            return True

        except Exception as error:
            logger.error(f"Error processing event {event.event_id}: {error}")
            return False

    async def execute(self, context: WorkflowContext) -> dict:
        """Listen for and process events."""
        max_events = context.get_input("max_events", 10)
        timeout_seconds = context.get_input("timeout_seconds", 30)

        processed_count = 0
        error_count = 0

        while processed_count < max_events:
            event = await self.event_queue.get(timeout=timeout_seconds)

            if not event:
                logger.debug("No events received (timeout)")
                break

            success = await self._process_event(event)

            if success:
                processed_count += 1
            else:
                error_count += 1

                # Retry logic
                if event.retry_count < event.max_retries:
                    event.retry_count += 1
                    await self.event_queue.put(event)
                    logger.info(
                        f"Event requeued: {event.event_id} "
                        f"(attempt {event.retry_count})"
                    )
                else:
                    await self.event_queue.add_to_dlq(
                        event,
                        "Max retries exceeded"
                    )

        return {
            "processed": processed_count,
            "errors": error_count,
            "dlq_count": len(self.event_queue.get_dlq_messages())
        }

class EventRouter:
    """Routes events to appropriate workflows."""

    def __init__(self):
        self.routes: Dict[EventType, str] = {}
        self.pattern_routes: List[tuple] = []

    def register_route(
        self,
        event_type: EventType,
        workflow_type: str
    ) -> None:
        """Register event type to workflow mapping."""
        self.routes[event_type] = workflow_type
        logger.debug(f"Registered route: {event_type.value} -> {workflow_type}")

    def register_pattern_route(
        self,
        pattern_func: Callable[[Event], bool],
        workflow_type: str
    ) -> None:
        """Register pattern-based routing."""
        self.pattern_routes.append((pattern_func, workflow_type))

    def route(self, event: Event) -> str:
        """Determine workflow for event."""
        # Check type-based routes first
        if event.event_type in self.routes:
            return self.routes[event.event_type]

        # Check pattern routes
        for pattern_func, workflow_type in self.pattern_routes:
            if pattern_func(event):
                return workflow_type

        # Default
        return "default_handler"
```

### Key Considerations

- **Idempotency**: Track processed events to handle retries without duplication.
- **Ordering**: Guarantee ordering for events that depend on sequence.
- **Scalability**: Use message queues (Azure Service Bus) for distributed processing.
- **Dead Letter Queue**: Handle permanently failed events separately for analysis.
- **Routing**: Implement flexible routing for different event types.

### Complete Workflow Example

```python
async def event_driven_workflow_example():
    # Setup
    event_queue = EventQueue(maxsize=1000)
    router = EventRouter()

    # Register routes
    router.register_route(EventType.USER_MESSAGE, "message_handler")
    router.register_route(EventType.SYSTEM_ALERT, "alert_handler")

    def workflow_factory(workflow_type: str) -> Executor:
        async def handler(ctx):
            return f"Processed by {workflow_type}"
        return handler

    # Create listener
    listener = EventListenerExecutor(
        event_queue=event_queue,
        route_handler=router.route,
        workflow_factory=workflow_factory,
        enable_idempotency=True
    )

    # Queue some events
    event1 = Event(
        event_id="evt_001",
        event_type=EventType.USER_MESSAGE,
        payload={"message": "Hello"},
        timestamp=datetime.now(),
        source="user_app"
    )

    event2 = Event(
        event_id="evt_002",
        event_type=EventType.SYSTEM_ALERT,
        payload={"alert": "High CPU"},
        timestamp=datetime.now(),
        source="monitoring"
    )

    await event_queue.put(event1)
    await event_queue.put(event2)

    # Process events
    context = WorkflowContext()
    context.set_input("max_events", 2)

    result = await listener.execute(context)
    logger.info(f"Processing result: {result}")
```

---

## 8. Fan-out/Fan-in with Dynamic Routing

The Fan-out/Fan-in pattern with dynamic routing enables distributing work across a dynamically determined number of parallel agents based on input analysis. This pattern handles complex, data-dependent parallelization.

### When to Use

Use the Fan-out/Fan-in with Dynamic Routing pattern when:
- Number of parallel tasks depends on input data
- Need to analyze input to determine parallelization strategy
- Have variable-sized datasets to process
- Want to distribute work based on content analysis
- Building adaptive, data-driven systems
- Need resource management for dynamic workloads

### Architecture

```
Input Data
  ↓
DynamicRouterExecutor (analyze and create tasks)
  ↓
[Worker 1] [Worker 2] ... [Worker N] (parallel, dynamic count)
  ↓
AggregatorExecutor (collect and merge results)
  ↓
Output
```

### Implementation

```python
from typing import List, Any, Callable, Dict, Optional
from dataclasses import dataclass
from agent_framework import Executor, WorkflowContext
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class DynamicTask:
    """Represents a dynamically created task."""
    task_id: str
    data: Any
    executor: Executor
    priority: int = 0
    timeout_seconds: Optional[float] = None

class DynamicRouterExecutor(Executor):
    """
    Executor that analyzes input and dynamically creates
    parallel tasks based on content analysis.
    """

    def __init__(
        self,
        analyzer: Callable[[Any], List[Any]],  # Returns list of subtasks
        task_creator: Callable[[Any, int], DynamicTask],  # Creates tasks
        max_workers: int = 10
    ):
        self.analyzer = analyzer
        self.task_creator = task_creator
        self.max_workers = max_workers

    async def execute(self, context: WorkflowContext) -> dict:
        """Analyze input and create dynamic tasks."""
        input_data = context.get_input("data")

        # Analyze to determine subtasks
        subtasks = await self._analyze(input_data)
        logger.info(
            f"Dynamic routing: created {len(subtasks)} tasks "
            f"from input (max_workers={self.max_workers})"
        )

        # Create task objects
        tasks = []
        for i, subtask_data in enumerate(subtasks):
            task = self.task_creator(subtask_data, i)
            tasks.append(task)

        context.set_state({
            "dynamic_tasks": tasks,
            "task_count": len(tasks)
        })

        return {
            "task_count": len(tasks),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "priority": t.priority
                }
                for t in tasks
            ]
        }

    async def _analyze(self, data: Any) -> List[Any]:
        """Analyze input to determine subtasks."""
        if callable(self.analyzer):
            return self.analyzer(data)
        return [data]

class WorkerExecutor(Executor):
    """
    Executor that processes a single subtask created by DynamicRouter.
    """

    def __init__(
        self,
        processor: Callable[[Any], Any],
        task_id: str
    ):
        self.processor = processor
        self.task_id = task_id

    async def execute(self, context: WorkflowContext) -> dict:
        """Process assigned task."""
        task_data = context.get_input("task_data")

        try:
            logger.debug(f"Worker processing task: {self.task_id}")
            result = self.processor(task_data)

            return {
                "task_id": self.task_id,
                "success": True,
                "result": result
            }

        except Exception as error:
            logger.error(f"Task {self.task_id} failed: {error}")
            return {
                "task_id": self.task_id,
                "success": False,
                "error": str(error)
            }

class AggregatorExecutor(Executor):
    """
    Executor that collects and merges results from parallel workers.
    Handles partial failures and result ordering.
    """

    def __init__(
        self,
        merge_strategy: str = "append",  # append, dict, custom
        preserve_order: bool = True,
        allow_partial_failure: bool = True
    ):
        self.merge_strategy = merge_strategy
        self.preserve_order = preserve_order
        self.allow_partial_failure = allow_partial_failure

    async def execute(self, context: WorkflowContext) -> dict:
        """Aggregate worker results."""
        worker_results = context.get_input("worker_results", [])

        if not worker_results:
            logger.warning("No worker results to aggregate")
            return {
                "items": [],
                "success_count": 0,
                "error_count": 0,
                "total_count": 0
            }

        # Process results
        aggregated = []
        error_count = 0

        for result in worker_results:
            if result.get("success"):
                aggregated.append(result.get("result"))
            else:
                error_count += 1
                if not self.allow_partial_failure:
                    raise Exception(f"Task failed: {result.get('error')}")

        logger.info(
            f"Aggregated {len(aggregated)} results "
            f"with {error_count} errors"
        )

        return {
            "items": aggregated,
            "success_count": len(aggregated),
            "error_count": error_count,
            "total_count": len(worker_results),
            "success": error_count == 0
        }

class DynamicParallelExecutor(Executor):
    """
    Complete executor combining dynamic routing, parallel workers,
    and aggregation in a single step.
    """

    def __init__(
        self,
        analyzer: Callable,
        worker_func: Callable,
        max_concurrency: int = 5,
        timeout_per_task: Optional[float] = None
    ):
        self.analyzer = analyzer
        self.worker_func = worker_func
        self.max_concurrency = max_concurrency
        self.timeout_per_task = timeout_per_task
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _process_task(self, task: DynamicTask) -> dict:
        """Process single task with semaphore limiting."""
        async with self.semaphore:
            try:
                logger.debug(f"Starting task: {task.task_id}")
                result = self.worker_func(task.data)

                return {
                    "task_id": task.task_id,
                    "success": True,
                    "result": result
                }

            except Exception as error:
                logger.error(f"Task {task.task_id} failed: {error}")
                return {
                    "task_id": task.task_id,
                    "success": False,
                    "error": str(error)
                }

    async def execute(self, context: WorkflowContext) -> dict:
        """Execute dynamic fan-out/fan-in."""
        input_data = context.get_input("data")

        # Analyze to create tasks
        subtasks = self.analyzer(input_data)
        logger.info(f"Created {len(subtasks)} dynamic tasks")

        # Create task objects
        tasks = [
            DynamicTask(
                task_id=f"task_{i}",
                data=subtask_data,
                executor=None,  # Not used in this executor
                timeout_seconds=self.timeout_per_task
            )
            for i, subtask_data in enumerate(subtasks)
        ]

        # Process tasks in parallel
        task_coroutines = [self._process_task(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines)

        # Aggregate results
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        logger.info(
            f"Dynamic execution completed: "
            f"{len(successful)} success, {len(failed)} failed"
        )

        aggregated_results = [r.get("result") for r in successful]

        return {
            "items": aggregated_results,
            "success_count": len(successful),
            "error_count": len(failed),
            "total_count": len(results),
            "errors": [r.get("error") for r in failed]
        }
```

### Key Considerations

- **Resource Limits**: Cap max_workers to prevent resource exhaustion.
- **Timeout Handling**: Handle stragglers with per-task timeouts.
- **Partial Results**: Decide whether to accept partial results when some tasks fail.
- **Dynamic Count**: Ensure analyzer produces reasonable task counts.

### Complete Workflow Example

```python
async def dynamic_fan_out_fan_in_example():
    # Analyzer: splits data into subtasks based on content
    def analyze_input(data: List[str]) -> List[str]:
        """Split documents into chunks for parallel processing."""
        chunks = []
        chunk_size = 100  # words per chunk
        words = " ".join(data).split()

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)

        return chunks

    # Worker function: process each chunk
    def process_chunk(chunk: str) -> dict:
        """Process a single chunk."""
        return {
            "chunk_length": len(chunk),
            "word_count": len(chunk.split()),
            "summary": chunk[:50] + "..."
        }

    # Create executor
    executor = DynamicParallelExecutor(
        analyzer=analyze_input,
        worker_func=process_chunk,
        max_concurrency=5,
        timeout_per_task=30.0
    )

    # Execute
    context = WorkflowContext()
    context.set_input("data", [
        "Document 1 with lots of text...",
        "Document 2 with more content...",
        "Document 3 with even more..."
    ])

    result = await executor.execute(context)
    logger.info(f"Result: {result}")
```

---

## Summary

These eight advanced design patterns provide robust solutions for common challenges in agent-based systems:

1. **Circuit Breaker**: Fault tolerance and graceful degradation
2. **Load Balancing**: Horizontal scaling and resource distribution
3. **Batch Processing**: Efficient processing of large datasets
4. **Mock Testing**: Deterministic, isolated testing
5. **Time-Travel Debugging**: Comprehensive workflow analysis
6. **Caching**: Cost and latency reduction
7. **Event-Driven**: Reactive, asynchronous processing
8. **Dynamic Routing**: Adaptive, data-dependent parallelization

Each pattern can be combined with others to create sophisticated workflows. Choose patterns based on your specific requirements for reliability, scalability, performance, and maintainability.
