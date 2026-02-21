# AG-UI Protocol — Agent User Interaction

## Overview

### What is AG-UI?
AG-UI is an open, lightweight, event-based protocol for agentic backend-to-frontend communication. It enables real-time, structured interaction between AI agents running on a backend and user interfaces (web, mobile, desktop), providing streaming responses, tool invocation feedback, and state synchronization.

### Standards and Philosophy
- **Event-driven architecture**: Real-time communication via Server-Sent Events (SSE)
- **Language agnostic**: HTTP-based, works with any frontend framework
- **Lightweight**: Minimal overhead, minimal bandwidth consumption
- **Interoperable**: Standard event format adopted across frameworks (React, Angular, iOS, Android, etc.)
- **Type-safe**: JSON schema validation for all event payloads

### Key Features
- **Response Streaming**: Real-time token-by-token or chunk-level responses
- **Tool Invocation Visibility**: See when tools are called, their arguments, and results
- **State Synchronization**: Track conversation history, thread management, message state
- **Error Propagation**: Structured error information with recovery suggestions
- **Progress Tracking**: Monitor long-running operations with progress indicators

### Core Concepts
1. **EventStream**: Continuous stream of typed events from agent to frontend
2. **Event Types**: response, tool, error, state, metadata events
3. **Conversation Context**: Thread IDs, message IDs, conversation state
4. **Tool Schema**: JSON schema describing tool parameters and return types
5. **State Synchronization**: Version-based state updates and conflict resolution

---

## FastAPI Integration

### Basic Setup

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agent_framework.ag_ui.fastapi import (
    add_agent_framework_fastapi_endpoint,
    AgUiConfig
)
from agent_framework.core import Agent

# Create your agent
agent = Agent(
    name="AssistantAgent",
    instructions="You are a helpful AI assistant."
)

# Create FastAPI app
app = FastAPI(title="Agent Service")

# Add AG-UI endpoint
add_agent_framework_fastapi_endpoint(
    app=app,
    agent=agent,
    path="/",  # Mounts at root or /api/chat
    config=AgUiConfig(
        stream_timeout=300,      # 5 minutes timeout
        max_message_length=4096,
        enable_streaming=True,
        cors_origins=["*"]
    )
)

# Run with: uvicorn app:app --reload
```

### Multi-Agent Setup

```python
from fastapi import FastAPI
from agent_framework.ag_ui.fastapi import add_agent_framework_fastapi_endpoint
from agent_framework.core import Agent

app = FastAPI(title="Multi-Agent Service")

# Create multiple specialized agents
research_agent = Agent(
    name="ResearchAgent",
    instructions="You are a research specialist..."
)

writing_agent = Agent(
    name="WritingAgent",
    instructions="You are a writing specialist..."
)

# Mount each at different paths
add_agent_framework_fastapi_endpoint(
    app=app,
    agent=research_agent,
    path="/api/research"
)

add_agent_framework_fastapi_endpoint(
    app=app,
    agent=writing_agent,
    path="/api/writing"
)
```

### With Database Persistence

```python
from fastapi import FastAPI
from agent_framework.ag_ui.fastapi import add_agent_framework_fastapi_endpoint
from agent_framework.core import Agent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up database
engine = create_engine("sqlite:///./agent.db")
SessionLocal = sessionmaker(bind=engine)

# Agent with conversation persistence
agent = Agent(
    name="PersistentAgent",
    instructions="Remember our conversation context."
)

app = FastAPI()

# Configure with database
config = {
    "database_url": "sqlite:///./agent.db",
    "persist_messages": True,
    "persist_state": True
}

add_agent_framework_fastapi_endpoint(
    app=app,
    agent=agent,
    path="/",
    config=config
)
```

---

## Event Types and Streaming Format

### Complete Event Type Reference

All events follow the structure:

```json
{
  "type": "event_type",
  "id": "evt_unique_id",
  "timestamp": "2024-01-15T10:30:45Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": { /* Type-specific payload */ }
}
```

### 1. response.started

Emitted when the agent begins generating a response.

```json
{
  "type": "response.started",
  "id": "evt_001",
  "timestamp": "2024-01-15T10:30:45Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "model": "claude-opus-4.6",
    "role": "assistant",
    "tokens": {
      "input_tokens": 250,
      "output_tokens_estimated": 500
    }
  }
}
```

**Python Example:**

```python
from agent_framework.ag_ui.events import ResponseStarted

