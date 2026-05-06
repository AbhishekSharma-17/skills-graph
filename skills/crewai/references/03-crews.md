# CrewAI Crews

> Source: https://docs.crewai.com/en/concepts/crews

## Overview

A Crew is a collaborative group of agents working together to achieve a set of tasks. It defines the strategy for task execution, agent collaboration, and the overall workflow. Crews are where agents and tasks come together.

## Crew Definition

```python
from crewai import Agent, Task, Crew, Process

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,
    verbose=True,
)
```

## Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agents` | list[Agent] | required | Agents in the crew |
| `tasks` | list[Task] | required | Tasks to execute |
| `process` | Process | sequential | Execution strategy |
| `verbose` | bool | False | Print execution details |
| `memory` | bool | False | Enable crew-level memory |
| `cache` | bool | True | Enable tool result caching |
| `max_rpm` | int | None | Global rate limit |
| `language` | str | "en" | Language for internal prompts |
| `full_output` | bool | False | Return full output with all task results |
| `output_log_file` | str/bool | None | Log file path |
| `manager_llm` | LLM/str | None | LLM for hierarchical manager |
| `manager_agent` | Agent | None | Custom manager agent |
| `planning` | bool | False | Enable planning agent |
| `planning_llm` | LLM/str | None | LLM for planning agent |
| `embedder` | dict | None | Embedding config for memory |
| `step_callback` | callable | None | Called after each step |
| `task_callback` | callable | None | Called after each task |

## Kickoff Methods

```python
# Standard synchronous execution
result = crew.kickoff()

# With input variables
result = crew.kickoff(inputs={"topic": "AI agents", "year": "2026"})

# Execute for multiple inputs (batch)
results = crew.kickoff_for_each(
    inputs=[
        {"topic": "CrewAI"},
        {"topic": "LangGraph"},
        {"topic": "AutoGen"},
    ]
)

# Async execution
import asyncio

async def main():
    result = await crew.kickoff_async(inputs={"topic": "AI agents"})
    return result

result = asyncio.run(main())

# Async batch execution
async def batch():
    results = await crew.kickoff_for_each_async(
        inputs=[{"topic": "CrewAI"}, {"topic": "LangGraph"}]
    )
    return results
```

## CrewOutput Object

```python
result = crew.kickoff()

# Access properties
result.raw          # str: Final output as string
result.json_dict    # dict: If last task has output_json
result.pydantic     # Model: If last task has output_pydantic
result.tasks_output # list[TaskOutput]: All task outputs
result.token_usage  # dict: Token consumption stats

# Dictionary-style access (if structured output)
result["field_name"]

# Token usage details
print(f"Total tokens: {result.token_usage}")
```

## Crew with Memory

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    memory=True,
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
    verbose=True,
)
```

## Crew with Planning

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    planning=True,  # Enables a planning agent that creates step-by-step plan
    planning_llm=LLM(model="openai/gpt-4o"),
    verbose=True,
)
```

## Crew Callbacks

```python
def on_step(step_output):
    print(f"Step completed by agent")

def on_task(task_output):
    print(f"Task done: {task_output.description[:50]}")
    print(f"Output: {task_output.raw[:100]}")

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    step_callback=on_step,
    task_callback=on_task,
)
```

## Crew with Output Logging

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    output_log_file="logs/crew_execution.log",
    verbose=True,
)
```

## @CrewBase Decorator (CLI Projects)

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyResearchCrew:
    """Research crew for comprehensive topic analysis."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config["researcher"])

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"])

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def writing_task(self) -> Task:
        return Task(config=self.tasks_config["writing_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Auto-collected from @agent methods
            tasks=self.tasks,    # Auto-collected from @task methods
            process=Process.sequential,
            verbose=True,
        )
```

## Running @CrewBase Crew

```python
# In main.py
from my_project.crew import MyResearchCrew

def run():
    crew = MyResearchCrew()
    result = crew.crew().kickoff(inputs={"topic": "AI Agents"})
    print(result.raw)

if __name__ == "__main__":
    run()
```

## Crew with Custom Manager (Hierarchical)

```python
from crewai import Agent, Crew, Process, LLM

manager = Agent(
    role="Project Manager",
    goal="Efficiently coordinate the team to deliver the best output",
    backstory="Veteran PM with expertise in AI project delivery.",
    allow_delegation=True,
)

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.hierarchical,
    manager_agent=manager,
    verbose=True,
)
```

## Crew with Rate Limiting

```python
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    max_rpm=30,  # Global: max 30 requests/minute across all agents
    verbose=True,
)
```

## Crew Execution with Error Handling

```python
from crewai import Crew

crew = Crew(agents=[...], tasks=[...], process=Process.sequential)

try:
    result = crew.kickoff(inputs={"topic": "AI"})
    if result.raw:
        print("Success:", result.raw[:200])
    else:
        print("Empty result")
except Exception as e:
    print(f"Crew execution failed: {e}")
```

## Testing Crews

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
)

# Train the crew (evaluates and improves over iterations)
crew.train(n_iterations=3, filename="training_data.pkl")

# Test the crew
crew.test(n_iterations=2, openai_model_name="gpt-4o")

# Replay a specific task
crew.replay(task_id="task_123")
```

## Common Pitfalls

1. **Mismatched agent-task assignment** — Ensure each task's agent is in the crew's agents list
2. **Sequential without explicit order** — Tasks execute in list order; arrange carefully
3. **Memory without embedder** — Specify embedder config when using memory=True
4. **Rate limits in batch** — kickoff_for_each can hit API limits; use max_rpm
5. **Missing inputs** — If tasks use {variables}, pass them in kickoff(inputs={...})
