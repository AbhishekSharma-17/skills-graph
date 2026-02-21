# M365 Integration — Copilot Agents & Microsoft 365

## Overview

The Microsoft Agent Framework integrates seamlessly with Microsoft 365, enabling two complementary approaches to building AI agents:

1. **Declarative Agents**: Use Microsoft Copilot's built-in orchestration and security
2. **Custom Engine Agents**: Bring your own Agent Framework orchestration to M365

Both approaches can access Microsoft 365 resources (Teams, Outlook, SharePoint, OneDrive) via the Microsoft Graph API.

---

## Declarative Agents vs Custom Engine Agents

### Declarative Agents

Declarative agents leverage Copilot's existing orchestration, security, and model infrastructure.

**Characteristics:**
- Uses Copilot's orchestrator and model routing
- Automatic adherence to M365 security, compliance, and responsible AI policies
- Faster to deploy, less custom code required
- Limited to Copilot's capabilities and models
- Ideal for productivity scenarios

**Architecture:**
```
User Input
    ↓
M365 Copilot (built-in orchestrator)
    ↓
Your Agent Logic (plugins/actions)
    ↓
Microsoft Graph API
    ↓
M365 Resources (Teams, Outlook, etc.)
```

**Definition Format (YAML):**

```yaml
$schema: https://developer.microsoft.com/json-schemas/copilot/agent/agent-schema.json
version: 1.0
name: "DataAnalysisAgent"
description: "Agent for analyzing business data within Teams"
instructions: |
  You are a data analysis assistant. Help users analyze business metrics
  and generate insights from company data. Always cite data sources.
  Never share sensitive information outside the organization.

resources:
  - type: connector
    name: AzureDataConnector
    config:
      endpoint: "https://data.contoso.com/api"
      auth: oauth2

  - type: knowledge
    name: CompanyPolicies
    source: "https://sharepoint.contoso.com/policies"

actions:
  - name: analyzeMetrics
    description: "Analyze key business metrics"
    inputSchema:
      type: object
      properties:
        metric: { type: string }
        timeRange: { type: string }
    implementation:
      type: api
      endpoint: "https://api.contoso.com/analyze"

triggers:
  - type: copilot-chat
    location: teams
  - type: message-extension
```

### Custom Engine Agents

Custom engine agents use the Agent Framework as the orchestrator, deployed to M365.

**Characteristics:**
- Full control over agent behavior and reasoning
- Choose any LLM (OpenAI, Anthropic, open source, etc.)
- Responsible for compliance and security implementation
- More code required, more flexibility
- Ideal for specialized, domain-specific agents

**Architecture:**
```
User Input
    ↓
Agent Framework (your orchestrator)
    ↓
Your LLM Choice
    ↓
Custom Logic & Middleware
    ↓
Microsoft Graph API
    ↓
M365 Resources
```

**Implementation:**

