# Hermes Web Client — Requirements Specification

## 1. Clarified User Goals

### Vision Statement

A web-based control plane for supervising a persistent Hermes agent. The client makes transparent what the agent is thinking about, what tools it's using, what files it's touching, what it wants permission to do, and what it remembers across sessions — all rendered as structured, inspectable events rather than flattened text messages.

### Core Positioning

> A Hermes-native control plane for supervising persistent agents across sessions, tools, skills, memory, terminal environments, and scheduled work.

The client is not a chatbot window. It is an observation deck, a permission panel, and a workspace browser wrapped around a running Hermes instance. The number-one differentiator from Hermes' existing Telegram interface is **tool trace visibility** — every tool call, its inputs, outputs, duration, effects, and risk level must be inspectable in the UI.

### Reference Codebase

`github.com/NousResearch/hermes-agent` — `main` branch. The web_gateway module uses the same underlying primitives as the existing TUI gateway: `AIAgent` (`run_agent.py`), `SessionStore` (`gateway/session.py`), `PlatformRegistry` (`gateway/platform_registry.py`), and the AIAgent callback system for event hooks.

### Key Design Decisions

| Dimension | Decision | Rationale |
|---|---|---|
| Builder role | Independent builder | Exploring the design space. Hermes-inspired but not constrained by upstream maintainership. |
| Primary platform | Web (Vue/Vite SPA) | Reach without install. Works on any device with a browser. |
| Backend | Django | Thin backend: authentication, user preferences, serving the SPA, approval audit log. |
| Hermes integration | Built-in web_gateway module | A Hermes module modeled on the TUI gateway's RPC method dispatch and event emission patterns, but over WebSocket with JWT auth. Configured in Hermes config. No separate process. |
| User model | Single user | No multi-tenancy. Auth exists only for security between components. |
| Development timeline | 6–9 months | Polished v1 with Phases 1–3 complete. All three components built by a solo developer. Realistic estimate after accounting for net-new Hermes features. |
| MVP scope | Phases 1–3 | View (observability) + Control (live agent interaction) + Workspace (terminal + files). |
| Testing philosophy | No mocks | Development and testing happen against a live Hermes+Gateway instance. |
| Disconnect behavior | Pause indefinitely | Hermes pauses actions requiring approval until the client reconnects. No auto-deny, no queueing — the user must decide. |

---

## 2. System Context

The system has three runtime components in two containers on the same machine. The architecture is component-separated to allow splitting onto separate machines later if needed.

**Container A: Hermes + web_gateway**
- A fork/branch of the Hermes repository with a new built-in web_gateway module
- Modeled on the TUI gateway's RPC method dispatch and event emission patterns
- Configured in Hermes config alongside other platform gateways
- Exposes a WebSocket server on a configurable port (internal to the Docker network)
- Has direct access to Hermes internals: session store, tool system, memory, filesystem workspace
- Validates WebSocket connections using JWT tokens signed by Django
- Provides direct filesystem read access to the Hermes workspace directory for the file browser feature

**Container B: Django Server**
- Serves the compiled Vue SPA as static files
- Provides authentication API (login, logout, JWT issuance) via RS256
- Stores user preferences (theme, notification settings, etc.)
- Stores approval audit log (who approved/denied what, when, and the action context)
- Does NOT handle Hermes interaction — it is not a middleman for agent communication
- A reverse proxy (e.g., nginx in a third container or on the host) terminates TLS and routes `/api/*` to Django and `/ws/*` to the web_gateway

**Browser (Vue SPA)**
- Single-page application built with Vue 3 + Vite + ecosystem plugins
- Connects to the single domain served by the reverse proxy (e.g., `https://hermes.myserver.com`)
- Django handles authentication and preferences under `/api/*`
- The reverse proxy routes WebSocket connections under `/ws/*` to the web_gateway
- From the browser's perspective, it talks to one origin — no CORS issues, no separate gateway domain
- Handles all Hermes interaction logic: event rendering, prompt submission, approval responses, terminal, file browsing

### Authentication Flow
1. User visits the single application URL (e.g., `https://hermes.myserver.com`)
2. Vue SPA renders a login form
3. User submits credentials to Django via `/api/auth/login`; Django authenticates and returns an RS256-signed JWT
4. Vue SPA stores the JWT
5. Vue SPA opens a WebSocket to `/ws` on the same origin; reverse proxy routes it to the web_gateway
6. Browser sends JWT as the first message or as a query parameter for authentication
7. Gateway validates the JWT against Django's public key
8. All subsequent Hermes events and commands flow through this WebSocket

---

