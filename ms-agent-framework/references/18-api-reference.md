# API Reference — Classes, Methods, Signatures

## Core Classes

### AzureOpenAIResponsesClient

```python
from agent_framework.azure import AzureOpenAIResponsesClient

client = AzureOpenAIResponsesClient(
    project_endpoint: str,               # Azure AI project endpoint
    deployment_name: str,                 # Model deployment name
    credential: TokenCredential,          # AzureCliCredential or DefaultAzureCredential
    api_version: str = "2024-12-01",     # Optional API version override
)

agent = client.as_agent(
    name: str,                            # Agent name (used in hosting/A2A)
    instructions: str,                    # System prompt
    tools: list | callable = None,        # Function tools or tool names
    context_providers: list = None,       # Memory/context providers
    middleware: list = None,              # Agent-level middleware
    default_options: dict = None,         # Default run options
    mcp_servers: list[str] = None,        # Hosted MCP server names
    response_format: Type[BaseModel] = None,  # Default structured output
) -> Agent
```

### Agent

```python
class Agent:
    # Properties
    name: str                             # Agent name
    id: str                               # Agent identifier

    # Non-streaming run
    async def run(
        self,
        message: str | Message | list[Message],  # User input
        session: AgentSession = None,     # Session for multi-turn
        stream: Literal[False] = False,   # Non-streaming
        options: dict = None,             # Override run options
        tools: list = None,              # Additional tools for this run
        middleware: list = None,          # Run-level middleware
    ) -> AgentResponse

    # Streaming run
    async def run(
        self,
        message: str | Message | list[Message],
        session: AgentSession = None,
        stream: Literal[True] = True,
        options: dict = None,
        tools: list = None,
        middleware: list = None,
    ) -> ResponseStream

    # Session management
    def create_session(
        self,
        session_id: str = None,           # Optional custom ID
    ) -> AgentSession

    def get_session(
        self,
        service_session_id: str,          # Service conversation ID
    ) -> AgentSession
```

### AgentResponse

```python
class AgentResponse:
    text: str                             # Aggregated text from all messages
    messages: list[Message]               # All response messages
    value: T | None                       # Parsed structured output (if response_format set)
```

### ResponseStream

```python
class ResponseStream:
    # Async iteration — yields AgentResponseUpdate
    async def __aiter__(self) -> AsyncIterator[AgentResponseUpdate]

    # Get complete aggregated response
    async def get_final_response(self) -> AgentResponse
```

### AgentResponseUpdate

```python
class AgentResponseUpdate:
    text: str | None                      # Text portion of this chunk
    contents: list[Content]               # Content items in this update
```

### AgentSession

```python
class AgentSession:
    id: str                               # Local unique identifier
    service_session_id: str               # Remote service conversation ID
    state: dict                           # Mutable key-value store

    def to_dict(self) -> dict             # Serialize for persistence
    @classmethod
    def from_dict(cls, data: dict) -> AgentSession  # Deserialize
```

### Message

```python
class Message:
    role: str                             # "user", "assistant", "system"
    text: str                             # Text content (convenience)
    contents: list[Content]               # All content items

    def __init__(
        self,
        role: str,
        text: str = None,                 # Shorthand for text content
        contents: list = None,            # Full content list
    )
```

### Content

```python
class Content:
    type: str                             # "text", "data", "uri", etc.

    @staticmethod
    def from_text(text: str) -> Content
    @staticmethod
    def from_data(data: bytes, media_type: str) -> Content
    @staticmethod
    def from_uri(uri: str) -> Content
```

### Content Subclasses

```python
class TextContent(Content):
    text: str

class DataContent(Content):
    data: bytes
    media_type: str
    uri: str

class URIContent(Content):
    uri: str

class FunctionCallContent(Content):
    function_name: str
    arguments: dict

class FunctionResultContent(Content):
    function_name: str
    result: Any

class ErrorContent(Content):
    message: str

class UsageContent(Content):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

## Decorators

### @tool

```python
from agent_framework import tool
from typing import Annotated