```python
from agent_framework import ChatAgent, AgentExecutor
from agent_framework.safety import ContentSafetyMiddleware
from azure.identity import DefaultAzureCredential
from msgraph.core import GraphClient

# Initialize Microsoft Graph client for M365 access
auth = DefaultAzureCredential()
graph_client = GraphClient(credential=auth)

# Define agent with M365 capabilities
m365_agent = ChatAgent(
    name="M365DataAgent",
    chat_client=azure_openai_client,
    description="Analyze and share M365 data securely",
    instructions="""You are a Microsoft 365 data agent. You can:
    - Access calendar and meeting information
    - Read emails and files
    - Create reports from Teams conversations
    - Always maintain organizational security and privacy
    - Ask permission before sharing sensitive data
    """,
    middleware=[
        ContentSafetyMiddleware(client=safety_client),
        # Add custom M365 security middleware
    ]
)

# Register tools for M365 interaction
from agent_framework import Tool

@Tool.register(m365_agent)
async def get_upcoming_meetings(days: int = 7):
    """Retrieve upcoming meetings from calendar."""
    endpoint = "/me/calendarview"
    params = {
        "startDateTime": datetime.utcnow().isoformat(),
        "endDateTime": (datetime.utcnow() + timedelta(days=days)).isoformat(),
        "$select": "subject,start,end,organizer"
    }

    response = await graph_client.get(endpoint, params=params)
    return response.json()["value"]

@Tool.register(m365_agent)
async def get_recent_files(folder: str = "root", limit: int = 10):
    """Retrieve recent files from OneDrive."""
    endpoint = f"/me/drive/root:{folder}:/children"
    params = {"$top": limit, "$orderBy": "lastModifiedDateTime desc"}

    response = await graph_client.get(endpoint, params=params)
    return response.json()["value"]

@Tool.register(m365_agent)
async def read_email(message_id: str):
    """Read the full content of an email message."""
    endpoint = f"/me/messages/{message_id}"

    response = await graph_client.get(endpoint)
    return response.json()

@Tool.register(m365_agent)
async def list_teams_channels():
    """List all teams and their channels."""
    endpoint = "/me/joinedTeams"
    params = {"$select": "id,displayName"}

    response = await graph_client.get(endpoint, params=params)
    teams = response.json()["value"]

    channels = []
    for team in teams:
        channel_endpoint = f"/teams/{team['id']}/channels"
        channel_response = await graph_client.get(channel_endpoint)
        channels.extend(channel_response.json()["value"])

    return {"teams": teams, "channels": channels}
```

---

## Microsoft Graph API Integration

Access M365 data through the unified Microsoft Graph API.

### Authentication

```python
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from msgraph.core import GraphClient

# Option 1: Service Principal (for backend agents)
credential = DefaultAzureCredential()

# Option 2: User Context (for user-delegated scenarios)
credential = InteractiveBrowserCredential(
    client_id="your-app-id",
    tenant_id="your-tenant-id"
)

# Create Graph client
graph_client = GraphClient(credential=credential)
```

### Permissions & Consent

Required permission scopes depend on your operations:

```python
# Define required permissions
required_permissions = [
    "Calendar.Read",           # Read calendar events
    "Mail.Read",              # Read emails
    "Files.Read",             # Read files in OneDrive
    "Sites.Read.All",         # Read SharePoint sites
    "Teams.Read.All",         # Read Teams information
    "User.Read",              # Read user profile
    "Presence.Read",          # Read user presence
]

# Request consent (user or admin)
credential_with_scopes = InteractiveBrowserCredential(
    client_id="your-app-id",
    tenant_id="your-tenant-id",
    scopes=[f"https://graph.microsoft.com/.default"]  # Requests all consented scopes
)
```

### Common Graph Operations

#### Get User Profile

```python
async def get_user_profile():
    """Retrieve authenticated user's profile."""
    response = await graph_client.get("/me")
    profile = response.json()

    return {
        "id": profile.get("id"),
        "displayName": profile.get("displayName"),
        "email": profile.get("userPrincipalName"),
        "jobTitle": profile.get("jobTitle"),
        "department": profile.get("department"),
    }
```

#### List Emails

```python
async def list_emails(folder: str = "inbox", limit: int = 10):
    """List emails from a specific folder."""
    endpoint = f"/me/mailFolders('{folder}')/messages"
    params = {
        "$top": limit,
        "$orderBy": "receivedDateTime desc",
        "$select": "id,subject,from,receivedDateTime,isRead"
    }

    response = await graph_client.get(endpoint, params=params)
    return response.json()["value"]
```

#### Get Calendar Events

```python
async def get_calendar_events(days: int = 7):
    """Get calendar events for the next N days."""
    from datetime import datetime, timedelta

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days)

    endpoint = "/me/calendarview"
    params = {
        "startDateTime": start_date.isoformat(),
        "endDateTime": end_date.isoformat(),
        "$orderBy": "start/dateTime",
        "$select": "id,subject,start,end,isReminderOn,categories"
    }

    response = await graph_client.get(endpoint, params=params)
    return response.json()["value"]
```

