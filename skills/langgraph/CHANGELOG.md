# Changelog

All notable changes to the `langgraph` skill will be documented in this file.

## [1.0.0] — 2026-04-30

**Source version tracked:** langgraph 1.x (langgraph-prebuilt 1.0.13)

### Added

- `00-overview.md` — Framework overview, installation, quickstart, Graph vs Functional API comparison, ecosystem
- `01-graph-api.md` — StateGraph class, add_node, add_edge, conditional edges, compile, Send, Command, caching
- `02-state-management.md` — State schemas (TypedDict/dataclass/Pydantic), reducers, add_messages, MessagesState, I/O schemas
- `03-functional-api.md` — @entrypoint, @task decorators, execution methods, entrypoint.final, design rules
- `04-persistence-checkpointing.md` — Checkpointer backends (InMemory, SQLite, Postgres), thread management, time-travel, durable execution
- `05-memory.md` — Short-term vs long-term memory, BaseStore API, InMemoryStore, semantic/episodic/procedural memory types
- `06-streaming.md` — Stream modes (values, updates, messages, custom, debug), token streaming, v2 format, async patterns
- `07-human-in-the-loop.md` — interrupt() function, Command resume, static breakpoints, approval/review/validation patterns
- `08-tool-integration.md` — Tool definition, binding, ToolNode, routing, error handling, dynamic tool selection
- `09-prebuilt-agents.md` — create_react_agent, configuration, prompts, persistence, structured output, extension patterns
- `10-multi-agent.md` — Supervisor pattern, swarm pattern, handoff mechanisms, agent communication, hierarchical teams
- `11-subgraphs.md` — Subgraph composition, state mapping, cross-graph navigation, nested subgraphs, reusable modules
- `12-deployment.md` — LangGraph Platform, self-hosted FastAPI, LangSmith integration, testing, monitoring, performance

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,700