@tool
def function_name(
    param: Annotated[type, "description"],
    optional_param: Annotated[type, "description"] = default,
) -> ReturnType:
    """Tool description (shown to LLM)."""
    ...
```

### Middleware Decorators

```python
from agent_framework import agent_middleware, function_middleware, chat_middleware

@agent_middleware
async def my_agent_mw(context: AgentRunContext, next) -> None: ...

@function_middleware
async def my_func_mw(context: FunctionInvocationContext, next) -> None: ...

@chat_middleware
async def my_chat_mw(context: ChatContext, next) -> None: ...
```

## Middleware Classes

```python
from agent_framework import AgentMiddleware, FunctionMiddleware, ChatMiddleware

class MyAgentMW(AgentMiddleware):
    async def process(self, context: AgentRunContext, next) -> None: ...

class MyFuncMW(FunctionMiddleware):
    async def process(self, context: FunctionInvocationContext, next) -> None: ...

class MyChatMW(ChatMiddleware):
    async def process(self, context: ChatContext, next) -> None: ...
```

## Context Types

```python
class AgentRunContext:
    messages: list[Message]
    metadata: dict
    terminate: bool
    result: AgentResponse | AsyncIterable[AgentResponseUpdate]
    is_streaming: bool

class FunctionInvocationContext:
    function: FunctionInfo
    function.name: str
    arguments: dict
    metadata: dict
    result: Any
    terminate: bool

class ChatContext:
    messages: list[Message]
    chat_client: Any
    metadata: dict
    result: Any
```

## Workflow Classes

```python
from agent_framework.workflows import Workflow, Executor, handler, executor, WorkflowContext

class Workflow:
    def add_node(self, name: str, executor: Executor) -> None
    def connect(self, from_node: str, to_node: str) -> None
    def set_entry_node(self, name: str) -> None
    def set_exit_node(self, name: str) -> None
    async def run(self, input_data: Any) -> WorkflowEvents

class Executor:
    def __init__(self, id: str)

class WorkflowContext[TInput, TOutput]:
    async def send_message(self, data: Any, target: str = None) -> None
    async def yield_output(self, data: TOutput) -> None

class WorkflowEvents:
    def get_outputs(self) -> Any
    def get_final_state(self) -> Any
```

## Provider Client Classes

```python
from agent_framework.azure import AzureOpenAIResponsesClient    # Azure OpenAI
from agent_framework.azure import AzureOpenAIChatClient          # Azure OpenAI (legacy)
from agent_framework.azure import AzureAIAgentClient             # Azure AI Foundry
from agent_framework.openai import OpenAIResponsesClient         # OpenAI
from agent_framework.anthropic import AnthropicChatClient        # Anthropic
from agent_framework.ollama import OllamaChatClient              # Ollama
from agent_framework.github import GitHubModelsChatClient        # GitHub Models
```

## Memory Classes

```python
from agent_framework import InMemoryHistoryProvider, BaseContextProvider

class InMemoryHistoryProvider:
    def __init__(
        self,
        name: str,
        load_messages: bool = True,
        store_context_messages: bool = False,
    )

class BaseContextProvider:
    async def get_context(self, session: AgentSession, **kwargs) -> str: ...
```

## Hosting Classes

```python
from agent_framework.azure import AgentFunctionApp

class AgentFunctionApp:
    def __init__(
        self,
        agents: list[Agent],
        enable_health_check: bool = True,
        max_poll_retries: int = 50,
    )
```

## Base Classes for Custom Agents

```python
from agent_framework import BaseAgent, SupportsAgentRun

class BaseAgent:
    async def _run_implementation(self, messages, session, **kwargs) -> AgentResponse: ...
    async def _run_streaming_implementation(self, messages, session, **kwargs) -> AsyncIterable: ...

class SupportsAgentRun:  # Protocol
    async def run(self, messages, session, *, stream, **kwargs): ...
```

## Utility Functions

```python
from agent_framework import normalize_messages

# Convert various input formats to list[Message]
messages = normalize_messages("Hello")           # str → [Message]
messages = normalize_messages(msg)               # Message → [Message]
messages = normalize_messages([msg1, msg2])      # passthrough
```