event = ResponseStarted(
    conversation_id="conv_abc123",
    message_id="msg_def456",
    model="claude-opus-4.6",
    role="assistant"
)
```

### 2. response.delta

Emitted with each chunk of the response (token or phrase level).

```json
{
  "type": "response.delta",
  "id": "evt_002",
  "timestamp": "2024-01-15T10:30:46Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "delta": "The capital of France ",
    "index": 0,
    "finish_reason": null
  }
}
```

**Multiple deltas in sequence:**

```json
{ "type": "response.delta", "data": { "delta": "is" } }
{ "type": "response.delta", "data": { "delta": " Paris" } }
{ "type": "response.delta", "data": { "delta": "." } }
```

### 3. response.completed

Emitted when response generation finishes.

```json
{
  "type": "response.completed",
  "id": "evt_003",
  "timestamp": "2024-01-15T10:30:48Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "finish_reason": "stop",
    "tokens": {
      "input_tokens": 250,
      "output_tokens": 42
    },
    "full_response": "The capital of France is Paris.",
    "stop_reason": "natural"
  }
}
```

### 4. tool.started

Emitted when the agent begins invoking a tool.

```json
{
  "type": "tool.started",
  "id": "evt_004",
  "timestamp": "2024-01-15T10:30:49Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "tool_name": "search_web",
    "tool_call_id": "tool_xyz789",
    "description": "Search the web for information"
  }
}
```

### 5. tool.arguments

Emitted with each part of the tool's arguments (for streaming argument parsing).

```json
{
  "type": "tool.arguments",
  "id": "evt_005",
  "timestamp": "2024-01-15T10:30:50Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "tool_call_id": "tool_xyz789",
    "arguments_delta": "{\"query\": \"Paris tourism\"}",
    "arguments_index": 0,
    "argument_name": "query"
  }
}
```

### 6. tool.result

Emitted when a tool completes and returns a result.

```json
{
  "type": "tool.result",
  "id": "evt_006",
  "timestamp": "2024-01-15T10:30:55Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "tool_call_id": "tool_xyz789",
    "tool_name": "search_web",
    "result": {
      "results": [
        {
          "title": "Paris Tourism Guide",
          "url": "https://example.com/paris",
          "snippet": "Paris is the capital..."
        }
      ],
      "status": "success"
    },
    "duration_ms": 2500
  }
}
```

### 7. tool.end

Emitted when tool processing is finished (error or success).

```json
{
  "type": "tool.end",
  "id": "evt_007",
  "timestamp": "2024-01-15T10:30:56Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "tool_call_id": "tool_xyz789",
    "status": "completed",
    "total_duration_ms": 3000
  }
}
```

### 8. error

Emitted when an error occurs at any stage.

```json
{
  "type": "error",
  "id": "evt_008",
  "timestamp": "2024-01-15T10:31:00Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "error_code": "TOOL_EXECUTION_ERROR",
    "error_message": "search_web tool failed",
    "details": {
      "tool_name": "search_web",
      "reason": "Network timeout",
      "recovery_suggestions": [
        "Retry with a simpler query",
        "Try a different search tool",
        "Ask the agent to proceed without this tool"
      ]
    },
    "severity": "error"
  }
}
```

### 9. state.update

Emitted when conversation state changes.

```json
{
  "type": "state.update",
  "id": "evt_009",
  "timestamp": "2024-01-15T10:31:01Z",
  "conversationId": "conv_abc123",
  "messageId": "msg_def456",
  "data": {
    "state": {
      "messages": 5,
      "tools_used": ["search_web", "summarize"],
      "tokens_used": {
        "input": 500,
        "output": 200
      },
      "context_length": 700
    },
    "version": "2"
  }
}
```

### 10. metadata

Emitted with agent metadata and capability information.

```json
{
  "type": "metadata",
  "id": "evt_010",
  "timestamp": "2024-01-15T10:31:02Z",
  "conversationId": "conv_abc123",
  "data": {
    "agent_name": "AssistantAgent",
    "agent_version": "1.0.0",
    "model": "claude-opus-4.6",
    "available_tools": [
      {
        "name": "search_web",
        "description": "Search the web for information",
        "parameters": {
          "query": { "type": "string", "required": true }
        }
      }
    ],
    "capabilities": [
      "code_execution",
      "document_analysis",
      "web_search"
    ]
  }
}
```

---

## Python Event Types Reference

```python
from agent_framework.ag_ui.events import (
    ResponseStarted,
    ResponseDelta,
    ResponseCompleted,
    ToolStarted,
    ToolArguments,
    ToolResult,
    ToolEnd,
    ErrorEvent,
    StateUpdate,
    Metadata
)
from datetime import datetime
from typing import Optional, Dict, Any

