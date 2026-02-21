# Integrations

Third-party platform integrations for Agno agents.

## Available Integrations

| Integration | Description | Package |
|-------------|-------------|---------|
| **Discord** | Host agents as Discord bots | `agno` (built-in) |
| **Memori** | Open-source memory layer for AI | `memori`, `sqlalchemy` |

---

## Discord Bot

Host Agno agents as Discord bots with automatic thread creation and media support.

### Setup Steps
1. Create a Discord Application at https://discord.com/developers
2. Create a Bot and get the token
3. Enable Message Content Intent in the bot settings
4. Invite bot to server with appropriate permissions
5. Set environment variable: `export DISCORD_BOT_TOKEN=<token>`

### DiscordClient Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent` | `Agent` | The Agno agent to power the bot |
| `team` | `Team` | Or use a Team instead of a single agent |

### Event Handling
- `on_ready`: Bot connected and ready
- `on_message`: New message received (auto-creates threads for channel messages)

### Supported Media Types
Images (PNG, JPG, GIF, WebP), Audio (MP3, WAV, OGG), Video (MP4, WebM)

### Example
```python
import os
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.integrations.discord import DiscordClient

agent = Agent(
    name="Discord Bot",
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="You are a helpful Discord assistant.",
    markdown=True,
)

client = DiscordClient(agent=agent)
client.run(os.getenv("DISCORD_BOT_TOKEN"))
```

### Features
- **Automatic Thread Creation**: Channel messages spawn threads; DMs are direct
- **Media Support**: Process images, audio, and video attachments
- **Message Formatting**: Auto-splits long messages (2000 char limit)

---

## Memori

Open-source memory layer that captures conversations, extracts facts, and makes them searchable.

### Prerequisites
```bash
uv pip install -U memori sqlalchemy python-dotenv
```

### Example
```python
import os
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from memori import Memori

load_dotenv()

engine = create_engine("sqlite:///memory.db")
Session = sessionmaker(bind=engine)
session = Session()

memori = Memori(
    api_key=os.getenv("OPENAI_API_KEY"),
    session=session,
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[memori.as_tool()],
    instructions="Use Memori to store and recall information.",
)

agent.print_response("Remember that I prefer dark mode.")
agent.print_response("What are my preferences?")
```

### Key Features
- Automatic conversation capture and fact extraction
- Entity-based memory search across sessions
- Multiple database backends via SQLAlchemy
- Process-level and session-level memory isolation

### Setup
1. Install: `uv pip install -U memori sqlalchemy`
2. Configure SQLAlchemy engine (SQLite, PostgreSQL, etc.)
3. Create Memori instance with API key and session
4. Add as tool to your agent

## Key Imports

```python
from agno.integrations.discord import DiscordClient
# Memori is a third-party package
from memori import Memori
```
