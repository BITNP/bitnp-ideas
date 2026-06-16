# BITNP IDEAS

BITNP IDEAS is an internal _**I**dea-**D**riven **E**xecution **A**dministration **S**ystem_. It turns ideas into projects, tasks, schedules, activity streams, and audit logs.

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

Backend runtime configuration is loaded from [apps/backend/config.yaml](apps/backend/config.yaml). The local database URL is:

```text
postgres://bitnp_ideas:bitnp_ideas@127.0.0.1/bitnp_ideas
```

Invalid or incomplete backend configuration fails startup immediately; the backend does not silently replace bad YAML values with code defaults.

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

Docker uses [apps/backend/config.docker.yaml](apps/backend/config.docker.yaml), selected with `BITNP_IDEAS_CONFIG`, so the backend container connects to the Compose `postgres` service while the normal local config remains pointed at `127.0.0.1`.

## Database Migrations

Alembic migration files under `apps/backend/alembic/versions/*.py` are ignored by default.

After pulling code, generate and apply your local migration when models changed:

```bash
cd apps/backend
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

This is similar to Django's model-to-migration workflow. The project does not upload development migration files by default because parallel schema work can create revision conflicts that are painful to merge and may force teams to rebuild whole databases. Commit migration files only when the team has coordinated the revision chain for a release.