#### Create Event

```python
async def create_calendar_event(
    subject: str,
    start_time: datetime,
    end_time: datetime,
    attendees: list[str] = None
):
    """Create a calendar event."""
    event = {
        "subject": subject,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC"
        },
    }

    if attendees:
        event["attendees"] = [
            {
                "emailAddress": {"address": attendee},
                "type": "required"
            }
            for attendee in attendees
        ]

    response = await graph_client.post("/me/events", json=event)
    return response.json()
```

#### Access OneDrive Files

```python
async def list_onedrive_files(path: str = "root"):
    """List files in OneDrive."""
    endpoint = f"/me/drive/root:/{path}:/children"
    params = {"$select": "id,name,size,lastModifiedDateTime,webUrl"}

    response = await graph_client.get(endpoint, params=params)
    return response.json()["value"]

async def upload_file(file_path: str, dest_folder: str = "root"):
    """Upload file to OneDrive."""
    from pathlib import Path

    file = Path(file_path)
    endpoint = f"/me/drive/root:/{dest_folder}/{file.name}:/content"

    with open(file, "rb") as f:
        response = await graph_client.put(endpoint, content=f.read())

    return response.json()
```

#### Access SharePoint

```python
async def get_sharepoint_sites():
    """List SharePoint sites."""
    response = await graph_client.get("/sites?search=*")
    return response.json()["value"]

async def get_sharepoint_lists(site_id: str):
    """Get lists in a SharePoint site."""
    endpoint = f"/sites/{site_id}/lists"
    response = await graph_client.get(endpoint)
    return response.json()["value"]

async def get_list_items(site_id: str, list_id: str):
    """Get items from a SharePoint list."""
    endpoint = f"/sites/{site_id}/lists/{list_id}/items"
    params = {"$expand": "fields"}

    response = await graph_client.get(endpoint, params=params)
    return response.json()["value"]
```

---

## Teams Integration

Deploy agents as Teams bots or message extensions.

### Teams Bot Setup

```python
from agent_framework.teams import TeamsAgentAdapter
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from aiohttp import web

# Initialize Bot Framework adapter
SETTINGS = BotFrameworkAdapterSettings(
    app_id="your-bot-app-id",
    app_password="your-bot-app-password"
)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Create Teams-aware agent
m365_agent = ChatAgent(
    name="TeamsAssistant",
    chat_client=client,
)

# Create Teams adapter
teams_adapter = TeamsAgentAdapter(
    agent=m365_agent,
    app_id="your-bot-app-id"
)

# Error handling
async def on_error(context, error):
    logger.error(f"Teams bot error: {error}")
    await context.send_activity("An error occurred. Please try again.")

ADAPTER.on_turn_error = on_error

# Create web server
async def messages(req):
    """Handle incoming Teams messages."""
    body = await req.json()
    activity = ADAPTER.deserialize(body)

    async def logic(turn_context):
        await teams_adapter.process_activity(turn_context)

    await ADAPTER.process_activity(activity, logic)
    return web.Response(status=200)

app = web.Application()
app.router.add_post("/api/messages", messages)
```

### Adaptive Cards

Send rich, interactive cards in Teams:

```python
from botbuilder.schema import CardFactory, Attachment
import json

def create_report_card(report_data):
    """Create an adaptive card for displaying report."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Report: {report_data['title']}",
                "weight": "bolder",
                "size": "large"
            },
            {
                "type": "TextBlock",
                "text": report_data['summary'],
                "wrap": True
            },
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": f"**Metric**: {metric['name']}"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Value: {metric['value']}"
                            }
                        ]
                    }
                    for metric in report_data['metrics']
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "View Full Report",
                "url": report_data['url']
            },
            {
                "type": "Action.Submit",
                "title": "Export as PDF",
                "data": {"action": "export", "format": "pdf"}
            }
        ]
    }

    return CardFactory.adaptive_card(card)
```

### Message Extensions

Enable agents in Teams message compose box:

