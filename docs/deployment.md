# BITNP IDEAS Non-Docker Deployment

This document describes a production-style deployment without Docker. It keeps the
same API contract as local development and Docker:

```text
Browser request: /api/v1/*
nginx: strip /api/v1
FastAPI backend: /*
```

## 1. Layout

Example target layout:

```text
/opt/bitnp-ideas/
  apps/backend/
  apps/frontend/
  package.json
  pnpm-lock.yaml
  pnpm-workspace.yaml
/etc/bitnp-ideas/
  backend.yaml
/var/lib/bitnp-ideas/
```

The examples below assume:

- backend listens on `127.0.0.1:8000`
- nginx serves the frontend on port `80` or `443`
- PostgreSQL database is named `bitnp_ideas`
- service user is `bitnp-ideas`

## 2. System Packages

Install the platform packages for Python, Node.js, PostgreSQL, nginx, and build
tools. On Debian/Ubuntu this is typically:

```bash
sudo apt-get update
sudo apt-get install -y nginx postgresql postgresql-contrib python3.12 curl git
curl -LsSf https://astral.sh/uv/install.sh | sh
corepack enable
corepack prepare pnpm@latest --activate
```

Record the absolute `uv` path after installation:

```bash
command -v uv
```

Use that path in the systemd unit below. The examples use
`/usr/local/bin/uv`, but installations created by a user-local installer may
land somewhere else.

Create a dedicated service user:

```bash
sudo useradd --system --create-home --home-dir /var/lib/bitnp-ideas --shell /usr/sbin/nologin bitnp-ideas
sudo mkdir -p /opt/bitnp-ideas /etc/bitnp-ideas
sudo chown -R bitnp-ideas:bitnp-ideas /opt/bitnp-ideas /var/lib/bitnp-ideas
```

## 3. PostgreSQL

Create the database and application role:

```bash
sudo -u postgres psql
```

```sql
CREATE USER bitnp_ideas WITH PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE bitnp_ideas OWNER bitnp_ideas;
\q
```

Use the same URL shape that the backend validates:

```text
postgres://bitnp_ideas:replace-with-a-strong-password@127.0.0.1/bitnp_ideas
```

## 4. Backend Configuration

Copy `apps/backend/config.yaml` to `/etc/bitnp-ideas/backend.yaml` and replace
all local/demo values. The backend fails startup when required YAML fields are
missing or invalid, so keep the full structure:

```bash
sudo install -o root -g bitnp-ideas -m 0640 apps/backend/config.yaml /etc/bitnp-ideas/backend.yaml
openssl rand -hex 64
```

Use the generated random value as `security.session_secret_key`. Do not reuse
the local or Docker demo secrets in production.

```yaml
app:
  name: BITNP IDEAS
  version: 0.1.0
  openapi_url: /openapi.json
  docs_url: /docs

server:
  cors_origins:
    - https://ideas.example.com

database:
  url: postgres://bitnp_ideas:replace-with-a-strong-password@127.0.0.1/bitnp_ideas

security:
  session_secret_key: replace-with-at-least-64-random-hex-chars
  session_token_ttl_seconds: 28800
  oidc_state_ttl_seconds: 600
  oidc:
    enabled: true
    issuer_url: https://login.example.com/realms/bitnp
    client_id: bitnp-ideas
    client_secret: replace-with-oidc-client-secret

api_keys:
  timestamp_tolerance_seconds: 300
  allowed_entities:
    - idea
```

The `api_keys.allowed_entities` list must remain `idea` only for v1.

Configure the OIDC provider with the same production origin:

- allowed redirect URI: `https://ideas.example.com/login`
- allowed web origin: `https://ideas.example.com`
- client type: confidential client with a client secret
- issuer URL, client ID, and client secret matching `backend.yaml`
- `server.cors_origins` containing the frontend origin

## 5. Backend Install And Migrate

