# CrewAI Processes

> Source: https://docs.crewai.com/en/concepts/processes

## Overview

Processes define how tasks are assigned and executed within a CrewAI crew. They determine the workflow strategy — whether tasks run in a fixed order or are dynamically delegated by a manager.

## Process Types

| Process | Use Case | Task Assignment | Manager Required |
|---------|----------|-----------------|-----------------|
| Sequential | Predictable pipelines | Fixed order, explicit agent | No |
| Hierarchical | Dynamic delegation | Manager assigns at runtime | Yes |

## Sequential Process

Tasks execute in the order they appear in the tasks list. Each task's output automatically becomes context for subsequent tasks.

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[
        research_task,    # Runs first
        analysis_task,    # Runs second (gets research output)
        writing_task,     # Runs third (gets analysis output)
    ],
    process=Process.sequential,
    verbose=True,
)
```

### Sequential Rules

1. Every task MUST have an `agent` assigned
2. Tasks execute in list order (index 0, 1, 2, ...)
3. Output from task N is available as context to task N+1
4. Explicit `context` parameter overrides automatic context passing
5. Async tasks within sequential still respect the overall order

### Sequential with Explicit Context

```python
# Override automatic context chaining
task_a = Task(description="...", expected_output="...", agent=agent1)
task_b = Task(description="...", expected_output="...", agent=agent2)
task_c = Task(
    description="...",
    expected_output="...",
    agent=agent3,
    context=[task_a],  # Only gets task_a output, NOT task_b
)

crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task_a, task_b, task_c],
    process=Process.sequential,
)
```

## Hierarchical Process

A manager agent dynamically assigns tasks to team members based on their roles, goals, and capabilities.

```python
from crewai import Crew, Process, LLM

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.hierarchical,
    manager_llm=LLM(model="openai/gpt-4o"),  # Manager uses this LLM
    verbose=True,
)
```

### Hierarchical Rules

1. Tasks do NOT need explicit `agent` assignment — manager decides
2. Must specify either `manager_llm` or `manager_agent`
3. Manager creates and delegates sub-tasks automatically
4. Manager validates outputs before moving forward
5. Manager can re-assign if an agent produces poor results

### Custom Manager Agent

```python
from crewai import Agent, Crew, Process

custom_manager = Agent(
    role="Engineering Manager",
    goal="Coordinate the team to deliver production-ready code",
    backstory=(
        "You are an experienced engineering manager who understands "
        "each team member's strengths and delegates accordingly."
    ),
    allow_delegation=True,
    verbose=True,
)

crew = Crew(
    agents=[backend_dev, frontend_dev, qa_engineer],
    tasks=[api_task, ui_task, testing_task],
    process=Process.hierarchical,
    manager_agent=custom_manager,
    verbose=True,
)
```

### Hierarchical with Validation

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.hierarchical,
    manager_llm=LLM(model="openai/gpt-4o"),
    # Manager will validate task outputs before proceeding
    # If output is insufficient, manager can request revision
)
```

## Planning Agent

Enable an automatic planning phase before execution. The planning agent analyzes all tasks and creates a step-by-step plan.

```python
from crewai import Crew, Process, LLM

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,
    planning=True,
    planning_llm=LLM(model="openai/gpt-4o"),
    verbose=True,
)
```

### How Planning Works

1. Before execution, the planning agent receives all task descriptions
2. It creates a detailed step-by-step plan for each task
3. Plans are injected as additional context for each agent
4. Agents follow the plan while still having autonomy to adapt

### Planning with Custom Instructions

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    planning=True,
    planning_llm=LLM(model="openai/gpt-4o", temperature=0.2),
    verbose=True,
)
```

## Choosing the Right Process

| Scenario | Recommended Process |
|----------|-------------------|
| Fixed pipeline (A → B → C) | Sequential |
| Tasks with clear dependencies | Sequential |
| Dynamic task allocation needed | Hierarchical |
| Team of >5 agents | Hierarchical |
| Need quality validation between steps | Hierarchical |
| Simple 2-3 agent workflows | Sequential |
| Complex projects with unclear routing | Hierarchical + Planning |

## Process Comparison Example

### Same Task, Different Processes

```python
# Sequential: Fixed assignment
crew_seq = Crew(
    agents=[researcher, writer],
    tasks=[
        Task(description="Research AI trends", expected_output="...", agent=researcher),
        Task(description="Write blog post", expected_output="...", agent=writer),
    ],
    process=Process.sequential,
)

# Hierarchical: Manager decides who does what
crew_hier = Crew(
    agents=[researcher, writer],
    tasks=[
        Task(description="Research AI trends", expected_output="..."),
        Task(description="Write blog post", expected_output="..."),
    ],
    process=Process.hierarchical,
    manager_llm=LLM(model="openai/gpt-4o"),
)
```

## Advanced: Combining Process Types with Flows

```python
from crewai.flow.flow import Flow, listen, start

class ResearchPipeline(Flow):
    @start()
    def run_research_crew(self):
        # Sequential for research phase
        research_crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
        )
        return research_crew.kickoff(inputs=self.state)

    @listen(run_research_crew)
    def run_writing_crew(self, research_output):
        # Hierarchical for writing phase with editor oversight
        writing_crew = Crew(
            agents=[writer, editor, reviewer],
            tasks=[writing_task, editing_task, review_task],
            process=Process.hierarchical,
            manager_llm=LLM(model="openai/gpt-4o"),
        )
        return writing_crew.kickoff(inputs={"research": research_output.raw})
```

## Common Pitfalls

1. **Hierarchical without good model** — The manager needs a capable LLM (GPT-4o or Claude Sonnet+)
2. **Too many tasks in hierarchical** — Manager gets confused with >10 tasks; split into sub-crews
3. **Sequential with unrelated tasks** — If tasks don't chain, consider parallel or hierarchical
4. **Planning without verbose** — Can't debug if you can't see the generated plan
5. **Missing agent in sequential** — Every sequential task needs an explicit agent assignment
