# Issues Amendment — All Critical & High Findings

Resolved 2026-05-10. Every finding has been discussed and a decision reached. This document is the source of truth for the changes; apply them to each GitHub issue systematically.

---

## 1. New Issue: Protocol Spec (#0)

**Action**: Create issue #0 before any Phase 1 issue.

**Title**: WebSocket Protocol Specification — Events, RPC Methods, Types, Auth

**Body**: This issue defines the complete WebSocket protocol. All Phase 1–4 issues that send or receive WebSocket messages reference this issue instead of defining shapes inline.

Contents:
- **Auth contract**: login response shape, JWT payload fields, WebSocket auth message (`{"type": "auth", "token": "..."}`), response shapes (`auth_ok`, `auth_error`)
- **All event types** with TypeScript shapes and JSON examples:
  - `message.delta`, `message.completed`, `message.failed`
  - `tool.start`, `tool.progress`, `tool.complete`, `tool.error`
  - `approval.request`, `approval.response`
  - `terminal.output`, `terminal.completed`
  - `session.updated`, `session.summary`
  - `file.read`, `file.written`, `diff.created`
  - `error`
- **All RPC methods** with request/response shapes:
  - `session.list`, `session.get`, `session.search`, `session.timeline`
  - `prompt.submit`, `agent.interrupt`, `agent.redirect`
  - `approval.respond`
  - `terminal.exec`, `terminal.kill`, `terminal.list`, `terminal.history`
  - `filesystem.list`, `filesystem.read`, `filesystem.search`, `filesystem.diff`, `filesystem.touched`
- **Common error responses**: loading, empty, network failure, auth failure, timeout, server error
- **Shared TypeScript types**: `ToolCall`, `Session`, `ApprovalRequest`, `TimelineEvent`, `CommandRun`, `Artifact`, `SearchResult`

**All event IDs use UUID v4 strings.**

**No `Depends on` needed** — this is a reference document, not an implementation task. It should be created before any Gateway work starts.

---

## 2. Dependency Tracking — Every Issue

**Action**: Add a `Depends on: #N` line to every issue body. The dependency graph is:

```
#0 (Protocol Spec) — reference only, no impl dependency

Phase 0:
  #1 (Docker Compose) — Depends on: none
  #2 (Preferences API) — Depends on: none
  #3 (Audit log model) — Depends on: none
  #4 (SPA serving) — Depends on: none
  #14 (Login page) — MOVED TO PHASE 0. Depends on: #2, #3

Phase 1:
  #5 (Scaffold web_gateway) — Depends on: none
  #6 (WS server + JWT auth) — Depends on: #5
  #7 (Session streaming) — Depends on: #6
  #8 (Message submission) — Depends on: #7
  #9 (Tool trace events) — Depends on: #8
  #10 (Approval relay) — Depends on: #9
  #11 (/simulate, standalone) — Depends on: none (standalone utility)
  #12 (Terminal relay) — Depends on: #7
  #13 (File access) — Depends on: #6

Phase 2:
  #15 (Gateway connection manager) — Depends on: #6, #14
  #16 (Session list view) — Depends on: #7, #15
  #17 (Session timeline view) — Depends on: #7, #15
  #18 (Tool call card) — Depends on: #17
  #19 (Session info panel) — Depends on: #17
  #20 (Search UI) — Depends on: #7, #15
  #21 (Session export) — Depends on: #17

Phase 3:
  #22 (Composer) — Depends on: #8, #15
  #23 (Streaming renderer) — Depends on: #22
  #24 (Interrupt/redirect) — Depends on: #23
  #25 (Session lifecycle) — Depends on: #16
  #26 (Approval inbox) — Depends on: #10, #15

Phase 4:
  #27 (Terminal panel) — Depends on: #12, #15
  #28 (User PTY input) — Depends on: #27
  #29 (File browser) — Depends on: #13, #15
  #30 (Diff viewer) — Depends on: #29
  #31 (Context inspector) — Depends on: #7, #15
```

