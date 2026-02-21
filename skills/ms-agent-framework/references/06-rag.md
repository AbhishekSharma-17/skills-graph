# RAG — Retrieval-Augmented Generation Agents

## Overview

RAG agents enhance LLM responses with retrieved knowledge. Microsoft Agent Framework supports RAG through:

1. **File Search tool** — Built-in vector search over uploaded files
2. **Azure AI Search tool** — Enterprise search over indexed data
3. **Custom RAG via Context Providers** — Your own retrieval pipeline
4. **Custom RAG via Function Tools** — Search as a tool the agent calls

## File Search RAG (Built-in)

The simplest RAG approach — upload files and let the framework handle indexing/retrieval:

```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

async with AzureAIAgentClient(
    async_credential=DefaultAzureCredential(),
) as client:
    agent = client.as_agent(
        name="KnowledgeAgent",
        instructions="""You are a helpful assistant.
        Use file search to find relevant information before answering.
        Always cite the source document.""",
        tools=["file_search"],
    )

    result = await agent.run("What does the Q4 report say about revenue growth?")
    print(result.text)
```

**Supported file types:** PDF, DOCX, TXT, MD, CSV, JSON, PPTX, XLSX, HTML

## Azure AI Search RAG

Enterprise-grade retrieval over your own search indexes:

```python
agent = foundry_client.as_agent(
    name="EnterpriseRAG",
    instructions="""Answer questions using the company knowledge base.
    If you can't find relevant information, say so.""",
    tools=[{
        "type": "azure_ai_search",
        "azure_ai_search": {
            "index_name": "company-policies",
            "endpoint": os.environ["AZURE_SEARCH_ENDPOINT"],
            "api_key": os.environ["AZURE_SEARCH_KEY"],
        }
    }],
)

result = await agent.run("What is the remote work policy?")
```

## Custom RAG via Context Providers

Inject retrieved context into every agent turn automatically:

```python
from agent_framework import BaseContextProvider, AgentSession

class VectorSearchProvider(BaseContextProvider):
    """Retrieves relevant documents and injects them as context."""

    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def get_context(self, session: AgentSession, **kwargs) -> str:
        # Get the latest user message
        last_msg = session.messages[-1].text if session.messages else ""
        if not last_msg:
            return ""

        # Search vector store
        results = await self.vector_store.search(last_msg, top_k=5)

        if not results:
            return "No relevant documents found."

        context = "Relevant documents:\n"
        for i, doc in enumerate(results, 1):
            context += f"\n[{i}] {doc.title} (score: {doc.score:.2f}):\n{doc.content}\n"

        return context

# Use with agent
agent = client.as_agent(
    name="RAGAgent",
    instructions="""Answer questions using the provided documents.
    Always cite document numbers [1], [2], etc.""",
    context_providers=[VectorSearchProvider(my_vector_store)],
)
```

**How it works:** Context providers run before each LLM call. The returned text is prepended to the conversation, so the LLM sees the retrieved documents as context.

## Custom RAG via Function Tools

Let the agent decide when to search (more flexible):

```python
from agent_framework import tool
from typing import Annotated

@tool
async def search_knowledge_base(
    query: Annotated[str, "Search query for the knowledge base"],
    max_results: Annotated[int, "Maximum results to return"] = 5,
) -> str:
    """Search the company knowledge base for relevant information."""
    results = await vector_store.search(query, top_k=max_results)

    if not results:
        return "No results found."

    output = []
    for i, doc in enumerate(results, 1):
        output.append(f"[{i}] {doc.title}: {doc.content[:500]}")

    return "\n\n".join(output)

agent = client.as_agent(
    name="SmartRAG",
    instructions="""You are a helpful assistant with access to a knowledge base.
    Search the knowledge base when you need specific information.
    Always cite your sources.""",
    tools=[search_knowledge_base],
)
```

**Key difference:** With function tools, the agent chooses when to search. With context providers, search happens every turn automatically.

## RAG Best Practices

| Practice | Why |
|---|---|
| Use context providers for always-needed context | Automatic, no LLM decision needed |
| Use function tools for optional search | Agent decides when to search |
| Limit retrieved chunks to ~5 | Avoid overwhelming the context window |
| Include relevance scores | Helps LLM assess reliability |
| Add source citations in instructions | Agent cites sources in responses |
| Use hybrid search (vector + keyword) | Better retrieval quality |
| Chunk documents at 500-1000 tokens | Optimal retrieval granularity |

## Choosing a RAG Approach

| Approach | Best For | Complexity |
|---|---|:-:|
| **File Search (built-in)** | Quick setup, small doc sets | Low |
| **Azure AI Search** | Enterprise, large doc sets | Medium |
| **Context Provider** | Always-on retrieval, custom pipelines | Medium |
| **Function Tool** | On-demand search, agent-driven | Medium |
| **Combined** | Complex requirements | High |
