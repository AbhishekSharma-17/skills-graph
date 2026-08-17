# Retrieval & RAG

> Source: https://docs.langchain.com/oss/python/langchain/retrieval

## Table of Contents

- [Overview](#overview)
- [Document Loaders](#document-loaders)
- [Text Splitters](#text-splitters)
- [Embedding Models](#embedding-models)
- [Vector Stores](#vector-stores)
- [Retrievers](#retrievers)
- [RAG Patterns](#rag-patterns)
- [Indexing Pipeline](#indexing-pipeline)
- [Common Patterns](#common-patterns)

## Overview

Retrieval-Augmented Generation (RAG) addresses two LLM limitations: finite context windows and static training knowledge. LangChain provides the complete RAG pipeline as composable components: document loaders to ingest, text splitters to chunk, embeddings to vectorize, vector stores to index, and retrievers to search.

## Document Loaders

Document loaders ingest data from external sources and produce standardized `Document` objects with `page_content` and `metadata`.

### Common Loaders

```python
# Text files
from langchain_community.document_loaders import TextLoader
docs = TextLoader("data.txt").load()

# PDF
from langchain_community.document_loaders import PyPDFLoader
docs = PyPDFLoader("report.pdf").load()

# CSV
from langchain_community.document_loaders import CSVLoader
docs = CSVLoader("data.csv").load()

# Web pages
from langchain_community.document_loaders import WebBaseLoader
docs = WebBaseLoader("https://example.com/article").load()

# Markdown
from langchain_community.document_loaders import UnstructuredMarkdownLoader
docs = UnstructuredMarkdownLoader("README.md").load()

# Directory of files
from langchain_community.document_loaders import DirectoryLoader
docs = DirectoryLoader("./docs", glob="**/*.md").load()
```

### Lazy Loading

For large datasets, use lazy loading to avoid memory issues:

```python
loader = PyPDFLoader("large_report.pdf")
for doc in loader.lazy_load():
    process(doc)
```

### Document Object

```python
from langchain_core.documents import Document

doc = Document(
    page_content="LangChain is a framework for LLM apps.",
    metadata={"source": "docs.md", "page": 1}
)
```

### Available Loader Categories

| Category | Examples |
|----------|----------|
| Files | PDF, DOCX, CSV, JSON, HTML, Markdown, Excel |
| Web | URLs, sitemaps, RSS feeds |
| Databases | SQL, MongoDB, BigQuery |
| Cloud | S3, Google Drive, Notion, Confluence |
| Code | GitHub, GitLab repositories |
| Communication | Slack, Discord, email |

## Text Splitters

Break documents into smaller chunks for embedding and retrieval.

### RecursiveCharacterTextSplitter (Recommended)

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_documents(docs)
print(f"{len(docs)} docs → {len(chunks)} chunks")
```

### Token-Based Splitting

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-4o",
    chunk_size=500,
    chunk_overlap=50,
)
```

### Markdown Splitting

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
chunks = splitter.split_text(markdown_text)
```

### Code Splitting

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=1000,
    chunk_overlap=100,
)
chunks = splitter.split_documents(code_docs)
```

### Splitting Guidelines

| Parameter | Recommendation |
|-----------|---------------|
| `chunk_size` | 500-1500 chars (match embedding model's sweet spot) |
| `chunk_overlap` | 10-20% of chunk_size |
| `separators` | Use defaults unless domain-specific needs |

## Embedding Models

Transform text into numerical vectors for similarity search.

### OpenAI Embeddings

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector = embeddings.embed_query("What is LangChain?")
vectors = embeddings.embed_documents(["Doc 1", "Doc 2", "Doc 3"])
```

### Other Providers

```python
# Anthropic (via Voyage)
from langchain_voyageai import VoyageAIEmbeddings
embeddings = VoyageAIEmbeddings(model="voyage-3")

# Google
from langchain_google_genai import GoogleGenerativeAIEmbeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# HuggingFace (local)
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Ollama (local)
from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

### Caching Embeddings

```python
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

store = LocalFileStore("./embeddings_cache")
cached = CacheBackedEmbeddings.from_bytes_store(
    embeddings, store, namespace=embeddings.model
)
```

## Vector Stores

Store and search embeddings efficiently.

### FAISS (In-Memory)

```python
from langchain_community.vectorstores import FAISS

vectorstore = FAISS.from_documents(chunks, embeddings)

# Save and load
vectorstore.save_local("faiss_index")
loaded = FAISS.load_local("faiss_index", embeddings)
```

### Chroma (Persistent)

```python
from langchain_chroma import Chroma

vectorstore = Chroma.from_documents(
    chunks, embeddings,
    persist_directory="./chroma_db",
    collection_name="my_docs"
)
```

### Pinecone (Cloud)

```python
from langchain_pinecone import PineconeVectorStore

vectorstore = PineconeVectorStore.from_documents(
    chunks, embeddings,
    index_name="my-index"
)
```

### Similarity Search

```python
results = vectorstore.similarity_search("What is RAG?", k=4)
for doc in results:
    print(doc.page_content[:100])
    print(doc.metadata)

# With scores
results = vectorstore.similarity_search_with_score("What is RAG?", k=4)
for doc, score in results:
    print(f"Score: {score:.4f} — {doc.page_content[:80]}")
```

### Metadata Filtering

```python
results = vectorstore.similarity_search(
    "LangChain features",
    k=4,
    filter={"source": "docs.md"}
)
```

## Retrievers

Unified interface for document retrieval. Every vector store can be converted to a retriever.

### From Vector Store

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

docs = retriever.invoke("What is LangChain?")
```

### Search Types

```python
# Similarity (default)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

# MMR (Maximal Marginal Relevance) — diversity-aware
retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 20})

# Similarity with score threshold
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.5}
)
```

### Multi-Query Retriever

Generate multiple query variations for better recall:

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=ChatOpenAI(model="gpt-4o-mini")
)
```

### Contextual Compression

Re-rank and filter retrieved documents:

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(ChatOpenAI(model="gpt-4o-mini"))
retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever()
)
```

## RAG Patterns

### 2-Step RAG (Simple)

Retrieval always precedes generation. Predictable and high control.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer based on context:\n\n{context}"),
    ("human", "{question}")
])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | ChatOpenAI(model="gpt-4o")
    | StrOutputParser()
)

answer = rag_chain.invoke("What is LangChain?")
```

### Agentic RAG

Agent dynamically decides when to retrieve:

```python
from langchain.agents import create_agent
from langchain.tools.retriever import create_retriever_tool

retriever_tool = create_retriever_tool(
    retriever,
    "search_docs",
    "Search internal documentation for answers."
)

agent = create_agent(
    model="openai:gpt-4o",
    tools=[retriever_tool]
)
```

### Hybrid RAG

Combine keyword and semantic search:

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

bm25 = BM25Retriever.from_documents(chunks)
bm25.k = 4

semantic = vectorstore.as_retriever(search_kwargs={"k": 4})

ensemble = EnsembleRetriever(
    retrievers=[bm25, semantic],
    weights=[0.4, 0.6]
)
```

## Indexing Pipeline

Complete pipeline from raw data to searchable index:

```python
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 1. Load
loader = DirectoryLoader("./docs", glob="**/*.md")
docs = loader.load()

# 2. Split
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3. Embed and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(chunks, embeddings)

# 4. Retrieve
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
results = retriever.invoke("How do I use LangChain?")
```

## Common Patterns

### Add Sources to RAG Output

```python
from langchain_core.runnables import RunnablePassthrough

def format_docs_with_sources(docs):
    formatted = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        formatted.append(f"[{source}] {doc.page_content}")
    return "\n\n".join(formatted)

rag_chain = (
    {"context": retriever | format_docs_with_sources, "question": RunnablePassthrough()}
    | prompt
    | model
    | parser
)
```

### Incremental Indexing

```python
from langchain.indexes import SQLRecordManager, index

record_manager = SQLRecordManager("my_index", db_url="sqlite:///records.db")
record_manager.create_schema()

index(chunks, record_manager, vectorstore, cleanup="incremental")
```