## 3. Functional Requirements

### Phase 1 — Read-Only Observability (View)

The client surfaces what Hermes already stores, making it browsable and searchable.

**FR1. Session Browser**
- List all sessions with metadata: id, title, status, source platform, model, user id, timestamps (created, updated, started, ended), token counts (input/output/total), tags
- Sort by created date, updated date, duration, token usage
- Filter by status, source platform, tags, date range
- Full-text search across session titles and content
- Display session summary if available (auto-generated or user-written)
- Session list loads with 1000+ sessions in under 2 seconds

**FR2. Session Timeline**
- Render a session's full typed timeline of events (not just messages)
- Event types must include: user message, assistant message, message delta, tool start, tool progress, tool complete, tool error, approval request, approval response, file read, file write, diff, terminal command, artifact created, memory read, memory write, skill created/updated, model changed, session summary, error
- Each timeline event is addressable by `event_id` with session_id, run_id, parent_event_id, timestamp, source, and typed payload
- Tool calls render as collapsed cards: tool name, duration, exit code, status, summary
- Expanded tool call card (MVP scope) shows: full input, full output, error (if any), duration
- **Deferred to later phase**: risk level, files read/written, commands run, network domains, secrets accessed — these require extending Hermes' tool system to collect effect metadata
- Copy tool call input and output individually
- View token counts per message and cumulative per session
- View model used per message/run
- View system prompt snapshot

**FR3. Session Search**
- Full-text search across sessions, messages, and tool outputs
- Results show result type, title, snippet, session context, timestamp, relevance score
- Results return within 5 seconds for any query

**FR4. Session Export**
- Export a session as JSON, Markdown, or plain text
- Include full timeline with all event types

### Phase 2 — Live Agent Control (Control)

The client can initiate and manage agent conversations in real-time.

**FR5. Message Submission and Streaming**
- Submit a text prompt to a new or existing session
- Optionally specify model, attachments, or context references per prompt
- Stream assistant response tokens in real-time
- Stream tool start/progress/complete events in real-time — tool call cards appear and update as they happen
- Show structured tool call cards (not just text) during streaming
- Interrupt an active agent run (kills the current run)
- Redirect the agent with a follow-up instruction mid-stream

