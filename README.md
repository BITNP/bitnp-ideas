# BITNP IDEAS

BITNP IDEAS is an internal idea-driven execution administration system. It turns ideas into projects, tasks, schedules, activity streams, and audit logs.

## Stack

- Backend: Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, uv, Ruff, pytest
- Frontend: Vue 3, TypeScript, Vuetify 4, Pinia, Vue Router, Vite, pnpm

## Local Development

```bash
pnpm install
cd apps/backend
uv sync
uv run uvicorn bitnp_ideas.main:app --reload
```

In another shell:

```bash
pnpm dev
```

Frontend code uses versioned API paths such as `/api/v1/ideas`. The FastAPI application itself does not mount any `/api/v1` prefix; Vite's development proxy and nginx strip that version prefix before forwarding requests to the backend.

## Docker Demo

```bash
cp .env.example .env
docker compose up --build
```

The API runs on `http://localhost:8000`, and the frontend runs on `http://localhost:8080`.

## Database Migrations

Alembic migration files under `apps/backend/alembic/versions/*.py` are ignored by default.

After pulling code, generate and apply your local migration when models changed:

```bash
cd apps/backend
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

This is similar to Django's model-to-migration workflow. The project does not upload development migration files by default because parallel schema work can create revision conflicts that are painful to merge and may force teams to rebuild whole databases. Commit migration files only when the team has coordinated the revision chain for a release.
