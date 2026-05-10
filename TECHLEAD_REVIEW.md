# Tech Lead Review — Hermes Web Client Requirements

**Status as of 2026-05-10: All 10 issues have been addressed and resolved in REQUIREMENTS.md. See section 6 (Resolved Design Decisions) for the current state.**

## Summary

The vision is compelling and well-articulated. The document clearly identifies the core differentiator (tool trace visibility) and the high-level architecture. However, there are significant risks, hidden complexities, and gaps that need attention before this is ready for implementation. This review is organized by severity.

---

## Red Flags (Must Fix)

### 1. Phase 2 and 3 Assume Hermes Features That Don't Exist

The document lists requirements that depend on Hermes internals that do not currently exist or are significantly less capable than assumed:

| Requirement | Hermes Reality | Impact |
|---|---|---|---|
| **Tool effect metadata** (FR2: files_read, files_written, commands_run, risk level, etc.) | Hermes does not annotate tool calls with this metadata. The AIAgent stores raw tool input/output, but there is no effects-tracking layer. | You must build a tool-wrapping/interception layer inside Hermes to collect this — this is a substantial engineering effort, not a config change. |
| **Risk levels and approval scoping** (FR7) | Hermes has approval prompts, but no risk-level taxonomy, no scope tracking, and no "approve for session" persistence. The TUI gateway's `approval.respond` is simple yes/no. | The entire approval system described (risk levels, scope, policies, audit log) is net-new in Hermes. |
| **Session forking** (FR6) | Hermes has no fork concept. Sessions have parent_session_id but no cloning mechanism. | Forking requires copying the full message history, system prompt state, and session metadata — then linking it as a child. Non-trivial. |
| **Full context resume** (FR6) | Hermes sessions have token limits and compression. "Full context" is a negotiation between budget and history. | What "full context" means varies by model and session length. This needs a policy, not a boolean. |

**Resolution**: All four gaps are addressed by deferring to later phases. MVP scope shows what Hermes already has (raw input/output, duration, exit code, parent_session_id links, simple yes/no approvals) and defers the enriched metadata, cloning, and approval policies to future phases. See the "Phased Feature Delivery" table in REQUIREMENTS.md section 6.

---

### 2. "No Mocks" Testing Will Destroy Velocity

A single developer building a Vue SPA, a Django backend, and a Hermes module — and insisting on testing everything against a live Hermes+Gateway instance — will spend most of their time context-switching between components rather than iterating on any one of them.

Specific problems:
- Every Vue UI change requires a running Hermes with specific session state, tool call history, and approval states to exercise the relevant code path.
- Error states (WebSocket disconnect, auth failure, tool timeout) require orchestrating Hermes into those states, which is far harder than simulating them.
- Regression testing requires rebuilding and restarting the Hermes process.

**Recommendation**: Do NOT abandon mocks entirely. Instead, have the Gateway expose a **`/simulate` endpoint** controlled via WebSocket messages that injects synthetic events into the event stream. This way the Vue app connects to the same Gateway (live or simulated) with the same protocol — no separate mock server, but the developer can trigger specific event sequences without running an agent.

**Resolution**: Accepted. The Gateway will include a `/simulate` WebSocket endpoint that accepts synthetic events for testing. Not a mock server — a real Gateway feature that happens to accept injected events.

---

### 3. "Three Separate Machines" Is Premature

Single-user tool, three services on three separate machines, needs JWT auth, TLS, CORS, and a public key distribution mechanism. This is a lot of operational overhead for a tool where, realistically, the developer and user are the same person for the first year.

The document says "separate machines in production" but also "dev workflow: mixed." The production topology adds real complexity:

- The Gateway needs the Django public key file — how does it get there? Mounted volume? Config management? Env var?
- The browser opens two connections (one to Django, one to Gateway) — this means two domains, two TLS certificates, two potential points of failure.
- CORS configuration is required for the WebSocket connection.
- The Gateway port needs to be open/firewalled.

**Recommendation**: For MVP, default to a **single-machine deployment** (Django + Gateway + Hermes on one server, possibly in Docker Compose). Keep the separate-process architecture so it CAN be split later, but don't require it for MVP. Remove "separate machines" from the System Context section — call it the "scaled deployment" option.

**Resolution**: Django and Hermes+Gateway run in separate containers on the same machine. A reverse proxy (nginx/Caddy) terminates TLS and routes `/api/*` to Django and `/ws/*` to the web_gateway. From the browser's perspective, there is one origin. Architecture remains component-separated for future splitting.

---

### 4. Document Inconsistency: "Like Telegram" vs. "New Module"

The document says the web_gateway is:

> Configured in Hermes config (**like the Telegram gateway**)

