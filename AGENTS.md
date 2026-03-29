# AGENTS.md

## Scope and Priority
- This file is for AI coding agents working in `Calnio/`; prefer code-observed behavior over outdated docs.
- Existing AI guidance sources: `.github/copilot-instructions.md` and global Copilot instructions; apply them, but treat Jinja2/CSS notes as legacy unless touching template endpoints.

## Big-Picture Architecture
- Backend entrypoint is `server/main.py` (`FastAPI()` app, router wiring, CORS, static mount, SPA catch-all).
- Frontend is Vue 3 + Vite in `frontend/src`; production build goes to `frontend/dist` and is served by FastAPI (`/assets` + catch-all `/{full_path:path}`).
- API layer is split between legacy web/form routes (`server/app/api/*.py`) and JSON API routes (`server/app/api/v1/*.py`).
- Data access follows model + repository pattern: models in `server/db/models/*.py`, DB operations in `server/db/repositories/*.py`.
- Auth is cookie-based JWT via AuthX (`server/core/jwt_config.py`, `server/deps/auth_deps.py`), not bearer headers.

## Request/Data Flow (Important)
- Frontend requests `API_BASE_URL` from `frontend/src/config/api.js` and uses `axios` with `withCredentials: true` (see `LoginPage.vue`, `DashboardLayout.vue`).
- `get_current_user` in `server/deps/auth_deps.py` validates access cookie, falls back to refresh cookie, and may issue a new access cookie.
- Time tracking flow: start/stop/current in `server/app/api/v1/time_entries.py`, persistence via `TimeEntriesRepository` and `time_entries` table.

## Developer Workflows
- Python deps are managed by `uv` (`pyproject.toml`, `uv.lock`, `Dockerfile` uses `uv sync --frozen`).
- Frontend workflows are in `frontend/package.json`: `npm run dev`, `npm run build`, `npm run preview`.
- Migration workflow is managed through `manage.py` commands (`migrate`, `upgrade`, `downgrade`) wrapping Alembic.
- Runtime logs are configured by Loguru in `server/core/logging_config.py` and written to `logs/app_*.log`.

## Project-Specific Conventions
- Keep endpoint families consistent: `/api/v1/...` for JSON API, non-versioned routes for legacy page/form flows.
- Preserve cookie auth contract: endpoints expected by frontend must continue to accept credentials via cookies.
- Use repository objects in route handlers for DB mutations (`UserRepository`, `TimeEntriesRepository`) instead of embedding SQL logic everywhere.
- Pydantic schemas for request/response live in `server/deps/schemas/*` and are used directly by route signatures.

## Known Inconsistencies to Handle Carefully
- Entrypoint strings conflict across files (`server/main.py` exists; several docs/commands reference `server.app.main:app`).
- Port/config references also differ (`settings.server_port=8080`, Docker command exposes app on `8000`, compose maps `8080:8080`).
- Alembic path config appears drifted (`alembic.ini` points to `server/alembic`, migrations are in top-level `alembic/`).
- Before changing startup/migration wiring, verify with current runtime commands instead of trusting README text.

## Safe-Change Checklist for Agents
- If changing auth/session behavior, update both backend cookie handling and frontend `withCredentials` callers.
- If changing API routes, confirm impacted Vue components under `frontend/src/components/**`.
- If changing DB models, generate/apply migration through `manage.py` and check repository usage sites.
- Prefer minimal, localized fixes; this repo has legacy and active paths side-by-side.

## Claude Context

### Who I am
- Name: Myroslav Repin, 15 y/o, self-taught developer, high school student in Canada (Grande Prairie, AB)
- Ukrainian-Canadian Christian, reads Bible daily, spiritual journal, working through C.S. Lewis "Mere Christianity"
- Communicates in Russian and English

### Tech stack
- Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Docker
- MacBook Air M2 (16GB/512GB), Neovim on all servers
- DigitalOcean VPS (Ubuntu 24.04, 30+ users), Raspberry Pi 5 home server (4GB, domain myroslavrepin.com)
- Main project: Calnio — Notion↔Apple Calendar 2-way sync, target first paying customer end of April

### How to respond to me
- Always answer in Russian
- Be a mentor — ask questions, don't hand answers on a plate
- No code unless explicitly asked
- Dry and direct on technical topics
- Point out mistakes directly, don't agree for politeness
- No filler, no motivational fluff — explain logic, teach thinking
