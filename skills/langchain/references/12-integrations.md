# Integrations

> Source: https://docs.langchain.com/oss/python/integrations

## Table of Contents

- [Overview](#overview)
- [Chat Model Providers](#chat-model-providers)
- [Embedding Providers](#embedding-providers)
- [Vector Store Integrations](#vector-store-integrations)
- [Document Loader Integrations](#document-loader-integrations)
- [Tool Integrations](#tool-integrations)
- [Community Packages](#community-packages)
- [Model Profiles](#model-profiles)
- [Installation Patterns](#installation-patterns)

## Overview

LangChain integrations are organized into three tiers:

1. **First-party packages** (`langchain-openai`, `langchain-anthropic`) — Maintained by LangChain, high quality
2. **Partner packages** (`langchain-pinecone`, `langchain-chroma`) — Co-maintained with providers
3. **Community package** (`langchain-community`) — Community-contributed, broader coverage

## Chat Model Providers

### OpenAI

```bash
pip install langchain-openai
```

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")
model = ChatOpenAI(model="gpt-4o-mini")
model = ChatOpenAI(model="o1")
```

### Anthropic

```bash
pip install langchain-anthropic
```

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-6")
model = ChatAnthropic(model="claude-haiku-4-5")

# With extended thinking
model = ChatAnthropic(
    model="claude-sonnet-4-6",
    thinking={"type": "enabled", "budget_tokens": 5000}
)
```

### Google Generative AI

```bash
pip install langchain-google-genai
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI

model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
model = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
```

### Azure OpenAI

```bash
pip install langchain-openai
```

```python
from langchain_openai import AzureChatOpenAI

model = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2024-08-01-preview",
    azure_endpoint="https://my-resource.openai.azure.com/",
)
```

### AWS Bedrock

```bash
pip install langchain-aws
```

```python
from langchain_aws import ChatBedrock

model = ChatBedrock(
    model_id="anthropic.claude-sonnet-4-6-20250514-v1:0",
    region_name="us-east-1",
)
```

### Ollama (Local)

```bash
pip install langchain-ollama
```

```python
from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.2")
model = ChatOllama(model="mistral")
```

### OpenRouter

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="anthropic/claude-sonnet-4-6",
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-..."
)
```

### HuggingFace

```bash
pip install langchain-huggingface
```

```python
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

llm = HuggingFaceEndpoint(repo_id="meta-llama/Llama-3.2-3B-Instruct")
model = ChatHuggingFace(llm=llm)
```

## Embedding Providers

| Provider | Package | Model |
|----------|---------|-------|
| OpenAI | `langchain-openai` | text-embedding-3-small, text-embedding-3-large |
| Google | `langchain-google-genai` | text-embedding-004 |
| Voyage AI | `langchain-voyageai` | voyage-3, voyage-3-lite |
| HuggingFace | `langchain-huggingface` | all-MiniLM-L6-v2, bge-base-en |
| Ollama | `langchain-ollama` | nomic-embed-text, mxbai-embed-large |
| Cohere | `langchain-cohere` | embed-english-v3.0 |
| AWS Bedrock | `langchain-aws` | Via Bedrock |

```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

## Vector Store Integrations

| Store | Package | Type |
|-------|---------|------|
| FAISS | `langchain-community` + `faiss-cpu` | In-memory / local |
| Chroma | `langchain-chroma` | Local / persistent |
| Pinecone | `langchain-pinecone` | Cloud |
| Qdrant | `langchain-qdrant` | Cloud / self-hosted |
| Weaviate | `langchain-weaviate` | Cloud / self-hosted |
| Milvus | `langchain-milvus` | Cloud / self-hosted |
| PGVector | `langchain-postgres` | PostgreSQL extension |
| Supabase | `langchain-community` | Cloud (Postgres-based) |

```python
# FAISS
from langchain_community.vectorstores import FAISS
vs = FAISS.from_documents(docs, embeddings)

# Chroma
from langchain_chroma import Chroma
vs = Chroma.from_documents(docs, embeddings, persist_directory="./db")

# Pinecone
from langchain_pinecone import PineconeVectorStore
vs = PineconeVectorStore.from_documents(docs, embeddings, index_name="idx")
```

## Document Loader Integrations

### File Formats

| Format | Loader | Package |
|--------|--------|---------|
| PDF | `PyPDFLoader` | `langchain-community` + `pypdf` |
| DOCX | `Docx2txtLoader` | `langchain-community` + `docx2txt` |
| CSV | `CSVLoader` | `langchain-community` |
| JSON | `JSONLoader` | `langchain-community` + `jq` |
| HTML | `BSHTMLLoader` | `langchain-community` + `beautifulsoup4` |
| Markdown | `UnstructuredMarkdownLoader` | `langchain-community` |
| Excel | `UnstructuredExcelLoader` | `langchain-community` |

### Cloud Sources

| Source | Loader |
|--------|--------|
| Google Drive | `GoogleDriveLoader` |
| Notion | `NotionDBLoader` |
| Confluence | `ConfluenceLoader` |
| GitHub | `GithubFileLoader` |
| S3 | `S3FileLoader` |
| Slack | `SlackDirectoryLoader` |
| YouTube | `YoutubeLoader` |

### Web Sources

| Source | Loader |
|--------|--------|
| Web pages | `WebBaseLoader` |
| Sitemap | `SitemapLoader` |
| RSS | `RSSFeedLoader` |
| Wikipedia | `WikipediaLoader` |
| ArXiv | `ArxivLoader` |

## Tool Integrations

### Built-in Tools

```python
from langchain_community.tools import DuckDuckGoSearchRun
search = DuckDuckGoSearchRun()

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
```

### Retriever as Tool

```python
from langchain.tools.retriever import create_retriever_tool

tool = create_retriever_tool(
    retriever,
    name="search_docs",
    description="Search internal documentation"
)
```

### Custom API Tools

```python
from langchain.tools import tool
import httpx

@tool
async def fetch_api(endpoint: str) -> str:
    """Fetch data from the internal API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/{endpoint}")
        return response.text
```

## Model Profiles

Since v1.1.0, LangChain reads model capability metadata dynamically:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o", model_provider="openai")
profile = model.model_profile

print(profile.max_input_tokens)
print(profile.supports_tool_calling)
print(profile.supports_structured_output)
print(profile.supports_multimodal_input)
print(profile.supports_reasoning)
```

This enables auto-selection of structured output strategy and feature availability checks.

## Installation Patterns

### Minimal (Single Provider)

```bash
pip install langchain langchain-openai
```

### Full RAG Stack

```bash
pip install langchain langchain-openai langchain-community faiss-cpu langchain-text-splitters
```

### Multi-Provider

```bash
pip install langchain langchain-openai langchain-anthropic langchain-google-genai
```

### Production Agent

```bash
pip install langchain langchain-openai langgraph langsmith
```

### With Extras

```bash
pip install "langchain[openai,anthropic]"
```

### Version Pinning

```bash
pip install "langchain>=1.3,<2.0" "langchain-openai>=0.3"
```