# ResponseStarted
event = ResponseStarted(
    conversation_id="conv_123",
    message_id="msg_456",
    model="claude-opus-4.6",
    role="assistant"
)

# ResponseDelta
event = ResponseDelta(
    conversation_id="conv_123",
    message_id="msg_456",
    delta="Hello, ",
    index=0,
    finish_reason=None
)

# ResponseCompleted
event = ResponseCompleted(
    conversation_id="conv_123",
    message_id="msg_456",
    finish_reason="stop",
    full_response="Hello, how can I help?",
    tokens={"input_tokens": 100, "output_tokens": 10}
)

# ToolStarted
event = ToolStarted(
    conversation_id="conv_123",
    message_id="msg_456",
    tool_name="search_web",
    tool_call_id="tool_789"
)

# ToolResult
event = ToolResult(
    conversation_id="conv_123",
    message_id="msg_456",
    tool_call_id="tool_789",
    tool_name="search_web",
    result={"results": [...]},
    duration_ms=2500
)

# ErrorEvent
event = ErrorEvent(
    conversation_id="conv_123",
    message_id="msg_456",
    error_code="TOOL_EXECUTION_ERROR",
    error_message="Tool failed",
    severity="error"
)
```

---

## Frontend Compatibility

### React Integration

```javascript
import React, { useState, useEffect } from 'react';

function AgentChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (userMessage) => {
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    const conversationId = 'conv_' + Date.now();
    const messageId = 'msg_' + Date.now();

    const eventSource = new EventSource(
      `/api/chat?message=${encodeURIComponent(userMessage)}` +
      `&conversationId=${conversationId}` +
      `&messageId=${messageId}`
    );

    let currentMessage = '';

    eventSource.addEventListener('response.started', (event) => {
      const data = JSON.parse(event.data);
      console.log('Response started:', data);
      currentMessage = '';
    });

    eventSource.addEventListener('response.delta', (event) => {
      const data = JSON.parse(event.data);
      currentMessage += data.delta;
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: currentMessage }
      ]);
    });

    eventSource.addEventListener('response.completed', (event) => {
      const data = JSON.parse(event.data);
      console.log('Response completed:', data);
      setIsLoading(false);
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      const data = JSON.parse(event.data);
      console.error('Error:', data.error_message);
      setIsLoading(false);
      eventSource.close();
    });

    eventSource.addEventListener('tool.started', (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, {
        role: 'system',
        content: `Using tool: ${data.tool_name}`,
        type: 'tool'
      }]);
    });
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            sendMessage(input);
            setInput('');
          }
        }}
        placeholder="Type your message..."
      />
    </div>
  );
}

export default AgentChat;
```

### Angular Integration

```typescript
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: 'tool' | 'error';
}

@Component({
  selector: 'app-agent-chat',
  template: `
    <div class="chat-container">
      <div class="messages">
        <div *ngFor="let msg of messages" [class]="'message ' + msg.role">
          {{ msg.content }}
        </div>
      </div>
      <input
        [(ngModel)]="input"
        (keyup.enter)="sendMessage()"
        placeholder="Type your message..."
      />
    </div>
  `
})
export class AgentChatComponent implements OnInit {
  messages: AgentMessage[] = [];
  input: string = '';
  isLoading: boolean = false;

  constructor(private http: HttpClient) {}

  ngOnInit() {}

