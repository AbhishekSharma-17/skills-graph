# Productivity Toolkits

Pre-built toolkits for project management, calendars, spreadsheets, and business tools.

## Google Calendar

Event management with OAuth 2.0 authentication.

```bash
uv pip install -U tzlocal google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Setup:** Create OAuth 2.0 credentials in Google Cloud Console, download `credentials.json`.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.google_calendar import GoogleCalendarTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[GoogleCalendarTools(
        credentials_path="credentials.json",
        token_path="token.json",
    )],
)
agent.print_response("What meetings do I have this week?")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `credentials_path` | `str` | required | Path to OAuth credentials.json |
| `token_path` | `str` | `"token.json"` | Path to store OAuth token |
| `calendar_id` | `str` | `"primary"` | Calendar ID |
| `oauth_port` | `int` | `8080` | Port for OAuth redirect |
| `allow_update` | `bool` | `False` | Allow event modification |
| `scopes` | `list` | Google Calendar scopes | OAuth scopes |

**Functions:** `list_events`, `create_event`

---

## Google Sheets

Read, create, update, and duplicate spreadsheets.

```bash
uv pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

```python
from agno.tools.google_sheets import GoogleSheetsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[GoogleSheetsTools(
        spreadsheet_id="your_spreadsheet_id",
        creds_path="credentials.json",
    )],
)
agent.print_response("Read the data from Sheet1 and summarize it")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `spreadsheet_id` | `str` | `None` | Target spreadsheet ID |
| `spreadsheet_range` | `str` | `None` | Cell range (e.g., "A1:D10") |
| `creds_path` | `str` | `None` | Path to credentials.json |
| `token_path` | `str` | `None` | Path to token.json |
| `oauth_port` | `int` | `0` | OAuth redirect port |
| `enable_read_sheet` | `bool` | `True` | Read data |
| `enable_create_sheet` | `bool` | `True` | Create new sheet |
| `enable_update_sheet` | `bool` | `True` | Update data |
| `enable_create_duplicate_sheet` | `bool` | `True` | Duplicate sheet |

**Functions:** `read_sheet`, `create_sheet`, `update_sheet`, `create_duplicate_sheet`

---

## Notion

Page creation, updating, and search within Notion databases.

```bash
uv pip install -U notion-client
```

**Setup:**
1. Create integration at https://www.notion.so/my-integrations
2. Get Internal Integration Token
3. Create Notion Database and share with integration
4. Extract database ID from URL

```python
from agno.tools.notion import NotionTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[NotionTools(
        api_key="your_notion_api_key",
        database_id="your_database_id",
    )],
)
agent.print_response("Create a page titled 'Meeting Notes' with tag 'work'")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | env var | Notion API key |
| `database_id` | `str` | env var | Target database ID |
| `enable_create_page` | `bool` | `True` | Create pages |
| `enable_update_page` | `bool` | `True` | Update pages |
| `enable_search_pages` | `bool` | `True` | Search by tag |

**Environment:** `NOTION_API_KEY`, `NOTION_DATABASE_ID`

**Functions:** `create_page`, `update_page`, `search_pages`

---

## Linear

Issue tracking and project management for engineering teams.

```python
export LINEAR_API_KEY=your_key
```

```python
from agno.tools.linear import LinearTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[LinearTools()],
)
agent.print_response("Show me all high-priority issues assigned to me")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | env var | Linear API key |

**Functions:** `get_user_details`, `get_issue_details`, `create_issue`, `update_issue`, `get_user_assigned_issues`, `get_workflow_issues`, `get_high_priority_issues`

---

## Jira

Issue management, search, and commenting for Jira projects.

```bash
uv pip install -U jira
```

```python
from agno.tools.jira import JiraTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[JiraTools(
        server_url="https://your-org.atlassian.net",
        username="your_email",
        token="your_api_token",
    )],
)
agent.print_response("Search for open bugs in the PROJ project")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_url` | `str` | env var | Jira server URL |
| `username` | `str` | env var | Authentication username |
| `password` | `str` | `None` | Password (basic auth) |
| `token` | `str` | env var | API token |
| `enable_get_issue` | `bool` | `True` | Get issue details |
| `enable_create_issue` | `bool` | `True` | Create issues |
| `enable_search_issues` | `bool` | `True` | JQL search |
| `enable_add_comment` | `bool` | `True` | Add comments |

**Environment:** `JIRA_SERVER_URL`, `JIRA_USERNAME`, `JIRA_TOKEN`

**Functions:** `get_issue`, `create_issue`, `search_issues`, `add_comment`

---

## Todoist

Task management and organization.

```python
from agno.tools.todoist import TodoistTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[TodoistTools()],
)
agent.print_response("Show my tasks due today")
```

---

## Other Productivity Toolkits

| Toolkit | Import | Install | Description |
|---------|--------|---------|-------------|
| Confluence | `from agno.tools.confluence import ConfluenceTools` | `uv pip install atlassian-python-api` | Confluence wiki |
| ClickUp | `from agno.tools.clickup import ClickUpTools` | — | ClickUp project management |
| CalCom | `from agno.tools.calcom import CalComTools` | — | Scheduling |
| Shopify | `from agno.tools.shopify import ShopifyTools` | — | E-commerce management |
| Zendesk | `from agno.tools.zendesk import ZendeskTools` | — | Customer support |
| Airflow | `from agno.tools.airflow import AirflowTools` | — | Workflow orchestration |
| Composio | `from agno.tools.composio import ComposioTools` | `uv pip install composio-core` | Tool composition |
| Custom API | `from agno.tools.custom_api import CustomAPITools` | — | Custom REST API wrapper |
