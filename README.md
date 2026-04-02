# Maison-core

**Maison** is a multi-tenant backend for luxury ground transportation: one platform powers many independent operators (tenants), each with their own branding, fleet, drivers, and riders. It handles bookings end to end—routing and pricing (Mapbox), payments and payouts (Stripe, including Connect), white-label configuration, and role-specific portals for company admins, drivers, and customers.

If you are **evaluating the product or team**, that is the story: B2B2C SaaS for premium ride services, strong isolation between tenants, and integrations you would expect in production (payments, maps, email). If you are **building on the API**, everything routes under `/api/v1`, with JWT auth per role (`tenant`, `driver`, `rider`) and tenant-scoped data.

---

## Live API documentation

Interactive OpenAPI (Swagger UI):

**[https://api.usemaison.io/docs](https://api.usemaison.io/docs)**

The OpenAPI JSON is available at `/openapi.json` on the same host when exposed.

> **Note:** If that URL does not load, the `/docs` path may be blocked by a firewall, corporate network, or edge policy. Try another network or VPN, or run the API locally and open `http://localhost:8000/docs` after starting the server.

---

## What it does (feature snapshot)

- **Multi-tenancy** — Separate operators on shared infrastructure; data scoped by `tenant_id` (including via JWT context).
- **Roles** — Tenants (company admins), drivers, riders; OAuth2 / JWT with refresh patterns.
- **Bookings** — Airport, hourly, and point-to-point flows; status lifecycle and analytics-oriented aggregates.
- **Fleet & pricing** — Vehicles, categories, and tenant-level configuration (including deposits and white-label settings).
- **Billing** — Stripe for rider charges and platform/Connect flows; subscription endpoints for Maison SaaS billing where applicable.
- **Integrations** — Mapbox (routes/pricing inputs), Resend (transactional email), rate limiting backed by **Redis**.

---

## Infrastructure (how we run it)

| Layer | Choice |
|--------|--------|
| **API** | **FastAPI** on **Uvicorn** (Python 3.11 in Docker) |
| **Database** | **PostgreSQL 15** |
| **Cache / rate limits** | **Redis 7** |
| **Migrations** | **Alembic** |
| **Containers** | **Docker Compose** (`docker/docker-compose.yml`): `web` (API), `db`, `redis` |

Typical layout:

- **Development:** Compose brings up API + Postgres + Redis; the API container mounts the `backend/` tree for hot reload.


Environment variables are loaded from app settings (see **`backend/app/config.py`**). For Docker, Compose reads **`docker/.env`** (see `env_file` in `docker/docker-compose.yml`). Set database fields (`db_user`, `db_password`, `db_host`, `db_port`, `db_name`—use **`db`** as `db_host` when talking to the Compose Postgres service), plus `redis_url`, Stripe keys, Mapbox token, JWT secrets, `cors_origins`, and the rest of the required keys from `Settings`.

---

## Tech stack

- **Framework:** FastAPI  
- **ORM / DB:** SQLAlchemy, PostgreSQL  
- **Validation:** Pydantic v2  
- **Auth:** OAuth2 / JWT (role-based)  
- **Migrations:** Alembic  
- **Rate limiting:** SlowAPI + Redis  

---

## Prerequisites

- **Python 3.11+** (matches `docker/Dockerfile`)
- **Docker** and **Docker Compose** (recommended)
- **PostgreSQL** and **Redis** if you run the API without Compose

Linux, macOS, or **WSL2** on Windows are the smoothest paths; native Windows works with a virtualenv, but WSL2 avoids most path and tooling friction.

---

## Quick start (Docker Compose)

From the repository root:

```bash
cd docker
# Create docker/.env with variables required by backend/app/config.py (match Compose service names, e.g. db_host=db)
docker compose up --build
```

The API listens on **port 8000** by default (`http://localhost:8000`). Swagger UI: **`http://localhost:8000/docs`**.

Apply migrations inside the stack (example: exec into the `web` container, or run Alembic from a shell with the same env as the app):

```bash
cd backend && alembic upgrade head
```

On Linux/macOS you can also use **`./start_project.sh`** or **`./start_tmux.sh`** for a tmux-based workflow (Postgres container, Compose, Alembic shell, Stripe webhook forwarding—adjust paths to match your machine).

---

## Local development (without Docker)

```bash
python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

Configure **`backend/app/.env`** (or the path your `Settings` class uses) with the same variables as production-oriented deploys: database URL, Redis, JWT, Stripe, Mapbox, Resend, `cors_origins`, etc.

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API surface (overview)

All HTTP routes are versioned under **`/api/v1/`**, for example:

- **`/api/v1/auth/...`** — Login and token flows by role  
- **`/api/v1/tenant/...`** — Tenant admin operations  
- **`/api/v1/driver/...`** — Driver portal  
- **`/api/v1/users/...`** — Riders  
- **`/api/v1/bookings/...`** — Bookings  
- **`/api/v1/vehicles/...`** — Fleet  
- **`/api/v1/tenant/config/...`** — White-label and configuration  
- **`/api/v1/subscription/...`** — Maison subscription (Stripe)  
- **`/api/v1/webhooks/...`** — Stripe webhooks  

For exact paths and request bodies, use **[the live docs](https://api.usemaison.io/docs)** or local `/docs`.

---

## Repository layout

```text
backend/
├── app/
│   ├── api/
│   │   ├── routers/       # Route modules (/api/v1/...)
│   │   ├── services/      # Business logic
│   │   └── core/          # Auth, security, dependencies
│   ├── models/            # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── db/                # Database setup
│   └── utils/
├── alembic/               # Migrations
docker/
├── docker-compose.yml
├── Dockerfile
└── nginx.conf             # Example reverse proxy for /api/
```

---

## Database

Schema evolves via **Alembic**. A SQL reference dump lives in **`docs/database_schema.sql`**; diagram PDFs are under **`docs/`** if you need a visual ER overview.

---

## More detail


For a longer walkthrough of multi-tenancy, **ServiceContext**, booking and payment flows, and third-party integrations, see **`docs/PROJECT_OVERVIEW.md`**.