Add `**Depends on**: #N` as the first line after the title in every issue.

---

## 3. Issue Content Fixes

### #1 — Docker Compose production-ready
- Healthchecks: rewrite as "Reference best practice patterns" instead of hardcoded values
- Note that `restart: unless-stopped` already exists in the scaffolded compose

### #2 — Django preferences model
- **Remove** the broken example code block (missing quotes: `tags=[preferences]`, `theme: str = light`, `/preferences`)
- Replace with: "See Protocol Spec (#0) for API response shapes"
- Keep the rest of the issue body

### #4 — SPA serving
- Add a clear separation: "**Dev mode**: nginx reverse-proxies to Vite dev server for hot reload. **Prod mode**: Django serves compiled static files from `backend/static/`."
- Verification step for prod should check `http://localhost` (nginx), not `http://localhost:8000` (Django direct)

### #9 — Tool trace events
- Remove inline event schema definitions
- Replace with: "See Protocol Spec (#0) for event shapes"
- Keep the acceptance criteria (every tool emits start→complete|error, duration measured, exit code captured)

### #10 — Approval relay
- Add "**Depends on**: #9"
- Add approval logging mechanism: "Gateway POSTs decisions to Django `/api/auth/approvals/` asynchronously. If Django is down, queue in SQLite and retry with exponential backoff."
- Remove note about session ownership check (deferred)

### #11 — /simulate endpoint
- Rewrite as standalone utility: "A standalone script (no auth, no Hermes dependency) that opens a WebSocket and replays pre-recorded event sequences."
- New `Depends on`: none (was #6)
- Remove mention of authenticating "same as main"

### #13 — File system access
- Scope explicitly: "MVP: basic path traversal check only (resolved path must start with workspace root). Symlink detection, TOCTOU protection, and file size limits deferred to follow-up issue."
- No pagination for MVP (flat list, depth=unlimited)
- Add file size safeguard: "Log a warning if a file exceeds 100MB and skip reading it"

### #15 — Gateway connection manager
- Reconnection strategy: "Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (cap). Stop retrying after 5 minutes. Show 'Connection lost — refresh to reconnect' overlay."
- On auth failure: "Show error toast, clear JWT, redirect to /login"

### #17 — Session timeline view
- Fix: "5 components" (not 6). Remove the "6 component files" language.
- If unsure about the 6th, don't promise one. List exactly what's planned.

### #20 — Search UI
- Remove "Results in under 5 seconds" as a hard requirement. Replace with: "No hard timeout. Show a progress indicator. 5 seconds is a UX target — let the query run to completion."

### #23 — Streaming response renderer
- Replace "smooth, not chunk-by-chunk" with: "Render tokens via requestAnimationFrame (16ms update intervals). Tokens display as they arrive, individually if possible, batched only when more than 50 tokens arrive within a single frame."

---

## 4. Label Changes

**Action**: Remove `agent-ready` label from all issues. Keep only phase labels:
- `phase:0-infrastructure`
- `phase:1-gateway`
- `phase:2-vue-view`
- `phase:3-vue-control`
- `phase:4-vue-workspace`

---

## 5. Phase Reordering

**Action**: Move #14 (Login page) from Phase 2 to Phase 0. Place it after #3 (audit log) in the phase ordering.

New Phase 0 order: #1, #2, #3, #14, #4

This is because #14 has no dependency on the Gateway (only needs Django auth), and getting login working early unblocks all frontend development.

---

## 6. Architecture Confirmation

No changes needed. The existing split (Gateway = real-time streaming + temporary buffer, Django = auth/persistent storage/audit, client connects to both independently) is correct.

- Gateway's SQLite event replay buffer (last 1000 events per session or 24h) handles offline clients
- Approval audit logs flow Gateway → Django via async HTTP POST, independent of client connection state
- Client fetches audit history from Django on reconnect, live events from Gateway replay buffer
