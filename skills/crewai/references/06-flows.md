# CrewAI Flows

> Source: https://docs.crewai.com/en/concepts/flows

## Table of Contents

- [Overview](#overview) | [Why Flows?](#why-flows) | [Basic Flow](#basic-flow)
- [Decorators](#flow-decorators) | [State Management](#flow-state-management) | [Flow with Crews](#flow-with-crews)
- [Broadcasting](#broadcasting-one-to-many) | [Error Handling](#error-handling-in-flows) | [Loop/Retry](#flow-with-loopretry)
- [Running Flows](#running-flows) | [Visualization](#flow-visualization) | [Common Pitfalls](#common-pitfalls)

## Overview

Flows are CrewAI's event-driven orchestration layer for production systems. They wrap Crews with state management, sequencing, error recovery, and conditional routing — without the graph complexity of other frameworks. Flows use decorators (`@start`, `@listen`, `@router`) to define execution paths.

## Why Flows?

| Raw Crews | Flows |
|-----------|-------|
| Simple kickoff | Event-driven lifecycle |
| No state between crews | Shared state object |
| Manual error handling | Built-in retry/recovery |
| Single crew execution | Multi-crew orchestration |
| No routing logic | Conditional branching |

## Basic Flow

```python
from crewai.flow.flow import Flow, listen, start

class SimpleFlow(Flow):
    @start()
    def generate_topic(self):
        return "AI Agent Frameworks in 2026"

    @listen(generate_topic)
    def research_topic(self, topic):
        print(f"Researching: {topic}")
        # Could kickoff a crew here
        return f"Research findings about {topic}"

    @listen(research_topic)
    def write_report(self, findings):
        print(f"Writing report from: {findings[:50]}")
        return f"Final report: {findings}"

# Execute
flow = SimpleFlow()
result = flow.kickoff()
print(result)
```

## Flow Decorators

### @start() — Entry Point

Marks the method that begins the flow. A flow must have exactly one `@start()` method.

```python
class MyFlow(Flow):
    @start()
    def begin(self):
        return "Initial data"
```

### @listen() — Event Listener

Triggers when the specified method completes. Takes the previous method's return value as input.

```python
class MyFlow(Flow):
    @start()
    def step_one(self):
        return "data from step one"

    @listen(step_one)
    def step_two(self, data):
        # data = "data from step one"
        return f"processed: {data}"
```

### @router() — Conditional Branching

Routes execution to different paths based on conditions.

```python
from crewai.flow.flow import Flow, listen, router, start

class ConditionalFlow(Flow):
    @start()
    def classify_input(self):
        # Analyze and classify
        return {"type": "technical", "content": "How do I use CrewAI?"}

    @router(classify_input)
    def route_by_type(self, classification):
        if classification["type"] == "technical":
            return "technical_path"
        elif classification["type"] == "creative":
            return "creative_path"
        else:
            return "general_path"

    @listen("technical_path")
    def handle_technical(self):
        return "Technical response generated"

    @listen("creative_path")
    def handle_creative(self):
        return "Creative response generated"

    @listen("general_path")
    def handle_general(self):
        return "General response generated"
```

## Flow State Management

Flows maintain state across all steps using a structured state object.

```python
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

class ResearchState(BaseModel):
    topic: str = ""
    research_data: str = ""
    draft: str = ""
    final_output: str = ""
    iteration_count: int = 0

class ResearchFlow(Flow[ResearchState]):
    @start()
    def initialize(self):
        self.state.topic = "CrewAI Best Practices"
        self.state.iteration_count = 0

    @listen(initialize)
    def research(self):
        # Access and modify state
        self.state.research_data = f"Research on {self.state.topic}"
        self.state.iteration_count += 1

    @listen(research)
    def write_draft(self):
        self.state.draft = f"Draft based on: {self.state.research_data}"

    @listen(write_draft)
    def finalize(self):
        self.state.final_output = f"Final: {self.state.draft}"
        return self.state.final_output

flow = ResearchFlow()
result = flow.kickoff()
print(flow.state.iteration_count)  # 1
```

## Flow with Crews

The primary use case — orchestrating multiple crews within a flow:

```python
from crewai import Agent, Task, Crew, Process
from crewai.flow.flow import Flow, listen, start

class ContentPipeline(Flow):
    @start()
    def research_phase(self):
        researcher = Agent(
            role="Researcher",
            goal="Find information about {topic}",
            backstory="Expert researcher.",
        )
        task = Task(
            description="Research {topic} thoroughly.",
            expected_output="Comprehensive research notes.",
            agent=researcher,
        )
        crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential)
        result = crew.kickoff(inputs={"topic": self.state.get("topic", "AI")})
        return result.raw

    @listen(research_phase)
    def writing_phase(self, research):
        writer = Agent(
            role="Writer",
            goal="Write engaging content",
            backstory="Professional writer.",
        )
        task = Task(
            description=f"Write a blog post using this research:\n{research}",
            expected_output="800-word blog post in markdown.",
            agent=writer,
        )
        crew = Crew(agents=[writer], tasks=[task], process=Process.sequential)
        result = crew.kickoff()
        return result.raw

    @listen(writing_phase)
    def review_phase(self, draft):
        editor = Agent(
            role="Editor",
            goal="Review and polish content",
            backstory="Senior editor with high standards.",
        )
        task = Task(
            description=f"Review and improve this draft:\n{draft}",
            expected_output="Polished final article.",
            agent=editor,
        )
        crew = Crew(agents=[editor], tasks=[task], process=Process.sequential)
        result = crew.kickoff()
        return result.raw

flow = ContentPipeline()
result = flow.kickoff()
```

## Broadcasting (One-to-Many)

Multiple listeners on the same event execute in parallel:

```python
class MeetingFlow(Flow):
    @start()
    def process_meeting(self):
        return "Meeting notes: discussed Q4 goals..."

    @listen(process_meeting)
    def update_trello(self, notes):
        # Runs in parallel with other listeners
        return "Trello updated"

    @listen(process_meeting)
    def send_slack(self, notes):
        # Runs in parallel
        return "Slack message sent"

    @listen(process_meeting)
    def save_to_db(self, notes):
        # Runs in parallel
        return "Saved to database"
```

## Error Handling in Flows

```python
class ResilientFlow(Flow):
    @start()
    def fetch_data(self):
        try:
            return external_api_call()
        except Exception as e:
            self.state["error"] = str(e)
            return None

    @router(fetch_data)
    def check_success(self, data):
        if data is None:
            return "error_path"
        return "success_path"

    @listen("success_path")
    def process_data(self):
        return "Processing successful data"

    @listen("error_path")
    def handle_error(self):
        return f"Error occurred: {self.state.get('error')}"
```

## Flow with Loop/Retry

```python
class IterativeFlow(Flow[ResearchState]):
    @start()
    def initial_draft(self):
        self.state.draft = "First draft..."
        self.state.iteration_count = 0

    @listen(initial_draft)
    def review_and_improve(self):
        self.state.iteration_count += 1
        # Simulate review
        quality_score = evaluate(self.state.draft)
        self.state.draft = improve(self.state.draft)
        return quality_score

    @router(review_and_improve)
    def check_quality(self, score):
        if score >= 0.9 or self.state.iteration_count >= 3:
            return "finalize"
        return "retry"

    @listen("retry")
    def retry_improvement(self):
        return self.review_and_improve()

    @listen("finalize")
    def output_final(self):
        return self.state.draft
```

## Running Flows

```python
# Synchronous
flow = MyFlow()
result = flow.kickoff()

# With initial state
flow = MyFlow()
flow.state["topic"] = "AI Agents"
result = flow.kickoff()

# Async
import asyncio

async def main():
    flow = MyFlow()
    result = await flow.kickoff_async()
    return result

asyncio.run(main())
```

## Flow Visualization

```python
flow = MyFlow()
flow.plot()  # Generates a visual diagram of the flow
```

## Common Pitfalls

1. **Multiple @start decorators** — Only one entry point per flow
2. **Circular listeners** — Can create infinite loops; use @router to break
3. **State mutation without Pydantic** — Use typed state model for safety
4. **Not using flows for production** — Raw crews lack error recovery
5. **Heavy logic in @router** — Keep routing logic simple; do work in @listen methods
