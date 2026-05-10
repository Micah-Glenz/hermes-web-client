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
├── docker-compose.yml
├── nginx.conf        # Production reverse proxy config
├── AGENTS.md
├── REQUIREMENTS.md
└── TECHLEAD_REVIEW.md
```

## Dev workflow
```bash
docker compose up    # Starts all three services
```
- Backend: http://localhost:8000/api/
- Web (Vite): http://localhost:5173 (Vite proxies /api → backend, /ws → gateway)
- Gateway: ws://localhost:8765

## Build order
1. Docker Compose + project scaffolding ✅
2. Hermes web_gateway module + `/simulate` endpoint
3. Django auth + SPA serving
4. Vue session browser (Phase 1)
5. Phase 2 (live control) and Phase 3 (workspace) iteratively

## Timeline
- 6-9 months for Phases 1-3 as a solo developer

## Key requirements links
- REQUIREMENTS.md — full functional and non-functional requirements
- TECHLEAD_REVIEW.md — review notes and resolution of all 10 issues
