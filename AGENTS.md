# Hermes Web Client — Project Decisions

## Repository
- Monorepo. Hermes fork in `/hermes/` as a plain subdirectory (no git submodule).
- Client code (Vue + Django) at the monorepo root.

## Stack
- **Frontend**: Vue 3 + Vite + PrimeVue
- **Backend**: Django + Django Ninja
- **Hermes integration**: web_gateway module (built-in Hermes module, modeled on TUI gateway patterns)

## Architecture
- **Dev environment**: Docker Compose for everything (Hermes+Gateway, Django, Vue)
- **Production**: Two containers on same machine behind reverse proxy (nginx/Caddy)
  - Container A: Hermes + web_gateway
  - Container B: Django (serves SPA, auth, prefs, audit log)
  - Browser talks to one origin; reverse proxy routes /api/* to Django, /ws/* to Gateway

## Security
- **Auth**: RS256 JWT. Django signs, Gateway validates with public key.
- **No auth on Gateway in dev mode** (localhost-only in Docker network)

## Gateway
- Persisted event buffer in SQLite (last 1000 events per session or 24h)
- `/simulate` endpoint for synthetic event injection during development

## Project structure
```
agClient/
├── backend/          # Django + Ninja (auth, prefs, audit log)
├── gateway/          # Placeholder WebSocket server → will become web_gateway
├── hermes/           # Hermes fork (clone of NousResearch/hermes-agent)
├── web/              # Vue 3 + Vite + PrimeVue SPA
├── cli-config.yaml   # Hermes project-level config (opencode Go provider, DeepSeek V4 Flash)
├── docker-compose.yml
├── nginx.conf        # Production reverse proxy config
├── Makefile
├── AGENTS.md
├── REQUIREMENTS.md
├── TECHLEAD_REVIEW.md
├── ISSUES_AMENDMENT.md
└── SESSION_SUMMARY.md
```

## Dev workflow
```bash
make up    # Starts all three services in background
make logs  # Watch all service logs
make test  # Run both frontend and backend tests
make down  # Stop everything
```
- Backend: http://localhost:8000/api/ (login: admin / admin)
- Web (Vite): http://localhost:5173 (Vite proxies /api → backend, /ws → gateway)
- Gateway: ws://localhost:8765

## Testing
- **Backend**: `make test-backend` (Django TestCase) or `make test-backend-pytest` (pytest)
- **Frontend**: `make test-web` (Vitest + Vue Test Utils + jsdom)
- **Linting**: `make lint` (ruff for Python, eslint for Vue)
- **Formatting**: `make format-backend` (ruff format), `make format-web` (prettier)

## OpenCode MCPs configured
- **memory** (`@modelcontextprotocol/server-memory`) — local knowledge graph. Call tools like `search_nodes`, `read_graph`, `open_nodes` to retrieve project context. Pre-populated with 12 entities and 17 relations about this project.
- **sequential-thinking** (`@modelcontextprotocol/server-sequential-thinking`) — structured reasoning for complex planning.

### Memory usage instructions
At the start of every session, call `memory search_nodes` or `memory read_graph` to load project context from the local knowledge graph.

During the session, **automatically** save important information using `memory create_entities`, `memory add_observations`, or `memory create_relations` — do not wait to be asked. Use your judgment to decide what matters:
- Config changes, architecture decisions, dependency additions
- Bug root causes, solutions, workarounds discovered
- Project conventions, coding patterns, preferred tools
- Infrastructure setup, credentials locations, env var requirements
- Any context a future session would need to avoid knowledge gaps

The memory graph persists to a JSONL file on disk — it survives opencode restarts. This is the only persistent memory available (supermemory cloud was removed). Proactive saving is required.

## Hermes config
- `cli-config.yaml` in project root is Hermes' project-level config.
- Provider: opencode-go at `https://opencode.ai/zen/go/v1` with `deepseek-v4-flash` model.
- API key from `OPENCODE_GO_API_KEY` env var (sourced from `~/.local/share/opencode/auth.json` on startup).
- Docker compose gateway service passes this env var to the Hermes container.

## Build order (GitHub issues)
0. Protocol Spec: Issue #0 (reference only — create before Phase 1)
1. Phase 0: Infrastructure — Issues #1, #2, #3, #14, #4
2. Phase 1: Hermes web_gateway module — Issues #5–#13
3. Phase 2: Vue Phase 1 (View) — Issues #15–#21
4. Phase 3: Vue Phase 2 (Control) — Issues #22–#26
5. Phase 4: Vue Phase 3 (Workspace) — Issues #27–#31

See https://github.com/Micah-Glenz/hermes-web-client/issues for current status.

## Dependency rules
- Every issue has a `**Depends on**: #N` line in its body
- Protocol Spec (#0) is a reference document, not an implementation task
- Issue #14 moved to Phase 0 (login has no Gateway dependency)
- `/simulate` (#11) is a standalone utility (no auth, no Hermes dependency, outside Hermes repo)

## Timeline
- 6-9 months for Phases 1-3 as a solo developer

## Key requirements links
- REQUIREMENTS.md — full functional and non-functional requirements
- TECHLEAD_REVIEW.md — review notes and resolution of all 10 issues