  sendMessage() {
    const userMessage = this.input;
    this.messages.push({ role: 'user', content: userMessage });
    this.input = '';
    this.isLoading = true;

    const conversationId = 'conv_' + Date.now();
    const messageId = 'msg_' + Date.now();

    const eventSource = new EventSource(
      `/api/chat?message=${encodeURIComponent(userMessage)}` +
      `&conversationId=${conversationId}` +
      `&messageId=${messageId}`
    );

    let currentMessage = '';

    eventSource.addEventListener('response.started', () => {
      currentMessage = '';
    });

    eventSource.addEventListener('response.delta', (event: any) => {
      const data = JSON.parse(event.data);
      currentMessage += data.delta;
      if (this.messages[this.messages.length - 1].role === 'assistant') {
        this.messages[this.messages.length - 1].content = currentMessage;
      } else {
        this.messages.push({ role: 'assistant', content: currentMessage });
      }
    });

    eventSource.addEventListener('response.completed', () => {
      this.isLoading = false;
      eventSource.close();
    });
  }
}
```

### Swift/iOS Integration

```swift
import Foundation
import Combine

class AgentChatViewModel: NSObject, ObservableObject, URLSessionEventParserDelegate {
    @Published var messages: [Message] = []
    @Published var isLoading = false

    private var eventParser: URLSessionEventParser?

    func sendMessage(_ text: String) {
        messages.append(Message(role: .user, content: text))
        isLoading = true

        let conversationId = "conv_" + UUID().uuidString
        let messageId = "msg_" + UUID().uuidString

        var request = URLRequest(
            url: URL(string: "http://api/chat?message=\(text.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")")!
        )
        request.setValue(conversationId, forHTTPHeaderField: "X-Conversation-ID")
        request.setValue(messageId, forHTTPHeaderField: "X-Message-ID")

        let session = URLSession.shared
        eventParser = URLSessionEventParser(request: request)

        eventParser?.onEvent = { [weak self] event in
            DispatchQueue.main.async {
                switch event.type {
                case "response.delta":
                    if let delta = event.data["delta"] as? String {
                        if self?.messages.last?.role == .assistant {
                            self?.messages[self?.messages.count ?? 0 - 1].content += delta
                        } else {
                            self?.messages.append(Message(role: .assistant, content: delta))
                        }
                    }
                case "response.completed":
                    self?.isLoading = false
                case "tool.started":
                    if let toolName = event.data["tool_name"] as? String {
                        self?.messages.append(Message(
                            role: .system,
                            content: "Using tool: \(toolName)",
                            type: .tool
                        ))
                    }
                default:
                    break
                }
            }
        }

        eventParser?.start()
    }
}
```

### Kotlin/Android Integration

```kotlin
import kotlinx.coroutines.*
import okhttp3.OkHttpClient
import okhttp3.Request

class AgentChatViewModel : ViewModel() {
    private val _messages = MutableLiveData<List<Message>>(emptyList())
    val messages: LiveData<List<Message>> = _messages

    private val client = OkHttpClient()

    fun sendMessage(text: String) {
        val currentMessages = _messages.value.orEmpty().toMutableList()
        currentMessages.add(Message(role = "user", content = text))
        _messages.value = currentMessages

        val conversationId = "conv_${UUID.randomUUID()}"
        val messageId = "msg_${UUID.randomUUID()}"

        viewModelScope.launch(Dispatchers.IO) {
            val request = Request.Builder()
                .url("http://api/chat?message=${text.urlEncode()}")
                .addHeader("X-Conversation-ID", conversationId)
                .addHeader("X-Message-ID", messageId)
                .build()

            val response = client.newCall(request).execute()
            val reader = response.body?.source()?.let { BufferedSource(it) }

            reader?.let {
                while (!it.exhausted()) {
                    val line = it.readUtf8Line() ?: break
                    if (line.startsWith("data:")) {
                        val json = JSONObject(line.substring(5))
                        when (json.getString("type")) {
                            "response.delta" -> {
                                val delta = json.getJSONObject("data").getString("delta")
                                val current = _messages.value.orEmpty().toMutableList()
                                if (current.isNotEmpty() && current.last().role == "assistant") {
                                    current[current.size - 1].content += delta
                                } else {
                                    current.add(Message(role = "assistant", content = delta))
                                }
                                _messages.postValue(current)
                            }
                        }
                    }
                }
            }
        }
    }
}
```

---

## State Synchronization

### Conversation Context Management

```python
from agent_framework.ag_ui.state import ConversationContext
from typing import List, Dict, Any

