# Deploy

Deploy AgentOS to your cloud platform. 3-step process: Template → Apps → Interfaces.

## Templates

Production-ready codebases with AgentOS, PostgreSQL, and deployment scripts.

### Blank Canvas

| Template | Best For | Time |
|----------|----------|------|
| Docker | Local dev, testing, self-hosting | ~5 min |
| Railway | Quick production, MVPs | ~10 min |
| AWS (ECS) | Production at scale, enterprise | ~15 min |

### Pre-built Solutions

| Template | Description |
|----------|-------------|
| Dash | Self-learning data agent |
| Scout | Self-managing context agent |
| Gcode | Lightweight coding agent |

### Docker Deployment

```bash
git clone https://github.com/agno-agi/agno-docker.git
cd agno-docker
docker compose up -d
```

### Railway Deployment

```bash
# Uses Railway CLI
railway login
railway init
railway up
```

### AWS ECS Deployment

```bash
git clone https://github.com/agno-agi/agno-aws.git
cd agno-aws
# Follow AWS setup guide
```

## Apps

Pre-built agents, teams, and workflows to add to your deployment.

### Agent Apps

| App | Description |
|-----|-------------|
| Text-to-SQL | Self-learning SQL agent, improves with validated queries |
| Research Agent | Web research with citations and source credibility |
| Knowledge Agent | Answer questions from company docs/wikis |
| Document Summarizer | Structured summaries with key points, entities, actions |
| Invoice Extractor | Vision-based extraction from PDFs/images |
| Customer Support | Ticket resolution with knowledge retrieval + escalation |
| Inbox Agent | Email triage, draft replies, flag urgent items |
| Contract Review | Legal document analysis and risk flagging |
| Code Review | PR review with context-aware suggestions |
| Social Media Analyst | Sentiment analysis with brand health scoring |

### Team Apps

| App | Description |
|-----|-------------|
| Content Production Team | Writer + Editor + SEO Optimizer + Publisher |

### Workflow Apps

| App | Description |
|-----|-------------|
| Meeting to Tasks | Extract action items from recordings → Linear issues |
| Lead Enrichment | Enrich CRM contacts with LinkedIn + company data |
| Sales Call Analyzer | Transcribe calls, extract insights, score conversations |
| Competitor Tracker | Monitor competitor content, surface changes |

## Interfaces

Connect agents to platforms users already use.

### Messaging Platforms

| Interface | Description |
|-----------|-------------|
| Slack | Deploy agents as Slack apps responding to messages/commands |
| Discord | Run agents as Discord bots for support/moderation |
| WhatsApp | Connect agents to WhatsApp Business for customer interactions |
| Telegram | Run agents as Telegram bots |

### Protocols

| Interface | Description |
|-----------|-------------|
| MCP | Expose agents via Model Context Protocol for any MCP client |
| AG-UI | Connect agents to frontends using the AG-UI protocol |

## Key Imports

```python
from agno.os import AgentOS
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
```

## Quick Start Example

```python
from agno.os import AgentOS
from agno.agent import Agent

# Initialize AgentOS
os = AgentOS()

# Create an agent
agent = Agent(
    name="Sales Agent",
    description="Handles customer inquiries",
    model="gpt-4"
)

# Deploy to platform
os.add_agent(agent)
os.deploy(platform="railway")
```

## Cross-References

→ AgentOS: `references/agentos.md`
→ Integrations: `references/integrations.md`
