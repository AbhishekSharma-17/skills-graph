# Custom Logging

Configure custom loggers and formatters for your Agno setup.

## configure_agno_logging()

Replace Agno's default loggers with your own:

```python
from agno.utils.log import configure_agno_logging
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `custom_default_logger` | `logging.Logger` | Default logger for all Agno output |
| `custom_agent_logger` | `logging.Logger` | Logger for Agent runs |
| `custom_team_logger` | `logging.Logger` | Logger for Team runs |
| `custom_workflow_logger` | `logging.Logger` | Logger for Workflow runs |

## Basic Custom Logger

```python
import logging
from agno.agent import Agent
from agno.utils.log import configure_agno_logging, log_info

custom_logger = logging.getLogger("custom_logger")
handler = logging.StreamHandler()
formatter = logging.Formatter("[CUSTOM_LOGGER] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
custom_logger.addHandler(handler)
custom_logger.setLevel(logging.INFO)
custom_logger.propagate = False

# Configure Agno to use the custom logger
configure_agno_logging(custom_default_logger=custom_logger)

# All logging now uses the custom logger
log_info("This is using our custom logger!")

agent = Agent()
agent.print_response("What is 2+2?")
```

## Logging to a File

```python
import logging
from pathlib import Path
from agno.utils.log import configure_agno_logging, log_info

custom_logger = logging.getLogger("file_logger")

log_file_path = Path("tmp/log.txt")
log_file_path.parent.mkdir(parents=True, exist_ok=True)

handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
custom_logger.addHandler(handler)
custom_logger.setLevel(logging.INFO)
custom_logger.propagate = False

configure_agno_logging(custom_default_logger=custom_logger)

log_info("This is using our file logger!")
```

## Multiple Loggers (Per Component)

Assign different loggers for Agents, Teams, and Workflows:

```python
import logging
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.workflow.step import Step
from agno.utils.log import configure_agno_logging

custom_agent_logger = logging.getLogger("agent_logger")
custom_team_logger = logging.getLogger("team_logger")
custom_workflow_logger = logging.getLogger("workflow_logger")

for logger in [custom_agent_logger, custom_team_logger, custom_workflow_logger]:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# Workflow logs at DEBUG level when debug_mode is enabled
custom_workflow_logger.setLevel(logging.DEBUG)

configure_agno_logging(
    custom_default_logger=custom_agent_logger,
    custom_agent_logger=custom_agent_logger,
    custom_team_logger=custom_team_logger,
    custom_workflow_logger=custom_workflow_logger,
)

agent = Agent()
team = Team(members=[agent])
workflow = Workflow(debug_mode=True, steps=[Step(name="step1", agent=agent)])

agent.print_response("What is 2+2?")       # Uses custom_agent_logger
team.print_response("Tell me a short joke")  # Uses custom_team_logger
workflow.print_response("Tell me a fun fact") # Uses custom_workflow_logger
```

## Named Loggers (Convention-Based)

Agno automatically recognizes these logger names — no `configure_agno_logging()` call needed:

| Logger Name | Used For |
|-------------|----------|
| `agno` | All Agent logs |
| `agno-team` | All Team logs |
| `agno-workflow` | All Workflow logs |

```python
import logging
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.workflow.step import Step

# Set up named loggers BEFORE creating agents/teams/workflows
logger_configs = [
    ("agno", "agent.log"),
    ("agno-team", "team.log"),
    ("agno-workflow", "workflow.log"),
]

for logger_name, log_file in logger_configs:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

# Agno automatically detects and uses these loggers
agent = Agent()
agent.print_response("Hello from agent!")  # Logs to agent.log

team = Team(members=[agent])
team.print_response("Hello from team!")    # Logs to team.log

workflow = Workflow(debug_mode=True, steps=[Step(name="step1", agent=agent)])
workflow.run("Hello from workflow!")        # Logs to workflow.log
```

## Key Imports

```python
from agno.utils.log import configure_agno_logging, log_info, log_debug
```