class ConversationManager:
    """Manages conversation state and history."""

    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}

    async def create_conversation(self) -> ConversationContext:
        """Create a new conversation."""
        context = ConversationContext(
            conversation_id=f"conv_{uuid.uuid4()}",
            thread_id=f"thread_{uuid.uuid4()}",
            messages=[],
            state={}
        )
        self.conversations[context.conversation_id] = context
        return context

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:
        """Add a message to conversation history."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        context = self.conversations[conversation_id]
        context.add_message(role=role, content=content)

    async def get_conversation(self, conversation_id: str) -> ConversationContext:
        """Retrieve conversation context."""
        return self.conversations.get(conversation_id)

    async def update_state(
        self,
        conversation_id: str,
        state_update: Dict[str, Any]
    ) -> None:
        """Update conversation state."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        context = self.conversations[conversation_id]
        context.update_state(state_update)
```

### Database Persistence

```python
from sqlalchemy import Column, String, JSON, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime

Base = declarative_base()

class ConversationRecord(Base):
    """Database model for conversation persistence."""

    __tablename__ = "conversations"

    conversation_id = Column(String, primary_key=True)
    thread_id = Column(String)
    messages = Column(JSON)  # Stores message history
    state = Column(JSON)     # Stores conversation state
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PersistenceManager:
    """Manages conversation persistence."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    def save_conversation(self, context: ConversationContext) -> None:
        """Save conversation to database."""
        with Session(self.engine) as session:
            record = ConversationRecord(
                conversation_id=context.conversation_id,
                thread_id=context.thread_id,
                messages=[m.dict() for m in context.messages],
                state=context.state
            )
            session.merge(record)
            session.commit()

    def load_conversation(self, conversation_id: str) -> ConversationContext:
        """Load conversation from database."""
        with Session(self.engine) as session:
            record = session.query(ConversationRecord).filter(
                ConversationRecord.conversation_id == conversation_id
            ).first()

            if not record:
                return None

            return ConversationContext(
                conversation_id=record.conversation_id,
                thread_id=record.thread_id,
                messages=record.messages,
                state=record.state
            )
```

### Thread Management

```python
from agent_framework.ag_ui.state import ThreadManager

class ThreadManager:
    """Manages conversation threads."""

    def __init__(self):
        self.threads: Dict[str, List[str]] = {}  # thread_id -> conversation_ids

    def create_thread(self) -> str:
        """Create a new thread."""
        thread_id = f"thread_{uuid.uuid4()}"
        self.threads[thread_id] = []
        return thread_id

    def add_conversation(self, thread_id: str, conversation_id: str) -> None:
        """Add conversation to thread."""
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")
        self.threads[thread_id].append(conversation_id)

    def get_thread_conversations(self, thread_id: str) -> List[str]:
        """Get all conversations in a thread."""
        return self.threads.get(thread_id, [])

    def get_thread_context(self, thread_id: str) -> Dict[str, Any]:
        """Get combined context from all conversations in thread."""
        conversation_ids = self.threads.get(thread_id, [])
        combined_state = {}

        for conv_id in conversation_ids:
            # Merge state from each conversation
            pass

        return combined_state
```

---

## When to Use AG-UI vs Alternatives

### AG-UI vs Plain REST API

| Aspect | AG-UI | REST API |
|--------|-------|----------|
| **Streaming** | Native SSE support | Polling/WebSocket needed |
| **Real-time Updates** | Built-in event stream | Manual implementation |
| **Tool Visibility** | Automatic tool invocation events | Must implement separately |
| **State Sync** | Version-based sync | Manual synchronization |
| **Framework Support** | Multiple language SDKs | Generic HTTP |
| **Complexity** | Moderate | Low (but more to implement) |
| **Latency** | Lower (streaming) | Higher (polling) |
| **Use Case** | Interactive agents | Simple API endpoints |

### AG-UI vs WebSocket

| Aspect | AG-UI | WebSocket |
|--------|-------|-----------|
| **Protocol** | HTTP/SSE | TCP persistent connection |
| **Bidirectional** | No (unidirectional) | Yes |
| **Simplicity** | Simpler setup | More complex |
| **Browser Support** | Universal | Good, but requires polyfill on IE |
| **Scalability** | Better (HTTP) | More resource-intensive |
| **Standard Events** | Typed events | Custom message format |
| **Use Case** | Agent responses | Interactive real-time apps |

### AG-UI vs A2A Protocol

| Aspect | AG-UI | A2A |
|--------|-------|-----|
| **Purpose** | Backend-to-frontend | Agent-to-agent |
| **Communication** | Streaming events | JSON-RPC calls |
| **Direction** | One-way (server→client) | Bidirectional |
| **Event Schema** | Standard typed events | Agent-specific |
| **Discovery** | Built-in metadata | AgentCard-based |
| **Use Case** | UI interaction | Agent orchestration |

---

## Complete Working Example

### Full End-to-End AG-UI Implementation

```python
# ============================================
# Part 1: Backend Agent Service
# ============================================

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from agent_framework.core import Agent
from agent_framework.ag_ui.fastapi import add_agent_framework_fastapi_endpoint
from agent_framework.ag_ui.events import (
    ResponseDelta,
    ResponseStarted,
    ResponseCompleted,
    ToolStarted,
    ToolResult
)
from typing import AsyncIterator
import json
import uuid

# Create agent
agent = Agent(
    name="ResearchAssistant",
    instructions="""You are a research assistant. You help users find and
    summarize information. You have access to web search and document analysis tools."""
)

# Add tools
def search_web(query: str) -> str:
    """Simulate web search."""
    results = [
        {"title": "Result 1", "url": "https://example.com/1", "snippet": "Sample result..."},
        {"title": "Result 2", "url": "https://example.com/2", "snippet": "Another result..."}
    ]
    return json.dumps(results)

def summarize_text(text: str) -> str:
    """Simulate text summarization."""
    return f"Summary of {len(text)} characters: The text discusses..."

agent.add_tool(
    name="search_web",
    description="Search the web for information",
    func=search_web,
    parameters={"query": {"type": "string", "required": True}}
)

agent.add_tool(
    name="summarize_text",
    description="Summarize a given text",
    func=summarize_text,
    parameters={"text": {"type": "string", "required": True}}
)

# Create FastAPI app
app = FastAPI(title="AG-UI Agent Service")

# Add AG-UI endpoint with streaming
async def event_generator(
    message: str,
    conversation_id: str,
    message_id: str
) -> AsyncIterator[str]:
    """Generate AG-UI events as the agent processes."""

    # 1. Emit response.started
    yield f"data: {json.dumps({
        'type': 'response.started',
        'id': f'evt_{uuid.uuid4()}',
        'conversationId': conversation_id,
        'messageId': message_id,
        'data': {
            'model': 'claude-opus-4.6',
            'role': 'assistant'
        }
    })}\n\n"

    # 2. Simulate tool invocation
    tool_call_id = f"tool_{uuid.uuid4()}"
    yield f"data: {json.dumps({
        'type': 'tool.started',
        'id': f'evt_{uuid.uuid4()}',
        'conversationId': conversation_id,
        'messageId': message_id,
        'data': {
            'tool_name': 'search_web',
            'tool_call_id': tool_call_id
        }
    })}\n\n"

    # 3. Emit tool result
    yield f"data: {json.dumps({
        'type': 'tool.result',
        'id': f'evt_{uuid.uuid4()}',
        'conversationId': conversation_id,
        'messageId': message_id,
        'data': {
            'tool_call_id': tool_call_id,
            'tool_name': 'search_web',
            'result': json.loads(search_web('AI research')),
            'duration_ms': 1500
        }
    })}\n\n"

    # 4. Stream response in deltas
    response_text = "Based on my search, here are the latest developments in AI research. "
    response_text += "The field is advancing rapidly with new models and applications emerging constantly."

    for chunk in response_text.split(' '):
        yield f"data: {json.dumps({
            'type': 'response.delta',
            'id': f'evt_{uuid.uuid4()}',
            'conversationId': conversation_id,
            'messageId': message_id,
            'data': {
                'delta': chunk + ' ',
                'index': 0,
                'finish_reason': None
            }
        })}\n\n"

    # 5. Emit response.completed
    yield f"data: {json.dumps({
        'type': 'response.completed',
        'id': f'evt_{uuid.uuid4()}',
        'conversationId': conversation_id,
        'messageId': message_id,
        'data': {
            'finish_reason': 'stop',
            'full_response': response_text,
            'tokens': {
                'input_tokens': 100,
                'output_tokens': len(response_text.split())
            }
        }
    })}\n\n"

@app.get("/api/chat")
async def chat(
    message: str = Query(...),
    conversation_id: str = Query(default_factory=lambda: f"conv_{uuid.uuid4()}"),
    message_id: str = Query(default_factory=lambda: f"msg_{uuid.uuid4()}")
):
    """Chat endpoint with AG-UI streaming."""
    return StreamingResponse(
        event_generator(message, conversation_id, message_id),
        media_type="text/event-stream"
    )

@app.get("/api/metadata")
async def get_metadata():
    """Return agent metadata."""
    return {
        "type": "metadata",
        "data": {
            "agent_name": agent.name,
            "agent_version": "1.0.0",
            "model": "claude-opus-4.6",
            "available_tools": [
                {
                    "name": "search_web",
                    "description": "Search the web for information",
                    "parameters": {"query": {"type": "string"}}
                },
                {
                    "name": "summarize_text",
                    "description": "Summarize text",
                    "parameters": {"text": {"type": "string"}}
                }
            ]
        }
    }

# ============================================
# Part 2: Frontend HTML/JavaScript
# ============================================

HTML_FRONTEND = """
<!DOCTYPE html>
<html>
<head>
    <title>AG-UI Agent Chat</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 0 auto; }
        .container { display: flex; flex-direction: column; height: 100vh; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; background: #f5f5f5; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #fff; }
        .tool { background: #fff3cd; color: #856404; font-size: 0.9em; }
        .input-area { display: flex; padding: 10px; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="messages" id="messages"></div>
        <div class="input-area">
            <input type="text" id="input" placeholder="Ask me something...">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        let conversationId = 'conv_' + Date.now();

        async function sendMessage() {
            const input = document.getElementById('input');
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            addMessage('user', message);

            const messageId = 'msg_' + Date.now();
            const eventSource = new EventSource(
                `/api/chat?message=${encodeURIComponent(message)}&conversationId=${conversationId}&messageId=${messageId}`
            );

            let currentMessage = '';

            eventSource.addEventListener('response.started', (e) => {
                const data = JSON.parse(e.data);
                console.log('Response started:', data);
                currentMessage = '';
            });

            eventSource.addEventListener('response.delta', (e) => {
                const data = JSON.parse(e.data);
                currentMessage += data.data.delta;

                const messagesDiv = document.getElementById('messages');
                if (messagesDiv.lastChild?.classList.contains('assistant')) {
                    messagesDiv.lastChild.textContent = currentMessage;
                } else {
                    addMessage('assistant', currentMessage);
                }
            });

            eventSource.addEventListener('tool.started', (e) => {
                const data = JSON.parse(e.data);
                addMessage('tool', `Using tool: ${data.data.tool_name}`);
            });

            eventSource.addEventListener('response.completed', (e) => {
                const data = JSON.parse(e.data);
                console.log('Response completed:', data);
                eventSource.close();
            });

            eventSource.addEventListener('error', (e) => {
                const data = JSON.parse(e.data);
                addMessage('error', `Error: ${data.data.error_message}`);
                eventSource.close();
            });
        }

        function addMessage(role, content) {
            const messagesDiv = document.getElementById('messages');
            const msg = document.createElement('div');
            msg.className = `message ${role}`;
            msg.textContent = content;
            messagesDiv.appendChild(msg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // Load agent metadata on startup
        fetch('/api/metadata')
            .then(r => r.json())
            .then(data => {
                console.log('Agent metadata:', data);
                const tools = data.data.available_tools.map(t => t.name).join(', ');
                addMessage('system', `Agent ready. Available tools: ${tools}`);
            });
    </script>
</body>
</html>
"""

# Serve the frontend
@app.get("/")
async def root():
    return HTML_FRONTEND

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the Example

```bash
# Install dependencies
pip install fastapi uvicorn python-agent-framework

# Run the server
python app.py

# Visit in browser
open http://localhost:8000
```

### Example Session Output

```
User: What are the latest AI breakthroughs?

[Response started...]
[Using tool: search_web]
[Tool result received: 2 search results]

Based on my search, here are the latest developments in AI research.
The field is advancing rapidly with new models and applications emerging constantly.

[Response completed]
```

---

## Key Takeaways

1. **AG-UI standardizes backend-to-frontend agent communication** with typed events
2. **Works across frameworks** - React, Angular, iOS, Android, and more
3. **Native streaming support** makes it perfect for real-time interactions
4. **Tool visibility** gives users insight into what the agent is doing
5. **State synchronization** enables persistent conversations and thread management
6. **Lightweight HTTP/SSE** makes it scalable and simple to implement
7. **Type-safe events** prevent protocol misunderstandings across frameworks