```python
# manifest.json extension configuration
{
  "composeExtensions": [
    {
      "botId": "your-bot-id",
      "commands": [
        {
          "id": "searchCommand",
          "title": "Search Documents",
          "description": "Search company documents and files",
          "initialRun": false,
          "parameters": [
            {
              "name": "searchQuery",
              "title": "Search for",
              "description": "What would you like to find?",
              "inputType": "text"
            }
          ]
        }
      ]
    }
  ]
}

# Handler code
async def handle_message_extension(turn_context):
    """Process message extension invocation."""
    invoke = turn_context.activity.value
    command = invoke["commandId"]

    if command == "searchCommand":
        query = invoke["parameters"][0]["value"]

        # Use agent to search
        results = await m365_agent.invoke(
            f"Search for documents matching: {query}"
        )

        # Format results for Teams
        attachments = [
            {
                "contentType": "application/vnd.microsoft.card.thumbnail",
                "content": {
                    "title": result["name"],
                    "subtitle": result["path"],
                    "tap": {
                        "type": "openUrl",
                        "value": result["webUrl"]
                    }
                }
            }
            for result in results
        ]

        response = {
            "composeExtension": {
                "type": "result",
                "attachmentLayout": "list",
                "attachments": attachments
            }
        }

        await turn_context.send_activity(response)
```

---

## Copilot Agent Registration

Register your agent with Microsoft Copilot for discovery and deployment.

### Registration Process

```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

# Register agent
def register_copilot_agent(
    agent_name: str,
    agent_description: str,
    agent_endpoint: str,
    resource_group: str,
    subscription_id: str
):
    """Register custom agent with Copilot."""
    credential = DefaultAzureCredential()
    client = CognitiveServicesManagementClient(credential, subscription_id)

    agent_config = {
        "name": agent_name,
        "description": agent_description,
        "endpoint": agent_endpoint,
        "properties": {
            "capabilities": [
                "chat",
                "function-calling",
                "streaming"
            ],
            "authentication": {
                "type": "oauth2",
                "clientId": "your-app-id"
            }
        }
    }

    # Register (implementation depends on Copilot API)
    return agent_config
```

### Admin Approval Workflow

1. Agent registration submitted by developer
2. Security review by IT admin
3. Compliance check (data access, privacy)
4. Approval and deployment to organization
5. User discovery in Copilot

---

## Security & Compliance for M365 Agents

### Data Access Controls

```python
from agent_framework import Middleware

class M365DataAccessMiddleware(Middleware):
    """Control what M365 data agents can access."""

    async def on_invoke(self, agent_state):
        """Verify agent has permission to access requested data."""
        user_context = agent_state.context

        # Check permission level
        permission_level = await self._get_user_permission_level(user_context["user_id"])

        if permission_level == "RESTRICTED":
            # Limit data access
            agent_state.metadata["data_access_level"] = "limited"
            agent_state.metadata["blocked_resources"] = [
                "email_external",
                "sharepoint_admin",
                "user_directory"
            ]

    async def _get_user_permission_level(self, user_id):
        """Query permission system."""
        # Example: check Azure AD group membership
        from azure.identity import DefaultAzureCredential
        from msgraph.core import GraphClient

        graph = GraphClient(credential=DefaultAzureCredential())
        endpoint = f"/users/{user_id}/memberOf"

        response = await graph.get(endpoint)
        groups = response.json()["value"]

        # Check for admin/restricted groups
        for group in groups:
            if "admin" in group.get("displayName", "").lower():
                return "ADMIN"

        return "STANDARD"
```

### Audit Logging for M365 Access

```python
from agent_framework import Middleware
from datetime import datetime
import json

class M365AuditMiddleware(Middleware):
    """Log all M365 API access for compliance."""

    async def on_tool_execute(self, agent_state, tool_result):
        """Log Graph API calls."""
        if "graph" in str(tool_result.tool_name).lower():
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "graph_api_call",
                "user_id": agent_state.context.get("user_id"),
                "agent": agent_state.agent.name,
                "resource": tool_result.tool_name,
                "success": tool_result.success,
                "session_id": agent_state.session_id,
            }

            # Write to audit log
            with open("/var/log/m365-agent-audit.jsonl", "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
```

