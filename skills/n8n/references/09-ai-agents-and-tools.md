# AI Agents and Tools

> Source: https://docs.n8n.io/build/integrate-ai/

## Table of Contents

- [AI in n8n Overview](#ai-in-n8n-overview)
- [AI Components](#ai-components)
- [Agents](#agents)
- [Chains](#chains)
- [Tools](#tools)
- [Memory](#memory)
- [Vector Stores and Embeddings](#vector-stores-and-embeddings)
- [Retrieval and RAG](#retrieval-and-rag)
- [Building AI Workflows](#building-ai-workflows)
- [Testing AI Workflows](#testing-ai-workflows)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## AI in n8n Overview

n8n provides native AI integration through specialized nodes for building agents, chains, and RAG pipelines — all within the visual workflow canvas. Connect to any LLM provider (OpenAI, Anthropic, Google, open-source models) without vendor lock-in.

### AI Node Categories

| Category | Purpose |
|----------|---------|
| **Agent** | Decision-making node that selects tools dynamically |
| **Chain** | Sequential LLM processing without tool selection |
| **LLM** | Language model connector (sub-node) |
| **Tool** | Capability the agent can invoke |
| **Memory** | Conversation history persistence |
| **Vector Store** | Similarity search over embedded documents |
| **Embeddings** | Text-to-vector conversion |
| **Retriever** | Fetch relevant context from vector stores |

## AI Components

n8n's AI system uses a modular, composable architecture. Components connect as **sub-nodes** to agents or chains:

```
Chat Trigger
  └── Agent
       ├── LLM (OpenAI, Anthropic, etc.)      ← Required
       ├── Tool 1 (HTTP Request)                ← Optional
       ├── Tool 2 (Code)                        ← Optional
       ├── Memory (Window Buffer)               ← Optional
       └── Retriever (Vector Store)             ← Optional
```

### Agents vs Chains

| Aspect | Agent | Chain |
|--------|-------|-------|
| **Decision making** | Dynamically chooses which tools to use | Follows predetermined sequence |
| **Tool calling** | Yes — selects from available tools | No — fixed pipeline |
| **Use case** | Open-ended questions, multi-step tasks | Simple summarization, classification |
| **Cost** | Higher (multiple LLM calls per execution) | Lower (single LLM call) |
| **Reliability** | Less predictable (LLM decides) | More predictable (fixed path) |

## Agents

An agent is a "chain that knows how to make decisions." It receives input, evaluates available tools, and decides which actions to take.

### Agent Node Configuration

```
Agent Type: Tools Agent (default)
System Message: "You are a helpful assistant that can look up customer data..."
Human Message: {{ $json.userMessage }}
Max Iterations: 10
Return Intermediate Steps: false
```

### Agent Types

| Type | Description |
|------|-------------|
| **Tools Agent** | Default agent using OpenAI-style function calling |
| **Conversational Agent** | Optimized for multi-turn chat with memory |
| **ReAct Agent** | Reasoning + Acting pattern (think → act → observe) |
| **SQL Agent** | Specialized for database queries |
| **Plan and Execute** | Plans steps first, then executes them |

### Agent Execution Cycle

```
1. Receive user input
2. LLM evaluates input and available tools
3. LLM selects a tool and generates arguments
4. Tool executes and returns result
5. LLM evaluates tool result
6. Repeat 3-5 if needed (up to max iterations)
7. LLM generates final response
```

## Chains

Chains process data through a fixed LLM pipeline without tool calling.

### Chain Types

| Chain | Purpose |
|-------|---------|
| **Basic LLM Chain** | Single prompt → response |
| **Summarization Chain** | Summarize long documents |
| **Information Extractor** | Extract structured data from text |
| **Text Classifier** | Classify text into categories |
| **Sentiment Analysis** | Analyze text sentiment |

### Basic LLM Chain Example

```
Chat Trigger
  └── Basic LLM Chain
       ├── LLM: OpenAI (gpt-4o)
       └── Prompt: "Summarize the following text: {{ $json.text }}"
```

## Tools

Tools are specialized capabilities that agents can invoke to interact with external resources.

### Built-In Tool Nodes

| Tool | Purpose |
|------|---------|
| **HTTP Request Tool** | Make API calls to any endpoint |
| **Code Tool** | Execute custom JavaScript/Python |
| **Call n8n Workflow Tool** | Run another n8n workflow |
| **Wikipedia Tool** | Search and retrieve Wikipedia content |
| **SerpAPI Tool** | Web search results |
| **Vector Store Tool** | Search embedded documents |
| **MCP Client Tool** | Call external MCP servers |

### HTTP Request as AI Tool

```
HTTP Request Tool (attached to Agent):
  Description: "Look up customer details by email"
  URL: https://api.crm.com/customers?email={{ $fromAI('email', 'Customer email') }}
  Method: GET
  Optimize Response: JSON
```

### Code Tool

```
Code Tool (attached to Agent):
  Description: "Calculate shipping cost based on weight and destination"
  
  JavaScript:
  const weight = parseFloat($fromAI('weight', 'Package weight in kg'));
  const dest = $fromAI('destination', 'Destination country code');
  const rate = dest === 'US' ? 5.0 : 15.0;
  return [{ json: { cost: weight * rate, currency: 'USD' } }];
```

### Workflow Tool

Convert any existing n8n workflow into an AI tool:

```
Call n8n Workflow Tool:
  Description: "Process a refund for an order"
  Workflow: "Process Refund" (select from list)
  → Agent sends data to the sub-workflow
  → Sub-workflow processes and returns result
  → Agent uses the result in its response
```

### The $fromAI() Function

Lets the AI agent dynamically fill in tool parameters:

```javascript
// Syntax
$fromAI('parameterName', 'Description for the LLM', 'expectedType')

// Examples
$fromAI('city', 'The city to get weather for', 'string')
$fromAI('quantity', 'Number of items to order', 'number')
$fromAI('userId', 'The user ID to look up')
```

## Memory

Memory nodes preserve conversation history across interactions.

### Memory Types

| Type | Behavior |
|------|----------|
| **Window Buffer Memory** | Keeps last N message pairs |
| **Token Buffer Memory** | Keeps messages up to a token limit |
| **Summary Memory** | Summarizes old messages to stay within limits |
| **Motorhead Memory** | External managed memory service |
| **Xata Memory** | Xata database-backed memory |
| **Postgres Memory** | PostgreSQL-backed chat memory |
| **Redis Memory** | Redis-backed chat memory |
| **Zep Memory** | Zep memory service integration |

### Window Buffer Memory Configuration

```
Context Window Length: 10
→ Keeps the last 10 message pairs (user + assistant)
→ Older messages are dropped
→ Session ID: {{ $json.sessionId }}
```

### Session Management

Each conversation needs a unique session ID to maintain separate histories:

```javascript
// Use a per-user or per-conversation session ID
Session ID: {{ $json.userId }}_{{ $json.conversationId }}
```

## Vector Stores and Embeddings

### Embeddings Nodes

Convert text into vector representations:

| Embeddings Node | Provider |
|----------------|----------|
| **OpenAI Embeddings** | text-embedding-3-small/large |
| **Azure OpenAI Embeddings** | Azure-hosted models |
| **Cohere Embeddings** | Cohere embed models |
| **Google Gemini Embeddings** | Gemini embedding models |
| **Ollama Embeddings** | Local open-source models |
| **Hugging Face Embeddings** | HF Inference API |
| **NVIDIA Nemotron Embeddings** | NeMo Retriever models |

### Vector Store Nodes

Store and search embedded documents:

| Vector Store | Backend |
|-------------|---------|
| **Pinecone** | Pinecone managed service |
| **Qdrant** | Qdrant vector database |
| **Supabase** | Supabase pgvector |
| **PGVector** | PostgreSQL pgvector |
| **Chroma** | Chroma vector database |
| **Milvus/Zilliz** | Milvus vector database |
| **In-Memory** | Ephemeral (lost on restart) |

### Indexing Documents

```
Read Files (from Google Drive/S3)
  → Text Splitter (chunk documents)
  → Embeddings (convert to vectors)
  → Vector Store (store for search)
```

## Retrieval and RAG

### Retrieval-Augmented Generation

Combine vector search with LLM generation:

```
Chat Trigger
  └── Agent
       ├── LLM: OpenAI
       ├── Memory: Window Buffer
       └── Retriever: Vector Store Retriever
            ├── Vector Store: Pinecone
            └── Embeddings: OpenAI
```

### Retriever Configuration

```
Vector Store Retriever:
  Top K: 4                  # Number of relevant documents to retrieve
  Metadata Filter: {}       # Optional filtering by metadata
  → Feeds relevant context to the LLM prompt
```

### Context Retrieval Flow

```
1. User asks a question
2. Question is embedded using the Embeddings node
3. Vector Store searches for similar document chunks
4. Top K results are injected into the LLM prompt
5. LLM generates answer grounded in retrieved context
```

## Building AI Workflows

### Chat Interface

```
Chat Trigger (opens n8n chat widget)
  → Agent
       ├── LLM: OpenAI GPT-4o
       ├── Memory: Window Buffer (10 messages)
       └── Tools: [HTTP Request, Code, Workflow]
```

### API-Triggered AI

```
Webhook (POST /api/chat)
  → Agent
       ├── LLM: Anthropic Claude
       └── Tools: [Database Query, Email Sender]
  → Respond to Webhook (agent's response)
```

### Document Q&A

```
Schedule Trigger (daily at midnight)
  → Google Drive (download new files)
  → Text Splitter (chunk into paragraphs)
  → Embeddings (OpenAI text-embedding-3-small)
  → Pinecone Vector Store (upsert)

Chat Trigger
  → Agent
       ├── LLM: GPT-4o
       └── Retriever: Pinecone
```

## Testing AI Workflows

### Quick Evaluation

Use the built-in evaluation framework:

```
Evaluation Trigger (test dataset)
  → Agent under test
  → Evaluation node (compare output vs expected)
  → Metrics: accuracy, faithfulness, relevancy
```

### Evaluation Metrics

| Metric | Measures |
|--------|----------|
| **Accuracy** | Correct answers vs expected |
| **Faithfulness** | Answers grounded in provided context |
| **Relevancy** | Answers relevant to the question |
| **Completeness** | All aspects of the question addressed |

## Common Patterns

### Customer Support Agent

```
Chat Trigger
  → Agent (system: "You are a customer support agent for Acme Corp")
       ├── LLM: GPT-4o
       ├── Memory: Window Buffer
       ├── Tool: Search Knowledge Base (vector store)
       ├── Tool: Look Up Order (HTTP Request to CRM)
       └── Tool: Create Ticket (Workflow → Jira)
```

### Data Extraction Pipeline

```
Webhook (receives document URL)
  → HTTP Request (download document)
  → Information Extractor Chain
       └── LLM: GPT-4o
  → Edit Fields (structure extracted data)
  → Google Sheets (save results)
  → Respond to Webhook
```

## Common Pitfalls

- **Agent loops** — set a reasonable `Max Iterations` (5-10) to prevent infinite tool-calling cycles
- **Token costs** — agents make multiple LLM calls per execution; monitor usage and set budget alerts
- **Tool descriptions matter** — clear, specific tool descriptions help the LLM choose the right tool
- **Memory limits** — unbounded memory fills the context window; use window or token buffer limits
- **Vector store stale data** — schedule regular re-indexing when source documents change
- **Streaming vs non-streaming** — streaming responses require compatible trigger nodes (Chat Trigger)
- **$fromAI() in non-AI context** — this function only works in tool sub-nodes attached to an agent

## Related Topics

- HTTP Request → `06-http-request-and-apis.md`
- Code Node → `05-code-node.md`
- Workflow Management → `11-workflow-management.md`