Then:

> It does **NOT reuse the TUI gateway** — it is a purpose-built module

The Telegram gateway and the TUI gateway are very different things. The Telegram gateway is a **message platform adapter** — it sends/receives text messages and maps them to/from agent conversations. The TUI gateway is a **control-plane protocol** — it exposes RPC methods for session management, prompt submission, tool execution, approvals, etc.

The web_gateway is architecturally closer to the **TUI gateway** (a control-plane protocol with structured events), not the Telegram gateway (a message relay). Calling it "like the Telegram gateway" in terms of config and lifecycle is fine, but the document should explicitly distinguish the two patterns.

**Recommendation**: Rephrase to: "Configured in Hermes config (like the Telegram gateway's `enabled`/`token` pattern) but architecturally modeled on the TUI gateway's RPC method dispatch and event emission patterns."

**Resolution**: The document now compares the web_gateway to the TUI gateway throughout. The Telegram gateway comparison is removed from all architectural descriptions.

---

### 5. Missing: Hermes Crash and Recovery Story

The disconnect behavior covers WebSocket drops, but what happens when:
- The Hermes process crashes mid-session?
- The Gateway module throws an exception and the WebSocket server goes down?
- Django restarts for a deployment and in-flight JWT tokens become invalid?

The document has no failure mode analysis for any component. For a "control plane," this is a significant gap.

**Recommendation**: Add a "Failure Modes" section covering at minimum:
- Hermes crash → sessions persist in SQLite, agent run is lost, client sees "Hermes disconnected" state
- Gateway crash → WebSocket drops, clients reconnect when Gateway is back, event replay buffer is lost (cold start)
- Django restart → existing JWT tokens remain valid until expiry, new logins may fail briefly
- Token expiry mid-session → client shows "session expired" and prompts re-authentication, running agent is interrupted

**Resolution**: Minimal coverage accepted. The WebSocket disconnect behavior is documented (pause indefinitely, reconnect replays buffer + state snapshot). Other failure modes are deferred to the design phase.

---

## Yellow Flags (Should Address Before Implementation)

### 6. Auth for a Single-User App

The document has a full authentication flow (login form, JWT, validation) for a single-user tool. If there's only one user:
- Why not skip the login form entirely for MVP? Use a pre-shared API key configured in both Django and the Gateway.
- Or skip auth on the Gateway entirely when it's on the same machine as the SPA (localhost-only for dev, VPN for prod).
- The JWT machinery adds real complexity (key generation, rotation, token refresh, error handling) for zero practical benefit in a single-user context.

**Recommendation**: Default to **no auth on Gateway in dev mode** (localhost), **pre-shared API key in single-machine prod**. Only add the full JWT flow if multi-user or separate-machine deployment is actually needed.

**Resolution**: JWT flow kept as-is. RS256 with Django signing and Gateway validation. Accepted because the implementation cost is modest and the security model is clean.

---

### 7. The Event Replay Buffer Has No Persistence

It's in-memory only: "last 1000 events per session, used to replay on reconnect." If the Gateway process restarts, the buffer is empty. This means:
- A client that reconnects after a Gateway restart gets a state snapshot but no event history.
- Events that happened between disconnect and Gateway restart are permanently lost to the client's UI.

For a "control plane," this invisibility is problematic. The user disconnects, misses something important, reconnects, and it's gone.

**Recommendation**: Either (a) persist the event buffer to a small SQLite table (lightweight, survives restarts), or (b) make the state snapshot rich enough that the client can reconstruct context from Hermes' existing SQLite/JSONL storage. Option (b) is simpler and consistent with the "Gateway is stateless" principle — the Gateway queries Hermes for missed events rather than storing them itself.

**Resolution**: Option (a) accepted. Event buffer persisted to a local SQLite table (last 1000 events per session or 24 hours, auto-pruned). Survives Gateway restarts.

---

### 8. The "Shared Terminal" Uses Hermes' Terminal Backend

FR9 describes a "live terminal" with streaming stdout/stderr, kill, history, etc. Hermes' terminal execution works through its tool system (`terminal`/`bash` tool), which:
- Runs commands via subprocess on the Hermes server
- Returns output as tool results
- Supports various backends (local, Docker, SSH, etc.)

The question is: does the shared terminal run through the **same agent tool system** or is it a **separate shell session**?

- If through the tool system: the agent and user share the same command execution environment, but user commands need to be injected as pseudo-tool-calls that the agent can see. This is architecturally novel.
- If a separate shell session: the user gets a real PTY, but the agent has no awareness of what the user is doing. This defeats the "shared context" goal.