---

## When to Use M365 Integration

| Use Case | Declarative | Custom Engine | Notes |
|----------|-------------|---------------|-------|
| Employee productivity assistant | YES | OPTIONAL | Copilot orchestration sufficient |
| Specialized data analyst | OPTIONAL | YES | Need custom reasoning |
| Teams bot | YES | YES | Both approaches work |
| Outlook add-in | YES | OPTIONAL | Limited Graph access needed |
| Complex workflows | NO | YES | Custom orchestration required |
| High security requirements | OPTIONAL | YES | Full control preferred |
| Rapid prototyping | YES | NO | Faster with Copilot |
| Open source LLM | NO | YES | Custom engine required |

---

## Complete Example: M365 Analysis Agent

```python
from agent_framework import ChatAgent, Tool
from azure.identity import DefaultAzureCredential
from msgraph.core import GraphClient
from datetime import datetime, timedelta

# Setup
auth = DefaultAzureCredential()
graph_client = GraphClient(credential=auth)
chat_client = AzureOpenAIClient(model="gpt-4")

# Create M365 agent
m365_analyst = ChatAgent(
    name="M365Analyst",
    chat_client=chat_client,
    description="Analyze Microsoft 365 business data",
    instructions="""You are an M365 analyst. Help users understand:
    - Meeting patterns and team productivity
    - Email communication trends
    - File collaboration and sharing
    - Overall organizational insights
    Always protect data privacy and confidentiality.
    """
)

# Register M365 tools
@Tool.register(m365_analyst)
async def get_team_meetings_summary(team_id: str, days: int = 30):
    """Analyze meeting patterns for a team."""
    endpoint = f"/teams/{team_id}/schedule"
    params = {
        "$filter": f"start/dateTime ge {(datetime.utcnow() - timedelta(days=days)).isoformat()}",
        "$select": "id,subject,start,end,organizer,attendees"
    }

    response = await graph_client.get(endpoint, params=params)
    events = response.json()["value"]

    # Analyze
    total_meetings = len(events)
    total_hours = sum([
        (datetime.fromisoformat(e["end"]["dateTime"]) -
         datetime.fromisoformat(e["start"]["dateTime"])).total_seconds() / 3600
        for e in events
    ])

    return {
        "period_days": days,
        "total_meetings": total_meetings,
        "total_hours_in_meetings": round(total_hours, 1),
        "avg_duration_minutes": round(total_hours * 60 / total_meetings if total_meetings else 0),
    }

@Tool.register(m365_analyst)
async def get_file_collaboration_stats():
    """Get collaboration statistics from OneDrive."""
    endpoint = "/me/drive/root:/children"
    params = {
        "$select": "id,name,lastModifiedDateTime,size,shared"
    }

    response = await graph_client.get(endpoint, params=params)
    files = response.json()["value"]

    recent_files = [f for f in files if
        datetime.fromisoformat(f["lastModifiedDateTime"]) >
        datetime.utcnow() - timedelta(days=7)
    ]

    return {
        "total_files": len(files),
        "recently_modified": len(recent_files),
        "shared_files": sum(1 for f in files if f.get("shared")),
    }

# Use the agent
result = await m365_analyst.invoke(
    "Summarize our team's meeting efficiency this month",
    context={"user_id": "user@contoso.com"}
)

print(result.message)
```

---

## Summary

M365 Integration enables:

1. **Declarative Agents**: Leverage Copilot for productivity scenarios
2. **Custom Engine Agents**: Full control for specialized use cases
3. **Graph API Access**: Unified access to all M365 data
4. **Teams Integration**: Deploy as bots and message extensions
5. **Enterprise Features**: Security, compliance, audit logging

Choose based on your customization needs and deployment timeline.
