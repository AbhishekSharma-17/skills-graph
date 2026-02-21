# Communication Toolkits

Pre-built toolkits for email, messaging, and social platforms.

## Email (SMTP)

Send emails via SMTP with configurable sender.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.email import EmailTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[EmailTools(
        receiver_email="team@example.com",
        sender_name="AI Assistant",
        sender_email="assistant@example.com",
        sender_passkey="your_app_password",
    )],
)
agent.print_response("Send a summary of today's tasks to the team")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `receiver_email` | `str` | required | Recipient email |
| `sender_name` | `str` | required | Sender display name |
| `sender_email` | `str` | required | Sender email address |
| `sender_passkey` | `str` | required | Email app password |
| `enable_email_user` | `bool` | `True` | Enable sending |

**Functions:** `email_user`

---

## Slack

Send messages, read channel history, and list channels.

```bash
uv pip install -U openai slack-sdk
export SLACK_TOKEN=xoxb-your-bot-token
```

```python
from agno.tools.slack import SlackTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[SlackTools()],
)
agent.print_response("List all channels and get the last 10 messages from #general")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token` | `str` | env var | Slack bot token |
| `enable_send_message` | `bool` | `True` | Send messages |
| `enable_send_message_thread` | `bool` | `True` | Reply in threads |
| `enable_list_channels` | `bool` | `True` | List channels |
| `enable_get_channel_history` | `bool` | `True` | Read channel history |

**Functions:** `send_message`, `list_channels`, `get_channel_history`

---

## Discord

Bot-based messaging, channel management, and message history.

```python
from agno.tools.discord import DiscordTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DiscordTools(bot_token="your_bot_token")],
)
agent.print_response("List all channels and send a greeting to #general")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bot_token` | `str` | required | Discord bot token |
| `enable_send_message` | `bool` | `True` | Send messages |
| `enable_get_channel_messages` | `bool` | `True` | Read message history |
| `enable_get_channel_info` | `bool` | `True` | Channel info |
| `enable_list_channels` | `bool` | `True` | List channels |
| `enable_delete_message` | `bool` | `False` | Delete messages |
| `all` | `bool` | `False` | Enable all functions |

---

## Telegram

Send messages via Telegram bot.

**Setup:** Create a bot with @BotFather, get the token, extract chat_id from `https://api.telegram.org/bot<TOKEN>/getUpdates`.

```python
from agno.tools.telegram import TelegramTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[TelegramTools(token="your_bot_token", chat_id="your_chat_id")],
)
agent.print_response("Send a daily summary to the group")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token` | `str` | required | Bot token from BotFather |
| `chat_id` | `str` | required | Target chat ID |
| `all` | `bool` | `False` | Enable all functions |

---

## Gmail

Google Gmail integration with OAuth.

```bash
uv pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Setup:** Create OAuth 2.0 credentials in Google Cloud Console.

```python
from agno.tools.gmail import GmailTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[GmailTools(credentials_path="credentials.json")],
)
agent.print_response("Show my latest unread emails")
```

---

## Other Communication Toolkits

| Toolkit | Import | Install | Description |
|---------|--------|---------|-------------|
| Twilio | `from agno.tools.twilio import TwilioTools` | `uv pip install twilio` | SMS & voice |
| WhatsApp | `from agno.tools.whatsapp import WhatsAppTools` | — | WhatsApp messaging |
| Webex | `from agno.tools.webex import WebexTools` | — | Cisco Webex messaging |
| X (Twitter) | `from agno.tools.x import XTools` | — | Twitter/X posting |
| Reddit | `from agno.tools.reddit import RedditTools` | `uv pip install praw` | Reddit interactions |
| Zoom | `from agno.tools.zoom import ZoomTools` | — | Zoom meeting management |
| Resend | `from agno.tools.resend import ResendTools` | `uv pip install resend` | Transactional email API |
| AWS SES | `from agno.tools.aws_ses import AWSSESTools` | `uv pip install boto3` | AWS email service |
