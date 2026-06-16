FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app/apps/backend
COPY apps/backend/pyproject.toml apps/backend/uv.lock* ./
RUN uv sync --no-dev || uv sync --no-dev

COPY apps/backend .
ENV PATH="/app/apps/backend/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "bitnp_ideas.main:app", "--host", "0.0.0.0", "--port", "8000"]

