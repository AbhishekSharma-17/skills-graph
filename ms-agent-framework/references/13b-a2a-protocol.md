# Agent-to-Agent (A2A) Protocol — Interoperable Agent Communication

## Overview

### What is A2A?
The Agent-to-Agent (A2A) protocol is a standardized HTTP/JSON-RPC protocol for seamless communication between different AI agents across frameworks and languages. It enables agents to discover each other's capabilities, invoke operations, and stream responses in a framework-agnostic manner.

### Standards Basis
- Based on [a2a-protocol.org](https://a2a-protocol.org) specification
- HTTP-based with JSON-RPC 2.0 message format
- Supports both request-response and streaming patterns
- Authentication via standard Bearer tokens or custom interceptors

### Key Features
- **Agent Discovery**: Dynamically discover remote agent capabilities via AgentCard
- **Interoperability**: Connect agents across different frameworks (Python, JavaScript, Go, Rust, Java)
- **Streaming**: Real-time response streaming for long-running operations
- **Authentication**: Pluggable auth layer for secure agent-to-agent communication
- **Resilience**: Built-in timeout and retry mechanisms

### Core Components
1. **A2AAgent**: Client for calling remote agents
2. **A2AServer**: Server hosting agents as A2A services
3. **AgentCard**: Agent metadata and capability descriptor
4. **A2ACardResolver**: Discovers AgentCard from remote hosts
5. **TaskManager**: Manages concurrent agent invocations

---

## A2AAgent Class (Client-Side)

### Purpose
`A2AAgent` is a client wrapper that allows you to call remote agents as if they were local. It handles service discovery, message serialization, streaming, and error handling.

### Basic Usage Pattern

```python
from agent_framework.a2a import A2AAgent, A2ACardResolver
import httpx

# Step 1: Discover the remote agent's capabilities
async with httpx.AsyncClient(timeout=60.0) as http_client:
    resolver = A2ACardResolver(
        httpx_client=http_client,
        base_url="http://remote-agent-host:8000"
    )
    agent_card = await resolver.get_agent_card()
    # agent_card contains name, description, tools, parameters

# Step 2: Create an A2AAgent instance
agent = A2AAgent(
    name=agent_card.name,
    description=agent_card.description,
    agent_card=agent_card,
    url="http://remote-agent-host:8000",
    timeout=60.0
)

# Step 3: Invoke the agent
result = await agent.run("What is the weather in Paris?")
print(result)
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | - | Display name of the remote agent |
| `id` | str | No | UUID | Unique identifier for this client instance |
| `description` | str | No | "" | Human-readable description of agent capabilities |
| `agent_card` | AgentCard | No | None | Pre-resolved AgentCard from remote host |
| `url` | str | Yes | - | Base URL of the remote A2A service |
| `client` | Agent | No | None | Optional local agent for context |
| `http_client` | httpx.AsyncClient | No | None | Custom HTTP client (auto-created if not provided) |
| `auth_interceptor` | AuthInterceptor | No | None | Authentication handler (see Authentication section) |
| `timeout` | float | No | 30.0 | Request timeout in seconds |

### API Methods

#### `async run(input: str, stream: bool = False, **kwargs) -> str | AsyncIterator[str]`

Execute the remote agent with input text.

```python
# Non-streaming execution
result = await agent.run("Summarize the top 3 news stories")
print(f"Result: {result}")

# Streaming execution
async with agent.run("Write a long essay on AI", stream=True) as stream:
    async for chunk in stream:
        print(chunk, end="", flush=True)
```

**Parameters:**
- `input` (str): The prompt or question for the remote agent
- `stream` (bool): If True, returns an async iterator for streaming responses
- `**kwargs`: Additional parameters passed to the remote agent's run method

**Returns:**
- Non-streaming: Complete response string
- Streaming: AsyncIterator yielding response chunks

**Raises:**
- `TimeoutError`: If the request exceeds the configured timeout
- `A2AConnectionError`: If the remote agent is unreachable
- `A2AProtocolError`: If the response format is invalid

#### `async invoke_tool(tool_name: str, **params) -> Any`

Call a specific tool exposed by the remote agent.

```python
# Invoke a tool on the remote agent
result = await agent.invoke_tool(
    "search_web",
    query="quantum computing breakthroughs",
    num_results=5
)
```

**Parameters:**
- `tool_name` (str): Name of the tool as defined in the remote agent's AgentCard
- `**params`: Tool-specific parameters matching the tool's schema

**Returns:** Tool execution result

#### `async close()`

Clean up resources and close the HTTP client.

```python
try:
    result = await agent.run("What is 2+2?")
finally:
    await agent.close()
```

---

## AgentCard — Agent Discovery and Metadata

### What AgentCard Contains

AgentCard is a JSON descriptor that contains everything needed to call a remote agent:

```json
{
  "name": "DocumentAnalyzer",
  "id": "doc-analyzer-v1",
  "description": "Analyzes documents and extracts insights",
  "version": "1.0.0",
  "endpoints": {
    "invoke": "http://analyzer-host:8000/invoke",
    "stream": "http://analyzer-host:8000/stream"
  },
  "tools": [
    {
      "name": "extract_text",
      "description": "Extract text from a document",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "Path to the document file"
          },
          "format": {
            "type": "string",
            "enum": ["pdf", "docx", "txt"],
            "description": "Document format"
          }
        },
        "required": ["file_path"]
      }
    }
  ],
  "auth": {
    "type": "bearer",
    "schemes": ["api_key"]
  }
}
```

### AgentCard Structure (Python)

```python
from agent_framework.a2a import AgentCard
from typing import List, Dict, Any