**FR6. Session Lifecycle Management**
- Resume a past session (load last N messages within the current model's token budget; the agent continues with available context)
- Fork a session (record a parent_session_id link — surface the relationship visually and allow the user to navigate between parent and child; full cloning is deferred to a later phase)
- Rename a session
- Archive a session
- View session parent/child relationships

**FR7. Approval Inbox**
- Receive approval requests in real-time via the WebSocket stream
- Display what Hermes provides: tool name, proposed action, explanation (MVP scope)
- Approval response options: Approve once, Deny once (MVP scope)
- Dedicated approval inbox view: pending, approved, denied requests
- Approval history per session and per event
- **Deferred to later phases**: risk level taxonomy, approval scoping (files/domains/commands), "Approve for session" and "Deny always" policies, Modify request, Ask for explanation

**FR8. Slash Commands**
- Slash command autocomplete in the composer
- Execute slash commands and display results as timeline events
- Support existing Hermes slash commands

### Phase 3 — Terminal and Workspace (Workspace)

The client exposes the Hermes workspace as a shared, browsable surface.

**FR9. Shared Terminal**
- The user gets access to a real PTY shell session in the Hermes workspace
- Agent-run commands appear with agent icon/indicator; user-run commands appear with user icon
- Visually distinct: agent commands vs. user commands
- Stream stdout and stderr in real-time per command
- Each command shows: id, actor (user/agent), command text, working directory, environment summary, start time, end time, exit code, stdout, stderr
- User can selectively share command outputs and errors with the agent (attach to context)
- Kill a running command
- View command history (scrollable)
- Copy command output

**FR10. File Browser**
- Browse the Hermes workspace directory tree
- Preview files: syntax-highlighted code, rendered Markdown, images
- Search files by name and content
- View files touched by a session (aggregated across all tool calls)
- View agent-generated diffs for files that were modified
- Show diff: before/after, per-file
- Pin files to the right-panel Context Inspector

**FR11. Context Inspector (right panel)**
- Show what is included in the current agent context:
  - Active memory entries (scope, key, summary, confidence)
  - Session summary
  - Pinned files
  - Recent terminal output
  - Referenced past sessions
- Show what is excluded (for user awareness)

---

## 4. Non-Functional Requirements

**NFR1. Real-time responsiveness.** Tool start events appear within 500ms of the agent invoking them. Streaming text renders as tokens arrive, not in chunks. WebSocket reconnection happens automatically within 3 seconds of disconnect.

**NFR2. Security.** JWT tokens issued by Django, verified by Gateway. All Hermes-bound commands require authentication. Approval decisions are logged to Django's audit table. No API keys or secrets are stored in the browser (JWTs only, short-lived). Gateway listens on a port that is not exposed to the public internet without auth.

**NFR3. Performance.**
- Session list (1000+ sessions) loads in under 2 seconds
- Session timeline (500+ events) renders in under 3 seconds
- Full-text search returns results within 5 seconds
- File tree for a workspace with 10,000+ files renders in under 3 seconds
- WebSocket reconnection after disconnect completes within 3 seconds

**NFR4. Graceful degradation.** If the Gateway WebSocket disconnects, the UI shows a clear disconnected state. Approved actions are paused and will resume on reconnect. Session browsing and search work from cached data.

**NFR5. Extensibility.** The Gateway event protocol is versioned and typed. New event types can be added without breaking existing Vue renderers. The UI renders unknown event types as a generic "event" card with raw JSON.

**NFR6. Accessibility.** The Vue SPA must be navigable by keyboard. Tool call cards, approval buttons, and timeline events have proper ARIA labels. Color is not the only differentiator for agent vs. user actions.

**NFR7. Browser compatibility.** Supports latest versions of Chrome, Firefox, Safari, and Edge.

---

## 5. User Stories & Acceptance Criteria

### Phase 1 — View

| ID | Story | Acceptance Criteria |
|---|---|---|
| US1 | As a user, I want to see all my Hermes sessions in one place so I can find the one I need. | Session list renders with title, status, model, date, and token counts. Sort, filter, and full-text search all work. 1000+ sessions load in under 2 seconds. |
| US2 | As a user, I want to open a session and replay every message and tool call so I understand what happened. | Full typed timeline renders. Tool calls are collapsed cards. Expanding shows input, output, duration, errors, risk level, effects. Event IDs are visible. |
| US3 | As a user, I want to search across all my sessions so I can find insights from past work. | Full-text search returns results with type, title, snippet, and session link. Results in under 5 seconds. |
| US4 | As a user, I want to see token usage per session so I can track costs. | Token counts shown per message and cumulative. Displayed in session list and session detail views. |

### Phase 2 — Control

| ID | Story | Acceptance Criteria |
|---|---|---|
| US5 | As a user, I want to start a new conversation and see the agent's response in real-time. | Type a message, submit, see tokens stream in. Tool calls appear as live cards with start/progress/complete. Interrupt button works mid-stream. |
| US6 | As a user, I want to resume a past session and continue where I left off. | Click a completed session, full timeline loads, composer is enabled. Submitting a message continues the session with full context. |
| US7 | As a user, I want to approve or deny risky agent actions before they execute. | Approval card appears with full details: tool, action, explanation, risk level, scope. Approve once/session, deny. Denied actions do not execute. History is logged. |
| US8 | As a user, I want to interrupt an agent that's going down the wrong path. | Interrupt button visible during active run. Clicking it stops the current run. Agent acknowledges. I can provide a redirect. |

### Phase 3 — Workspace

| ID | Story | Acceptance Criteria |
|---|---|---|
| US9 | As a user, I want to see the terminal output of commands the agent runs. | Agent commands appear in the terminal panel with stdout, stderr, exit code, and duration. Agent commands are visually distinguished from user commands. |
| US10 | As a user, I want to run my own commands in the same workspace. | Terminal input lets me type and execute commands. Output streams live. My commands are visually separate from the agent's. |
| US11 | As a user, I want to browse the workspace files the agent is working on. | File browser shows directory tree. Clicking a file opens a preview with syntax highlighting. Modified files show diffs. |
| US12 | As a user, I want to know what context the agent is using. | Context Inspector shows loaded memory, pinned files, recent terminal output, and referenced sessions. Updated in real-time as context changes. |

---

## 6. Resolved Design Decisions

### Gateway Architecture

The web_gateway is a new built-in module inside the Hermes repo (forked from `main` branch at `github.com/NousResearch/hermes-agent`). It is modeled on the TUI gateway's RPC method dispatch and event emission patterns, but purpose-built for WebSocket + JWT auth instead of stdio + local subprocess trust.

**Design**: A dedicated `web_gateway/` directory inside the Hermes codebase, structured similarly to `tui_gateway/` but purpose-built for:
- WebSocket server (not stdio)
- JWT authentication via RS256
- Structured event streaming (tool traces, approvals, files, diffs)
- Event replay buffer for reconnection (persisted to SQLite)

It uses the same underlying primitives as the TUI gateway (`AIAgent` from `run_agent.py`, `SessionStore` from `gateway/session.py`, and the AIAgent callback system for event hooks).

### Configuration Schema (`~/.hermes/config.yaml`)

```yaml
web_gateway:
  enabled: false
  port: 8765
  ws_path: "/ws"
  jwt_public_key: "/path/to/django_public_key.pem"
  tls:
    enabled: false
    cert_path: ""
    key_path: ""
  cors_allowed_origins:
    - "https://my-django-server.com"
  max_connections: 10
  heartbeat_interval: 30
  max_message_size: 10485760
  rate_limit: 100
  log_level: "info"
```

### Config Defaults

| Field | Default | Units / Notes |
|---|---|---|
| `enabled` | `false` | Must be explicitly set to `true` |
| `port` | `8765` | TCP port for the WebSocket server |
| `ws_path` | `"/ws"` | URL path for WebSocket connections |
| `jwt_public_key` | `""` | Path to Django's RSA public key PEM file |
| `tls.enabled` | `false` | When false, listens on plain WebSocket (use behind reverse proxy) |
| `tls.cert_path` | `""` | Path to TLS certificate file |
| `tls.key_path` | `""` | Path to TLS private key file |
| `cors_allowed_origins` | `[]` | List of allowed origins for browser WebSocket connections. Empty = all origins blocked |
| `max_connections` | `10` | Maximum concurrent WebSocket connections |
| `heartbeat_interval` | `30` | Seconds between WebSocket ping/pong heartbeats |
| `max_message_size` | `10485760` | Maximum WebSocket message size in bytes (10 MB) |
| `rate_limit` | `100` | Maximum messages per second per connection |
| `log_level` | `"info"` | One of: debug, info, warning, error |

### Security & Transport

- **Deployment topology**: Django and Hermes+web_gateway run in separate containers on the same machine. A reverse proxy (nginx/Caddy) terminates TLS and routes `/api/*` to Django and `/ws/*` to the web_gateway. From the browser's perspective, there is one origin — no CORS issues, no separate gateway domain.
- **TLS**: Gateway supports TLS natively (cert + key in config) for standalone deployments, OR sits behind a reverse proxy for shared TLS termination.
- **JWT**: RS256 — Django signs JWTs with its private key, Gateway validates with Django's public key. Industry standard for service-to-service trust. Kept even for single-user deployment because the implementation cost is modest and the security model is clean.
- **CORS**: Configurable allowed origins for browser WebSocket connections (empty by default — explicit opt-in required).

### Gateway Storage Model

The gateway is **stateless for persistence** (all session data lives in Hermes SQLite/JSONL) but maintains a **persistent event replay buffer** in a local SQLite table:

- Stores the last 1000 events per session (or last 24 hours, whichever is smaller)
- Auto-prunes old events
- Survives Gateway restarts
- Used to replay missed events when a client reconnects
- Does NOT replace Hermes' persistent storage — only provides continuity across WebSocket disconnects

### Phased Feature Delivery

Several requirements depend on Hermes internals that do not yet exist. These are deferred to later phases:

| Feature | MVP Scope | Future Phase |
|---|---|---|
| Tool effect metadata | Raw input, output, duration, exit code, error | Risk level, files read/written, commands run, network domains, secrets accessed |
| Session forking | Surface parent_session_id links, navigate between parent/child | Full session cloning (copy history + state) |
| Context resume | Load last N messages within token budget | Intelligent context budgeting and compression |
| Approval scoping | Simple yes/no per request | Risk level taxonomy, approval policies ("approve for session", "always deny this command"), scope enforcement |
| Tool call visual detail | Collapsed card: name, duration, status, exit code | Expanded card: risk level, effects, secrets, network domains |

### Message Handling

- **Unknown/unsupported message types**: Return a typed error response (gives the user visibility into what was rejected)
- **Reconnection behavior**: On reconnection, the Gateway replays the event buffer from SQLite AND sends a current state snapshot (active sessions, pending approvals, running agents)

### Shared Terminal Design

- User gets a real PTY shell session in the Hermes workspace
- User commands are NOT injected into the agent's tool loop by default
- User can selectively share command outputs and errors with the agent (attach to context)
- Agent commands and user commands are visually separated in the terminal history

### Scope Limitations

- **Single Hermes instance**: Out of scope for MVP. The client connects to one Hermes instance at a time.
- **Version coupling**: The web_gateway lives in the Hermes repo and ships with Hermes. Tight coupling is by design — no backward compatibility across Hermes versions for the internal gateway protocol.

