# Hosted & Built-in Tools — MCP, Code Interpreter, File Search, Bing, Azure AI Search

## Overview of Tool Types

| Tool Type | Description | Provider Support |
|---|---|---|
| **Function Tools** | Custom Python functions with `@tool` | All providers |
| **Hosted MCP Tools** | Remote MCP servers (Azure-hosted) | Azure OpenAI, Azure AI Foundry |
| **Code Interpreter** | Execute Python code in sandbox | Azure OpenAI, OpenAI, Foundry |
| **File Search** | Search uploaded files/vectors | Azure OpenAI, OpenAI, Foundry |
| **Bing Grounding** | Web search via Bing | Azure AI Foundry |
| **Azure AI Search** | Enterprise search over your data | Azure AI Foundry |
| **OpenAPI Tools** | Auto-generated tools from OpenAPI spec | Azure AI Foundry |

## Hosted MCP Tools

Model Context Protocol (MCP) servers hosted by Azure AI Foundry. The agent calls them like any other tool.

```python
from agent_framework.azure import AzureOpenAIResponsesClient

agent = client.as_agent(
    name="MCPAgent",
    instructions="You can search the web and analyze files.",
    mcp_servers=[
        "web-search",       # Hosted web search MCP
        "file-search",      # Hosted file search MCP
    ],
)

result = await agent.run("Search the web for latest Python news")
```

### Available Hosted MCP Servers

| Server | Description | How to Add |
|---|---|---|
| `web-search` | Bing-powered web search | `mcp_servers=["web-search"]` |
| `file-search` | Search project files | `mcp_servers=["file-search"]` |

### Local MCP Servers

Connect to locally running MCP servers:

```python
from agent_framework import MCPServerTool

# stdio-based MCP server
mcp_tool = MCPServerTool(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
)

agent = client.as_agent(
    name="FileBrowser",
    tools=[mcp_tool],
)
```

## Code Interpreter

Runs Python code in a sandboxed environment. Useful for math, data analysis, chart generation.

```python
from agent_framework.azure import AzureOpenAIResponsesClient

# Code interpreter is enabled via the provider
agent = client.as_agent(
    name="DataAnalyst",
    instructions="You are a data analyst. Use code interpreter to analyze data.",
    tools=["code_interpreter"],  # Enable code interpreter
)

result = await agent.run("Calculate the first 20 Fibonacci numbers")
```

### With Azure AI Foundry

```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

async with AzureAIAgentClient(
    async_credential=DefaultAzureCredential(),
) as foundry_client:
    agent = foundry_client.as_agent(
        name="Analyst",
        instructions="Use code interpreter for calculations.",
        tools=["code_interpreter"],
    )
    result = await agent.run("Plot a sine wave and save as PNG")
```

## File Search

Search over uploaded files using vector embeddings.

```python
# Azure AI Foundry file search
agent = client.as_agent(
    name="DocSearcher",
    instructions="Search uploaded documents to answer questions.",
    tools=["file_search"],
)

# Upload files for the agent to search
# Files are indexed and searchable via vector similarity
result = await agent.run("What does the Q4 report say about revenue?")
```

## Bing Grounding

Web search grounding — agent can search the web for current information.

```python
from agent_framework.azure import AzureAIAgentClient

agent = foundry_client.as_agent(
    name="WebResearcher",
    instructions="Use Bing search to find current information.",
    tools=["bing_grounding"],
)

result = await agent.run("What are today's top tech news stories?")
```

**Requires:** Azure AI Foundry with Bing grounding resource configured.

## Azure AI Search

Enterprise search over your indexed data (documents, databases, etc.).

```python
from agent_framework.azure import AzureAIAgentClient

agent = foundry_client.as_agent(
    name="EnterpriseSearcher",
    instructions="Search company knowledge base to answer questions.",
    tools=[{
        "type": "azure_ai_search",
        "azure_ai_search": {
            "index_name": "company-docs",
            "endpoint": os.environ["AZURE_SEARCH_ENDPOINT"],
            "api_key": os.environ["AZURE_SEARCH_KEY"],
        }
    }],
)

result = await agent.run("What is our company's parental leave policy?")
```

## OpenAPI Tools

Auto-generate tools from an OpenAPI specification:

```python
agent = foundry_client.as_agent(
    name="APIAgent",
    instructions="Use the API to manage tickets.",
    tools=[{
        "type": "openapi",
        "openapi": {
            "name": "ticketing_api",
            "description": "Ticketing system API",
            "spec_url": "https://api.example.com/openapi.json",
            "auth": {
                "type": "bearer",
                "token": os.environ["API_TOKEN"],
            }
        }
    }],
)
```

## Combining Multiple Tool Types

```python
from agent_framework import tool
from typing import Annotated

@tool
def calculate_discount(
    price: Annotated[float, "Original price"],
    percent: Annotated[float, "Discount percentage"],
) -> str:
    """Calculate discounted price."""
    return f"Discounted price: ${price * (1 - percent/100):.2f}"

agent = client.as_agent(
    name="ShoppingAssistant",
    instructions="Help users shop. Search web for products, calculate discounts.",
    tools=[
        calculate_discount,          # Function tool
        "code_interpreter",          # Built-in tool
    ],
    mcp_servers=["web-search"],      # Hosted MCP tool
)
```

## Tool Provider Compatibility Matrix

| Tool | Azure OpenAI Responses | OpenAI Responses | Azure AI Foundry | Anthropic | Ollama |
|---|:-:|:-:|:-:|:-:|:-:|
| Function `@tool` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Hosted MCP | ✅ | ❌ | ✅ | ❌ | ❌ |
| Code Interpreter | ✅ | ✅ | ✅ | ❌ | ❌ |
| File Search | ✅ | ✅ | ✅ | ❌ | ❌ |
| Bing Grounding | ❌ | ❌ | ✅ | ❌ | ❌ |
| Azure AI Search | ❌ | ❌ | ✅ | ❌ | ❌ |
| OpenAPI | ❌ | ❌ | ✅ | ❌ | ❌ |
