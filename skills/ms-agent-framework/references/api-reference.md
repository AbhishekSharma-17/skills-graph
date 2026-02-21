# API Reference — Complete Class & Method Signatures

## Table of Contents
1. [Chat Clients](#chat-clients)
2. [Agent](#agent)
3. [AgentSession](#agentsession)
4. [Workflow](#workflow)
5. [Tools](#tools)
6. [Context Providers](#context-providers)
7. [Middleware](#middleware)
8. [Response Types](#response-types)
9. [Exceptions](#exceptions)
10. [Environment Variables](#environment-variables)

---

## Chat Clients

### AzureOpenAIResponsesClient

```python
from agent_framework.azure import AzureOpenAIResponsesClient

class AzureOpenAIResponsesClient:
    def __init__(
        self,
        project_endpoint: str,          # Azure AI Foundry project endpoint
        deployment_name: str,            # Model deployment name (e.g., "gpt-4o")
        credential: TokenCredential,     # Azure credential
        api_version: str = "2024-12-01", # API version
    ): ...

    def as_agent(
        self,
        name: str,                                          # Agent identifier
        instructions: str,                                  # System prompt
        tools: Optional[List[Callable]] = None,             # @tool functions
        context_providers: Optional[List[BaseContextProvider]] = None,
        response_format: Optional[Type[BaseModel]] = None,  # Structured output
        mcp_servers: Optional[List[str]] = None,            # MCP server names
    ) -> Agent: ...

    async def run_streaming(self, message: str) -> AsyncIterator[str]: ...
```

### AzureOpenAIChatClient

```python
from agent_framework.azure import AzureOpenAIChatClient

class AzureOpenAIChatClient:
    def __init__(
        self,
        endpoint: str,
        deployment_name: str,
        credential: TokenCredential,
    ): ...

    def as_agent(self, **kwargs) -> Agent: ...
```

### OpenAIClient

```python
from openai import OpenAIClient

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"): ...
    def get_chat_client(self, model: str) -> ChatClient: ...
```

### AnthropicChatClient

```python
from agent_framework.anthropic import AnthropicChatClient

class AnthropicChatClient:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
    ): ...

    def as_agent(self, **kwargs) -> Agent: ...
```

### OllamaChatClient

```python
from agent_framework.ollama import OllamaChatClient

class OllamaChatClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
    ): ...

    def as_agent(self, **kwargs) -> Agent: ...
```

### GitHubModelsChatClient

```python
from agent_framework.github import GitHubModelsChatClient

class GitHubModelsChatClient:
    def __init__(
        self,
        token: str,           # GitHub PAT
        model: str = "gpt-4o",
    ): ...

    def as_agent(self, **kwargs) -> Agent: ...
```

---

## Agent

```python
from agent_framework import Agent

class Agent:
    @property
    def name(self) -> str: ...

    @property
    def instructions(self) -> str: ...

    async def run(
        self,
        message: str,                            # User message
        session: Optional[AgentSession] = None,  # Multi-turn context
        stream: bool = False,                    # Token streaming
    ) -> Union[str, AsyncIterator[ChatResponse]]: ...

    async def create_session(
        self,
        session_id: Optional[str] = None,  # Custom session ID
    ) -> AgentSession: ...

    async def get_session(
        self,
        service_session_id: str,
    ) -> AgentSession: ...

    def as_builder(self) -> AgentBuilder: ...

    def as_tool(self) -> Callable:
        """Expose this agent as a tool for other agents"""
        ...
```

### AgentBuilder

```python
class AgentBuilder:
    def use(
        self,
        runFunc: Optional[Callable] = None,          # Regular run middleware
        runStreamingFunc: Optional[Callable] = None,  # Streaming middleware
    ) -> "AgentBuilder": ...

    def build(self) -> Agent: ...
```

---

## AgentSession

```python
from agent_framework import AgentSession

class AgentSession:
    @property
    def id(self) -> str: ...                        # Local session ID

    @property
    def service_session_id(self) -> str: ...        # Remote service ID

    @property
    def state(self) -> dict: ...                    # Mutable key-value store

    @property
    def messages(self) -> List[Message]: ...        # Conversation history

    def to_dict(self) -> dict: ...                  # Serialize

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSession": ...  # Deserialize

    async def save(self) -> None: ...               # Persist to storage
    async def load(self, session_id: str) -> None: ...  # Load from storage
```

### Message

```python
class Message:
    role: str       # "user" or "assistant"
    content: str    # Message text
    timestamp: datetime
```

---

## Workflow

```python
from agent_framework import Workflow, ExecutionUnit

class Workflow:
    def __init__(self, name: str): ...

    def add_execution_unit(
        self,
        name: str,                              # Unique identifier
        executor: Union[Agent, Callable],       # Agent or async function
    ) -> ExecutionUnit: ...

    def add_edge(
        self,
        from_name: str,                         # Source unit
        to_name: str,                           # Target unit
        condition: Optional[Callable[[Any], bool]] = None,  # Gate function
    ) -> None: ...

    def set_entry_point(self, unit_name: str) -> None: ...
    def set_exit_point(self, unit_name: str) -> None: ...

    async def run_from_input(self, input_data: dict) -> dict: ...
    async def checkpoint(self, checkpoint_id: str, state: dict) -> None: ...
    async def restore_from_checkpoint(self, checkpoint_id: str) -> dict: ...

class ExecutionUnit:
    name: str
    executor: Union[Agent, Callable]
    async def execute(self, input_data: dict) -> dict: ...
```

---

## Tools

### @tool Decorator

```python
from agent_framework import tool
from typing import Annotated

@tool
def function_name(
    param: Annotated[type, "Description"],
    optional_param: Annotated[type, "Description"] = default,
) -> ReturnType:
    """Docstring — used as tool description for the LLM"""
    ...
```

### MCP Tools

```python
from agent_framework.tools import MCPStdioTool, MCPWebSocketTool, MCPHttpTool

class MCPStdioTool:
    def __init__(
        self,
        name: str,
        command: str,              # Command to run
        args: List[str] = [],      # Command arguments
        env: Optional[dict] = None, # Environment variables
    ): ...

class MCPWebSocketTool:
    def __init__(
        self,
        name: str,
        url: str,                   # WebSocket URL
        auth_token: Optional[str] = None,
    ): ...

class MCPHttpTool:
    def __init__(
        self,
        name: str,
        base_url: str,
        headers: Optional[dict] = None,
    ): ...
```

### OpenAPI Tool

```python
from agent_framework.tools import OpenAPITool

class OpenAPITool:
    def __init__(
        self,
        name: str,
        spec_url: Optional[str] = None,   # URL to OpenAPI spec
        spec_path: Optional[str] = None,   # Local path to spec
        auth: Optional[dict] = None,       # Authentication config
    ): ...
```

### ToolSchema

```python
from agent_framework.types import ToolSchema, ParameterSchema

class ToolSchema:
    name: str
    description: str
    parameters: Dict[str, ParameterSchema]

class ParameterSchema:
    name: str
    type: str           # "string", "integer", "number", "boolean", "array", "object"
    description: str
    required: bool
    default: Optional[Any]
```

---

## Context Providers

```python
from agent_framework import BaseContextProvider

class BaseContextProvider:
    async def get_context(self, session: AgentSession, **kwargs) -> str: ...
    async def on_session_created(self, session: AgentSession) -> None: ...
    async def on_session_closed(self, session: AgentSession) -> None: ...
```

### Built-in Providers

```python
from agent_framework.memory import (
    InMemoryHistoryProvider,
    RedisContextProvider,
    Mem0ContextProvider,
    SlidingWindowHistoryProvider,
)

class InMemoryHistoryProvider(BaseContextProvider):
    def __init__(self, name: str, load_messages: bool = True,
                 store_context_messages: bool = False, max_messages: int = 100): ...

class RedisContextProvider(BaseContextProvider):
    def __init__(self, redis_url: str, db: int = 0, ttl: int = 86400): ...

class Mem0ContextProvider(BaseContextProvider):
    def __init__(self, api_key: str, org_id: str): ...

class SlidingWindowHistoryProvider(BaseContextProvider):
    def __init__(self, max_window_size: int, base_provider: BaseContextProvider): ...
```

---

## Middleware

### Function Signature

```python
async def middleware_function(request) -> Any:
    """
    request attributes:
        .message: str          — User message
        .session: AgentSession — Current session (or None)
        .tools: List           — Available tools
        .agent_name: str       — Agent name
        .invoke(): Coroutine   — Call next handler in pipeline

    Returns: Agent response (str or structured)
    """
    result = await request.invoke()
    return result
```

---

## Response Types

```python
class ChatResponse:
    text: str
    role: str                # "assistant"
    finish_reason: str       # "stop", "length", "content_filter"
    usage: Optional[ChatCompletionTokenUsage]

class ChatCompletionTokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

---

## Exceptions

```
Exception
├── AgentException
│   ├── AgentExecutionError      # agent.run() failed
│   ├── AgentToolError           # Tool invocation failed
│   └── AgentValidationError     # Invalid input
├── SessionException
│   ├── SessionNotFoundError     # Session doesn't exist
│   ├── SessionExpiredError      # Session expired
│   └── SessionStateError        # Invalid state
├── WorkflowException
│   ├── WorkflowExecutionError   # Workflow step failed
│   ├── WorkflowGraphError       # Invalid graph structure
│   └── CheckpointError          # Checkpoint failed
├── ToolException
│   ├── ToolNotFoundError        # Tool not registered
│   └── ToolInvocationError      # Tool execution failed
├── ContextException
│   └── ContextProviderError     # Provider failed
└── MiddlewareException
    └── MiddlewareExecutionError # Middleware failed
```

### Usage

```python
from agent_framework import AgentExecutionError, SessionNotFoundError

try:
    result = await agent.run("message", session=session)
except AgentExecutionError as e:
    print(f"Agent failed: {e.message}")
    if e.cause:
        print(f"Caused by: {e.cause}")
except SessionNotFoundError as e:
    print(f"Session not found: {e.session_id}")
```

---

## Environment Variables

```bash
# AZURE OPENAI (Primary)
AZURE_AI_PROJECT_ENDPOINT              # Required
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME # Required
AZURE_OPENAI_API_VERSION               # Optional: "2024-12-01"
AZURE_OPENAI_API_KEY                   # Optional: if not using credential

# AZURE AUTH
AZURE_TENANT_ID                        # Service principal
AZURE_CLIENT_ID                        # Service principal
AZURE_CLIENT_SECRET                    # Service principal
AZURE_SUBSCRIPTION_ID                  # Azure subscription

# OPENAI
OPENAI_API_KEY                         # Required for OpenAI provider
OPENAI_MODEL                           # Default: "gpt-4o-mini"

# ANTHROPIC
ANTHROPIC_API_KEY                      # Required for Claude provider

# GITHUB
GITHUB_TOKEN                           # Required for GitHub Models
GITHUB_MODEL                           # Default: "gpt-4o"

# OLLAMA
OLLAMA_ENDPOINT                        # Default: "http://localhost:11434"
OLLAMA_MODEL                           # Default: "llama2"

# MEMORY
REDIS_URL                              # Redis provider
MEM0_API_KEY                           # Mem0 provider
DURABLE_TASK_HUB_NAME                  # Durable Functions

# OBSERVABILITY
OTEL_EXPORTER_OTLP_ENDPOINT           # OpenTelemetry collector
APPLICATIONINSIGHTS_CONNECTION_STRING  # Azure Monitor
LOG_LEVEL                              # DEBUG, INFO, WARNING, ERROR
ENABLE_TELEMETRY                       # true/false
```