class AgentCard:
    """Describes a remote agent's capabilities and how to call it."""

    name: str                          # Agent's display name
    id: str                            # Unique identifier
    description: str                   # What the agent does
    version: str                       # Agent version
    endpoints: Dict[str, str]         # URLs for invoke, stream, etc.
    tools: List[Dict[str, Any]]       # Available tools with schemas
    auth: Dict[str, Any]              # Authentication requirements
    metadata: Dict[str, str]          # Additional custom metadata
```

### Resolving AgentCard from Remote Hosts

```python
from agent_framework.a2a import A2ACardResolver
import httpx

# Create resolver
async with httpx.AsyncClient() as client:
    resolver = A2ACardResolver(
        httpx_client=client,
        base_url="http://remote-agent:8000"
    )

    # Fetch the AgentCard
    card = await resolver.get_agent_card()
    print(f"Agent: {card.name}")
    print(f"Tools available: {[t['name'] for t in card.tools]}")

# The resolver makes a GET request to:
# http://remote-agent:8000/.agent/card
```

### Caching AgentCards

```python
from agent_framework.a2a import A2ACardResolver
import httpx

class CachedCardResolver(A2ACardResolver):
    """Cache AgentCards in memory."""

    def __init__(self, *args, cache_ttl: int = 3600, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
        self.cache_ttl = cache_ttl

    async def get_agent_card(self):
        if "card" in self._cache:
            return self._cache["card"]
        card = await super().get_agent_card()
        self._cache["card"] = card
        return card

# Use cached resolver
resolver = CachedCardResolver(
    httpx_client=client,
    base_url="http://remote-agent:8000",
    cache_ttl=3600
)
```

---

## Hosting an Agent as A2A Service

### Setting Up A2AServer

```python
from agent_framework.a2a import A2AServer
from agent_framework.core import Agent

# Create your local agent(s)
my_agent = Agent(
    name="ResearchAssistant",
    instructions="You are a research assistant that finds and summarizes information."
)

# Create A2A server
server = A2AServer(
    agents=[my_agent],
    host="0.0.0.0",
    port=8000,
    cors_origins=["*"]  # Restrict in production
)

# Run the server
await server.run()
```

### With Authentication

```python
from agent_framework.a2a import A2AServer, BearerTokenAuth

auth = BearerTokenAuth(
    tokens=["sk-agent-secret-token-123"]
)

server = A2AServer(
    agents=[my_agent],
    auth=auth,
    host="0.0.0.0",
    port=8000
)

await server.run()
```

### Complete Server Example

```python
from fastapi import FastAPI, Depends
from agent_framework.a2a import A2AServer
from agent_framework.core import Agent

# Create agents
researcher = Agent(
    name="Researcher",
    instructions="You research topics and provide summaries."
)

writer = Agent(
    name="Writer",
    instructions="You write well-structured content based on research."
)

# Create server with multiple agents
server = A2AServer(
    agents=[researcher, writer],
    host="0.0.0.0",
    port=8000
)

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

### Server Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agents` | List[Agent] | [] | Local agents to expose |
| `host` | str | "0.0.0.0" | Bind address |
| `port` | int | 8000 | Port number |
| `auth` | AuthInterceptor | None | Authentication handler |
| `cors_origins` | List[str] | ["*"] | CORS allowed origins |
| `max_concurrent_calls` | int | 100 | Max parallel invocations |
| `timeout` | float | 300.0 | Default timeout per call |

---

## Calling Remote A2A Agents

### Non-Streaming Pattern

```python
from agent_framework.a2a import A2AAgent, A2ACardResolver
import httpx

async def query_remote_agent():
    async with httpx.AsyncClient() as client:
        # Discover agent
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url="http://analytics-agent:8000"
        )
        card = await resolver.get_agent_card()

        # Create client
        agent = A2AAgent(
            name=card.name,
            description=card.description,
            agent_card=card,
            url="http://analytics-agent:8000"
        )

        # Call agent
        response = await agent.run(
            "Analyze sales data for Q4 2024"
        )
        print(f"Response:\n{response}")

        await agent.close()
```

### Streaming Pattern

```python
async def stream_from_remote_agent():
    async with httpx.AsyncClient() as client:
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url="http://content-agent:8000"
        )
        card = await resolver.get_agent_card()

        agent = A2AAgent(
            name=card.name,
            agent_card=card,
            url="http://content-agent:8000"
        )

        # Stream the response
        try:
            async with agent.run(
                "Write a 5000-word article on neural networks",
                stream=True
            ) as stream:
                async for chunk in stream:
                    print(chunk, end="", flush=True)
        finally:
            await agent.close()
```

### With Error Handling

```python
from agent_framework.a2a.exceptions import (
    A2AConnectionError,
    A2AProtocolError,
    A2ATimeoutError
)

async def robust_agent_call():
    async with httpx.AsyncClient() as client:
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url="http://agent:8000"
        )

        try:
            card = await resolver.get_agent_card()
        except A2AConnectionError:
            print("Agent service is unreachable")
            return

        agent = A2AAgent(
            name=card.name,
            agent_card=card,
            url="http://agent:8000",
            timeout=30.0
        )

        try:
            result = await agent.run("Your question here")
            print(result)
        except A2ATimeoutError:
            print("Request timed out after 30 seconds")
        except A2AProtocolError as e:
            print(f"Protocol error: {e}")
        finally:
            await agent.close()
```

### Passing Agent Context

```python
# Some agents may accept context about the calling agent
async def call_with_context():
    my_agent = Agent(
        name="MainOrchestrator",
        instructions="Orchestrates other agents"
    )

    remote_agent = A2AAgent(
        name="DataProcessor",
        url="http://processor:8000",
        client=my_agent  # Pass local agent as context
    )

    result = await remote_agent.run(
        "Process the uploaded dataset",
        context_agent=my_agent  # Some agents use this
    )
```

---

## Using A2A Agents in Workflows

### Remote Agents as Tools

```python
from agent_framework.core import Agent
from agent_framework.a2a import A2AAgent, A2ACardResolver

async def create_orchestration():
    async with httpx.AsyncClient() as client:
        # Discover available agents
        search_resolver = A2ACardResolver(
            httpx_client=client,
            base_url="http://search-agent:8000"
        )
        search_card = await search_resolver.get_agent_card()

        # Create clients for remote agents
        search_agent = A2AAgent(
            name="SearchAgent",
            agent_card=search_card,
            url="http://search-agent:8000"
        )

        # Create local orchestrator
        orchestrator = Agent(
            name="Orchestrator",
            instructions="Coordinate multiple agents to answer complex questions"
        )

        # Use remote agent as a tool in orchestrator
        orchestrator.add_tool(
            name="search",
            description="Search the web for information",
            func=search_agent.run
        )

        # Now orchestrator can call search_agent
        result = await orchestrator.run(
            "Find and summarize the latest AI research papers"
        )
```

### A2A Agent Chain Pattern

```python
async def chain_agents():
    """Chain multiple A2A agents in sequence."""

    async with httpx.AsyncClient() as client:
        # Create clients for each agent in chain
        agents = {}
        for agent_name in ["researcher", "analyst", "writer"]:
            resolver = A2ACardResolver(
                httpx_client=client,
                base_url=f"http://{agent_name}-agent:8000"
            )
            card = await resolver.get_agent_card()
            agents[agent_name] = A2AAgent(
                name=agent_name,
                agent_card=card,
                url=f"http://{agent_name}-agent:8000"
            )

        try:
            # Step 1: Research
            research_result = await agents["researcher"].run(
                "Research quantum computing developments in 2024"
            )

            # Step 2: Analyze
            analysis_result = await agents["analyst"].run(
                f"Analyze this research: {research_result}"
            )

            # Step 3: Write
            final_result = await agents["writer"].run(
                f"Write an article based on this analysis: {analysis_result}"
            )

            return final_result
        finally:
            for agent in agents.values():
                await agent.close()
```

### Parallel Agent Calls

```python
import asyncio

async def parallel_agents():
    """Call multiple A2A agents concurrently."""

    async with httpx.AsyncClient() as client:
        # Create multiple agent clients
        agents = {}
        for i in range(5):
            resolver = A2ACardResolver(
                httpx_client=client,
                base_url=f"http://worker-agent-{i}:8000"
            )
            card = await resolver.get_agent_card()
            agents[i] = A2AAgent(
                name=f"Worker{i}",
                agent_card=card,
                url=f"http://worker-agent-{i}:8000"
            )

        # Call all agents concurrently
        tasks = [
            agents[i].run(f"Process batch {i}")
            for i in agents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Clean up
        await asyncio.gather(
            *[agent.close() for agent in agents.values()]
        )

        return results
```

---

## Authentication

### Bearer Token Authentication

```python
from agent_framework.a2a.client.auth import BearerTokenAuth

auth = BearerTokenAuth(token="sk-agent-xyz123")

agent = A2AAgent(
    name="SecureAgent",
    url="http://secure-agent:8000",
    auth_interceptor=auth
)

result = await agent.run("Query me securely")
```

### Basic Authentication

```python
from agent_framework.a2a.client.auth import BasicAuth

auth = BasicAuth(username="agent_user", password="secret_pass")

agent = A2AAgent(
    name="BasicAuthAgent",
    url="http://agent:8000",
    auth_interceptor=auth
)
```

### API Key Authentication

```python
from agent_framework.a2a.client.auth import ApiKeyAuth

auth = ApiKeyAuth(api_key="my-api-key-123", header_name="X-API-Key")

agent = A2AAgent(
    name="ApiKeyAgent",
    url="http://agent:8000",
    auth_interceptor=auth
)
```

### Custom Authentication

```python
from agent_framework.a2a.client.auth import AuthInterceptor
import httpx

class CustomAuth(AuthInterceptor):
    """Custom authentication implementation."""

    def __init__(self, secret: str):
        self.secret = secret

    async def intercept_request(self, request: httpx.Request) -> httpx.Request:
        """Modify request before sending."""
        import hashlib
        signature = hashlib.sha256(
            f"{self.secret}{request.method}".encode()
        ).hexdigest()
        request.headers["X-Signature"] = signature
        return request

    async def handle_response(self, response: httpx.Response) -> httpx.Response:
        """Handle response after receiving."""
        if response.status_code == 401:
            raise Exception("Authentication failed")
        return response

auth = CustomAuth(secret="my-secret")
agent = A2AAgent(
    name="CustomAuthAgent",
    url="http://agent:8000",
    auth_interceptor=auth
)
```

### Server-Side Authentication

```python
from agent_framework.a2a import A2AServer, BearerTokenAuth

# Configure with multiple valid tokens
auth = BearerTokenAuth(
    tokens=["sk-token-1", "sk-token-2", "sk-token-3"]
)

server = A2AServer(
    agents=[my_agent],
    auth=auth,
    host="0.0.0.0",
    port=8000
)

await server.run()
```

---

## A2A vs Direct Agent Calls

| Aspect | A2A Protocol | Direct Agent Calls |
|--------|--------------|-------------------|
| **Communication** | HTTP/JSON-RPC over network | In-process method calls |
| **Framework Coupling** | None - protocol agnostic | Tight - same framework required |
| **Language Support** | Any language with HTTP client | Limited to framework's language |
| **Latency** | Higher (network overhead) | Minimal |
| **Scalability** | Horizontal - scale agents independently | Vertical - single process |
| **Failure Isolation** | Agent crash doesn't affect caller | Propagates to caller |
| **Security** | Can add authentication layer | Implicit trust within process |
| **Discovery** | Via AgentCard mechanism | Manual configuration |
| **Streaming** | Native support via SSE | Direct async iteration |
| **Use Case** | Microservices, federated agents | Monolithic applications |

---

## Environment Variables

### Agent Client Configuration

```bash
# Remote agent base URL
A2A_AGENT_HOST=http://remote-agent:8000

# Authentication token
A2A_AGENT_TOKEN=sk-secret-token-xyz

# Request timeout (seconds)
A2A_AGENT_TIMEOUT=60

# Enable debug logging
A2A_DEBUG=true

# Custom CA certificate for HTTPS
A2A_CA_CERT=/path/to/ca.pem

# HTTP proxy
A2A_HTTP_PROXY=http://proxy:8080
A2A_HTTPS_PROXY=https://proxy:8080
```

### Agent Server Configuration

```bash
# Server binding
A2A_SERVER_HOST=0.0.0.0
A2A_SERVER_PORT=8000

# Authentication
A2A_AUTH_TYPE=bearer
A2A_AUTH_TOKENS=sk-token-1,sk-token-2,sk-token-3

# CORS settings
A2A_CORS_ORIGINS=http://localhost:3000,https://example.com

# Performance
A2A_MAX_CONCURRENT_CALLS=100
A2A_DEFAULT_TIMEOUT=300

# SSL/TLS
A2A_SSL_CERT=/path/to/cert.pem
A2A_SSL_KEY=/path/to/key.pem
```

### Usage in Code

```python
import os
from agent_framework.a2a import A2AAgent, A2ACardResolver

async def create_agent_from_env():
    host = os.getenv("A2A_AGENT_HOST", "http://localhost:8000")
    token = os.getenv("A2A_AGENT_TOKEN")
    timeout = float(os.getenv("A2A_AGENT_TIMEOUT", "60"))

    if token:
        from agent_framework.a2a.client.auth import BearerTokenAuth
        auth = BearerTokenAuth(token=token)
    else:
        auth = None

    async with httpx.AsyncClient() as client:
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url=host
        )
        card = await resolver.get_agent_card()

        return A2AAgent(
            name=card.name,
            agent_card=card,
            url=host,
            auth_interceptor=auth,
            timeout=timeout
        )
```

---

## Complete Working Example

### Full End-to-End A2A Workflow

```python
import asyncio
import httpx
from agent_framework.a2a import A2AAgent, A2ACardResolver, A2AServer
from agent_framework.core import Agent

# ============================================
# PART 1: Set up remote agent service
# ============================================

async def setup_remote_service():
    """Start the remote A2A agent service."""

    # Create the remote agent
    remote_agent = Agent(
        name="DataAnalysisAgent",
        instructions="""You are a data analysis expert.
        You can analyze datasets, find patterns, and provide insights.
        Always explain your reasoning step by step."""
    )

    # Add some tools to it
    def analyze_csv(file_path: str) -> str:
        """Dummy CSV analysis tool."""
        return f"Analyzed {file_path}: Found 1000 rows, 5 columns, no missing values"

    remote_agent.add_tool(
        name="analyze_csv",
        description="Analyze a CSV file and report statistics",
        func=analyze_csv
    )

    # Create A2A server
    server = A2AServer(
        agents=[remote_agent],
        host="0.0.0.0",
        port=9000
    )

    return server

# ============================================
# PART 2: Client calling the remote agent
# ============================================

async def client_calls_remote():
    """Client application calling the remote A2A agent."""

    async with httpx.AsyncClient() as client:
        # Step 1: Discover the agent
        print("Step 1: Discovering remote agent...")
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url="http://localhost:9000"
        )
        agent_card = await resolver.get_agent_card()
        print(f"  Found agent: {agent_card.name}")
        print(f"  Description: {agent_card.description}")
        print(f"  Available tools: {[t['name'] for t in agent_card.tools]}")

        # Step 2: Create client for remote agent
        print("\nStep 2: Creating A2A client...")
        agent = A2AAgent(
            name=agent_card.name,
            description=agent_card.description,
            agent_card=agent_card,
            url="http://localhost:9000",
            timeout=30.0
        )

        # Step 3: Call the agent (non-streaming)
        print("\nStep 3: Non-streaming call...")
        result = await agent.run(
            "Analyze the sales_data_2024.csv file and tell me the top insights"
        )
        print(f"Result:\n{result}\n")

        # Step 4: Call the agent (streaming)
        print("Step 4: Streaming call...")
        print("Response: ", end="", flush=True)
        async with agent.run(
            "Write a detailed analysis report of quarterly sales trends",
            stream=True
        ) as stream:
            async for chunk in stream:
                print(chunk, end="", flush=True)
        print("\n")

        # Step 5: Clean up
        await agent.close()
        print("Step 5: Connection closed")

# ============================================
# PART 3: Run both server and client
# ============================================

async def main():
    """Run server and client concurrently."""

    # Start server in background
    server = await setup_remote_service()
    server_task = asyncio.create_task(server.run())

    try:
        # Give server time to start
        await asyncio.sleep(1)

        # Run client
        await client_calls_remote()
    finally:
        # Shut down server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
```

### Output Example

```
Step 1: Discovering remote agent...
  Found agent: DataAnalysisAgent
  Description: You are a data analysis expert...
  Available tools: ['analyze_csv']

Step 2: Creating A2A client...

Step 3: Non-streaming call...
Result:
Based on the CSV analysis showing 1000 rows with 5 columns and no missing values,
here are the key insights:
1. Complete data integrity - all records are valid
2. Manageable dataset size for detailed analysis
3. Ready for statistical modeling and pattern detection
...

Step 4: Streaming call...
Response: # Quarterly Sales Analysis Report

## Executive Summary
The quarterly sales data reveals positive growth trends across all major segments...

[Streamed content continues...]

Step 5: Connection closed
```

---

## Key Takeaways

1. **A2A enables true agent interoperability** across frameworks and languages
2. **AgentCard provides dynamic discovery** - no hardcoded endpoint knowledge needed
3. **Supports both request-response and streaming** patterns for different use cases
4. **Authentication is pluggable** - integrate your security requirements
5. **Scale horizontally** by running agent services independently
6. **Combine local and remote agents** in sophisticated orchestration workflows