```bash
sudo -u bitnp-ideas git clone <repo-url> /opt/bitnp-ideas
cd /opt/bitnp-ideas/apps/backend
sudo -u bitnp-ideas uv sync --frozen
```

Choose the migration path for the release:

| Release artifact | Command |
| ---------------- | ------- |
| Contains a coordinated `apps/backend/alembic/versions/*.py` revision chain | `sudo -u bitnp-ideas BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml uv run alembic upgrade head` |
| Does not contain a coordinated revision chain | Generate, review, then apply a local migration with the commands below |

Local migration path:

```bash
sudo -u bitnp-ideas BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml \
  uv run alembic revision --autogenerate -m "release schema"
sudo -u bitnp-ideas BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml \
  uv run alembic upgrade head
```

## 6. systemd Backend Service

Create `/etc/systemd/system/bitnp-ideas-backend.service`:

```ini
[Unit]
Description=BITNP IDEAS Backend
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=bitnp-ideas
Group=bitnp-ideas
WorkingDirectory=/opt/bitnp-ideas/apps/backend
Environment=BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml
ExecStart=/usr/local/bin/uv run uvicorn bitnp_ideas.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bitnp-ideas-backend
sudo systemctl status bitnp-ideas-backend
curl http://127.0.0.1:8000/health
```

## 7. Frontend Build

The current frontend client uses a fixed `/api/v1` base URL. nginx must strip
that prefix before forwarding API calls to FastAPI. Setting `VITE_API_BASE_URL`
is not required unless the frontend client is later changed to read that
environment variable.

```bash
cd /opt/bitnp-ideas
sudo -u bitnp-ideas pnpm install --frozen-lockfile
sudo -u bitnp-ideas pnpm --filter @bitnp-ideas/frontend build
sudo mkdir -p /var/www/bitnp-ideas
sudo rsync -a --delete apps/frontend/dist/ /var/www/bitnp-ideas/
```

## 8. nginx

Create `/etc/nginx/sites-available/bitnp-ideas`:

```nginx
server {
  listen 80;
  server_name ideas.example.com;

  root /var/www/bitnp-ideas;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location = /api/v1 {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /api/v1/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/bitnp-ideas /etc/nginx/sites-enabled/bitnp-ideas
sudo nginx -t
sudo systemctl reload nginx
```

For HTTPS, terminate TLS in nginx and keep the same `/api/v1` locations.

## 9. Release Checklist

Run these before switching traffic:

```bash
cd /opt/bitnp-ideas/apps/backend
BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml uv run ruff check
BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml uv run pytest

cd /opt/bitnp-ideas
pnpm --filter @bitnp-ideas/frontend lint
pnpm --filter @bitnp-ideas/frontend typecheck
pnpm --filter @bitnp-ideas/frontend build
```

Runtime checks:

```bash
curl http://127.0.0.1:8000/health
curl https://ideas.example.com/api/v1/health
curl https://ideas.example.com/
```

The OpenAPI document should expose unversioned backend paths such as `/ideas`.
It should not expose `/api/v1/ideas`; that prefix belongs to nginx and the
frontend request layer.

OIDC login check:

1. In the provider, confirm `https://ideas.example.com/login` is registered as
   an allowed redirect URI.
2. Open `https://ideas.example.com/login`.
3. Complete the provider login.
4. Confirm the browser returns to `https://ideas.example.com/login` and the app
   stores a user session.

## 10. Operations

Useful commands:

```bash
sudo journalctl -u bitnp-ideas-backend -f
sudo systemctl restart bitnp-ideas-backend
sudo nginx -t
sudo systemctl reload nginx
```

For every deployment:

1. Pull the release.
2. Install backend and frontend dependencies from lockfiles.
3. Run Alembic migrations with `BITNP_IDEAS_CONFIG=/etc/bitnp-ideas/backend.yaml`.
4. Rebuild and rsync frontend assets.
5. Restart backend.
6. Reload nginx.
7. Run the runtime checks above.
