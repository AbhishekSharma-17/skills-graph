# Migrations

Migrate Agno database tables between versions and upgrade from Workflows 1.0 to 2.0.

## Database Migrations

Agno database schemas are stable across versions, but may occasionally need migration when upgrading.

### Using AgentOS Migration Endpoints

AgentOS provides built-in migration endpoints:

```bash
# Upgrade all tables
curl -X POST http://localhost:7777/migrations/upgrade

# Check migration status
curl -X GET http://localhost:7777/migrations/status
```

### Using MigrationManager

```python
from agno.migrations import MigrationManager
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url="postgresql://user:pass@localhost:5432/mydb")
manager = MigrationManager(db=db)

# Upgrade all tables
manager.upgrade()

# Upgrade a specific table
manager.upgrade(table_name="agno_sessions")

# Check status
status = manager.status()
```

### Reverting Migrations

```python
manager.downgrade()  # Revert last migration
manager.downgrade(table_name="agno_sessions")  # Revert specific table
```

### Migrating from Agno v1 to v2

- Run `manager.upgrade()` after updating the agno package
- All existing session data is preserved
- New columns are added automatically
- No manual SQL needed

### Troubleshooting

- If migration fails, check database connection and permissions
- Ensure the database user has ALTER TABLE privileges
- Back up your database before major version upgrades

---

## Workflows 2.0 Migration

Workflows 2.0 is a complete rewrite. Requires manual migration from 1.0.

### Key Differences

| Workflows 1.0 | Workflows 2.0 | Migration Path |
|----------------|---------------|----------------|
| Linear only | Multiple patterns (sequential, parallel, conditional, loop, router) | Restructure flow logic |
| Class-based with `run()` method | Step-based with `Step` objects | Replace class with Step list |
| Manual state passing | Built-in session state | Use `session_state` |
| No streaming | Full streaming support | Add `stream=True` |
| Limited error handling | Built-in retry and error handling | Remove custom retry logic |

### Migration Steps

1. **Replace Workflow class**: Convert from class-based to `Workflow(steps=[...])` format
2. **Convert run methods to Steps**: Each step in the old workflow becomes a `Step(name=..., agent=...)`
3. **Update state management**: Replace manual state passing with `session_state`
4. **Add streaming**: Enable `stream=True` for real-time output
5. **Update imports**: Replace old imports with new ones

### Before (Workflows 1.0)

```python
from agno.workflow import Workflow

class BlogWorkflow(Workflow):
    def run(self, topic: str):
        research = self.researcher.run(topic)
        article = self.writer.run(research.content)
        return article
```

### After (Workflows 2.0)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.workflow import Workflow
from agno.workflow.step import Step

researcher = Agent(
    name="Researcher",
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="Research the given topic thoroughly.",
)
writer = Agent(
    name="Writer",
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="Write a blog post based on the research.",
)

blog_workflow = Workflow(
    description="Research → Write Blog Post",
    steps=[
        Step(name="research", agent=researcher),
        Step(name="writing", agent=writer),
    ],
)

blog_workflow.print_response("Write about AI agents", stream=True)
```

## Key Imports

```python
from agno.migrations import MigrationManager
from agno.workflow import Workflow
from agno.workflow.step import Step
```
