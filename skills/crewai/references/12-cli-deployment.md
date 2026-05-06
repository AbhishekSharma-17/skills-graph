# CrewAI CLI & Deployment

> Source: https://docs.crewai.com/en/concepts/cli

## Table of Contents

- [Overview](#overview) | [CLI Commands](#cli-commands) | [Creating a New Project](#creating-a-new-project)
- [Project Configuration](#project-configuration) | [Running Locally](#running-locally)
- [Training](#training) | [Testing](#testing) | [Memory Management](#memory-management)
- [Deployment to AMP](#deployment-to-crewai-amp) | [Self-Hosted](#self-hosted-deployment)
- [Production Checklist](#production-checklist) | [Monitoring](#monitoring--observability) | [Common Pitfalls](#common-pitfalls)

## Overview

CrewAI provides a CLI tool for project scaffolding, running crews, training, testing, and deploying to the CrewAI AMP (Agent Management Platform). The CLI streamlines the development lifecycle from local development to production.

## Installation

```bash
pip install crewai
# CLI is included with the crewai package
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `crewai create crew <name>` | Scaffold a new crew project |
| `crewai create flow <name>` | Scaffold a new flow project |
| `crewai run` | Run the crew/flow locally |
| `crewai train` | Train the crew (evaluate & improve) |
| `crewai test` | Test the crew with evaluation |
| `crewai replay` | Replay a specific task |
| `crewai log-tasks-outputs` | View task outputs |
| `crewai reset-memories` | Reset crew memories |
| `crewai deploy` | Deploy to CrewAI AMP |
| `crewai version` | Show CLI version |
| `crewai install` | Install project dependencies |

## Creating a New Project

### Crew Project

```bash
crewai create crew my-research-project
```

This generates:

```
my-research-project/
├── src/
│   └── my_research_project/
│       ├── __init__.py
│       ├── main.py
│       ├── crew.py
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py
├── tests/
│   └── __init__.py
├── pyproject.toml
├── .env
├── .gitignore
└── README.md
```

### Flow Project

```bash
crewai create flow my-automation-flow
```

Generates a flow-based project with state management and event-driven structure.

## Project Configuration

### agents.yaml

```yaml
researcher:
  role: "Senior Research Analyst"
  goal: "Uncover cutting-edge developments in {topic}"
  backstory: >
    You're a seasoned researcher with a knack for uncovering
    the latest developments in {topic}. Known for your ability
    to find the most relevant information and present it clearly.
  tools:
    - SerperDevTool
  verbose: true

writer:
  role: "Tech Content Strategist"
  goal: "Craft compelling content on {topic}"
  backstory: >
    You're a renowned Content Strategist, known for your
    insightful and engaging articles about {topic}.
  verbose: true
```

### tasks.yaml

```yaml
research_task:
  description: >
    Conduct a thorough research about {topic}.
    Make sure you find any interesting and relevant information
    given the current year is 2026.
  expected_output: >
    A list with 10 bullet points of the most relevant
    information about {topic}.
  agent: researcher

reporting_task:
  description: >
    Review the research findings and create a detailed report
    about {topic}. Include all relevant information.
  expected_output: >
    A detailed report formatted as markdown with headers
    and bullet points about {topic}.
  agent: writer
  output_file: report.md
```

### crew.py

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class MyResearchProjectCrew:
    """My Research Project crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=[SerperDevTool()],
        )

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"])

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def reporting_task(self) -> Task:
        return Task(config=self.tasks_config["reporting_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

### main.py

```python
#!/usr/bin/env python
from my_research_project.crew import MyResearchProjectCrew

def run():
    inputs = {"topic": "AI Agents"}
    MyResearchProjectCrew().crew().kickoff(inputs=inputs)

def train():
    inputs = {"topic": "AI Agents"}
    MyResearchProjectCrew().crew().train(
        n_iterations=3,
        filename="training_output.pkl",
        inputs=inputs,
    )

def test():
    inputs = {"topic": "AI Agents"}
    MyResearchProjectCrew().crew().test(
        n_iterations=2,
        openai_model_name="gpt-4o",
        inputs=inputs,
    )

if __name__ == "__main__":
    run()
```

## Running Locally

```bash
cd my-research-project

# Install dependencies
crewai install

# Set environment variables
export OPENAI_API_KEY="sk-..."
export SERPER_API_KEY="..."

# Run the crew
crewai run
```

## Training

Train crews to improve agent performance over iterations:

```bash
crewai train -n 3
```

Training runs the crew multiple times, evaluating and storing improvements.

## Testing

Test crew performance with automated evaluation:

```bash
crewai test -n 2
```

## Memory Management

```bash
# Reset all memory types
crewai reset-memories --all

# Reset specific types
crewai reset-memories --short    # Short-term memory
crewai reset-memories --long     # Long-term memory
crewai reset-memories --entity   # Entity memory

# View task outputs from previous runs
crewai log-tasks-outputs
```

## Replay

Replay a specific task from a previous execution:

```bash
crewai replay -t <task_id>
```

## Deployment to CrewAI AMP

### Authentication

```bash
# Login to CrewAI platform
crewai login
```

### Deploy

```bash
# Deploy from project root
crewai deploy

# This will:
# 1. Read your project configuration
# 2. Prompt for environment variables confirmation
# 3. Package and upload your crew/flow
# 4. Deploy to CrewAI AMP platform
```

### Deployment Options

- **Cloud** — Managed by CrewAI (default)
- **On-premise** — Self-hosted for enterprise

## Self-Hosted Deployment

For production without CrewAI AMP:

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY .env .

RUN pip install crewai 'crewai[tools]'
RUN pip install -e .

CMD ["python", "-m", "my_project.main"]
```

### FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from my_project.crew import MyResearchProjectCrew

app = FastAPI()

class CrewInput(BaseModel):
    topic: str

class CrewResult(BaseModel):
    output: str
    token_usage: dict

@app.post("/run", response_model=CrewResult)
async def run_crew(input: CrewInput, background_tasks: BackgroundTasks):
    crew = MyResearchProjectCrew().crew()
    result = crew.kickoff(inputs={"topic": input.topic})
    return CrewResult(
        output=result.raw,
        token_usage=result.token_usage,
    )
```

### Background Execution with Celery

```python
from celery import Celery
from my_project.crew import MyResearchProjectCrew

celery_app = Celery("tasks", broker="redis://localhost:6379")

@celery_app.task
def run_crew_async(topic: str):
    crew = MyResearchProjectCrew().crew()
    result = crew.kickoff(inputs={"topic": topic})
    return {"output": result.raw, "tokens": result.token_usage}
```

## Production Checklist

| Check | Why |
|-------|-----|
| Environment variables secured | No hardcoded keys |
| Rate limits configured | Prevent API cost overruns |
| Error handling in place | Graceful failure recovery |
| Memory persistence configured | State survives restarts |
| Logging enabled | Debug production issues |
| Timeout settings | Prevent hung executions |
| Health checks | Monitor crew health |
| Output validation | Guardrails on critical tasks |

## Monitoring & Observability

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

crew = Crew(
    agents=[...],
    tasks=[...],
    verbose=True,
    output_log_file="logs/execution.log",
)
```

### Integration with Observability Tools

- **Langfuse** — Trace agent execution
- **Arize Phoenix** — Monitor performance
- **OpenTelemetry** — Distributed tracing

## Common Pitfalls

1. **Forgetting .env in deployment** — Environment variables must be set on the target
2. **Not pinning dependencies** — Use exact versions in pyproject.toml for production
3. **Synchronous in async context** — Use kickoff_async() in FastAPI/async servers
4. **No rate limiting in production** — Set max_rpm to prevent cost overruns
5. **Missing health checks** — Monitor long-running crews for hangs
6. **Deploying without testing** — Always `crewai test` before deploy