The document doesn't address this. The distinction between "user terminal command" and "agent terminal tool call" is noted, but the mechanism for making user commands visible to the agent is not defined.

**Recommendation**: Add a design decision on whether user commands flow through the agent's tool loop or bypass it. This affects both the Gateway architecture and the agent's context awareness.

**Resolution**: User gets a real PTY. User commands bypass the agent's tool loop by default. The user can selectively share command outputs and errors with the agent (attach to context). Agent and user commands are visually separated in the terminal history.

---

### 9. Timeline Feasibility: 3-6 Months

For a single developer building:

| Component | Effort Estimate |
|---|---|
| Hermes `web_gateway` module (WebSocket server, JWT auth, AIAgent integration, event streaming, session proxy, file access, terminal backend, approval relay) | 2-3 months |
| Django server (auth, preferences, audit log, static serving) | 2-4 weeks |
| Vue SPA (session browser, timeline, composer, tool trace cards, approval inbox, terminal, file browser, context inspector) | 3-4 months |
| Integration, debugging, edge cases, deployment | 1-2 months |
| **Total** | **6-10 months** |

The 3-6 month estimate assumes a significant portion of the Hermes gateway work can be reused from `tui_gateway/`. Looking at the actual codebase, the TUI gateway has the method dispatch pattern and the AIAgent integration, but the WebSocket transport, JWT auth, structured event protocol, event replay, filesystem access, and terminal forwarding are all net-new.

**Recommendation**: Be honest about the timeline. A realistic v1 for a single developer is 6-9 months. Either scope down to Phase 1 only for a 3-month target, or accept the longer timeline for Phases 1-3.

**Resolution**: Timeline revised to 6-9 months for Phases 1-3. Key Design Decisions table updated.

---

### 10. The Config Schema Has No Defaults Documented

The document says "All fields have sensible defaults" but doesn't say what they are. For a developer implementing this, the documented defaults matter:
- What's the default port? (8765 is documented, good.)
- What's the default `ws_path`? (`/ws` — good.)
- What happens when `tls.enabled` is `false` and the port is exposed? Plain WebSocket, no encryption.
- What's the default `rate_limit`? 100 what? Per second? Per minute? Per connection?

**Recommendation**: Document every default value explicitly, with units where applicable.

**Resolution**: Full defaults table added to REQUIREMENTS.md section 6 with all 12 fields, their defaults, and units/notes.

---

## Green Flags (What's Strong)

- **Tool trace visibility as the north star**: Correct call. This is the single feature that makes the client dramatically more valuable than Telegram.
- **New module, not a TUI wrapper**: The TUI gateway is designed for a very specific purpose (stdio to a local terminal UI). A purpose-built WebSocket gateway is the right call.
- **Event replay buffer on reconnect**: Smart lightweight solution to a real UX problem.
- **Pause indefinitely on disconnect**: Correct behavior for a control plane — never auto-approve.
- **Reference codebase exploration**: Including the specific Hermes files (`run_agent.py`, `gateway/session.py`, etc.) in the document shows real homework was done.
- **Rich event type taxonomy**: The 18+ event types in FR2 are appropriate and forward-looking for Phases 4-5.
- **Auth decoupled from Hermes**: Django handles auth independently — clean separation of concerns.

---

## Summary of Required Changes

| # | Change | Severity | Effort | Status |
|---|---|---|---|---|
| 1 | Add "new Hermes features needed" tracking column | High | Small | **Resolved** — Added "Phased Feature Delivery" table to section 6 |
| 2 | Add Gateway `/simulate` capability for testing | High | Medium | **Resolved** — Gateway includes a `/simulate` endpoint for synthetic events |
| 3 | Default to single-machine deployment for MVP | High | Small | **Resolved** — Two containers on same machine, reverse proxy, single origin |
| 4 | Fix "like Telegram" vs. TUI gateway inconsistency | High | Small | **Resolved** — Document compares to TUI gateway throughout |
| 5 | Add Failure Modes section | High | Small | **Resolved** — Minimal coverage: WebSocket disconnect behavior documented |
| 6 | Reconsider auth complexity for single-user | Medium | Small | **Resolved** — JWT flow kept; acknowledged as modest cost |
| 7 | Persist event buffer or make state snapshot sufficient | Medium | Medium | **Resolved** — Persisted to SQLite table |
| 8 | Clarify shared terminal: tool loop vs. separate shell | Medium | Small | **Resolved** — Real PTY, user controls sharing with agent |
| 9 | Revise timeline estimate (6-9 months realistic) | Medium | Small | **Resolved** — Timeline updated to 6-9 months |
| 10 | Document all config defaults explicitly | Low | Small | **Resolved** — Full defaults table added to section 6 |
