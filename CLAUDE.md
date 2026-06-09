# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run the API (local, no Docker)
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Docker Compose
```bash
cd docker
docker compose up --build
```

### Database migrations
```bash
cd backend
alembic upgrade head                          # apply all
alembic revision --autogenerate -m "message"  # generate new migration
alembic downgrade -1                          # roll back one step
```

### Install dependencies
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Run tests
```bash
cd backend
pytest
```

## Architecture

**Maison** is a multi-tenant B2B2C SaaS backend for luxury ground transportation. One deployed instance serves many independent operators (tenants), each with their own branding, fleet, drivers, and riders.

### Directory layout
```
backend/app/
├── api/
│   ├── routers/        # Thin HTTP layer — validates input, calls services
│   ├── services/       # All business logic
│   │   └── email_services/  # Resend email per role (drivers, riders, tenant)
│   └── core/           # JWT/OAuth2, deps, rate-limit helpers
├── models/             # SQLAlchemy ORM models (PostgreSQL)
├── schemas/            # Pydantic v2 request/response schemas
├── db/database.py      # SQLAlchemy engine + session factories
├── config.py           # Pydantic-settings Settings class (reads .env)
├── domain/plans.py     # Subscription plan definitions
└── policies/           # Plan-gating policy logic
```

### ServiceContext pattern
Every service class inherits from `ServiceContext` (`app/api/services/service_context.py`). The constructor receives `db` and `current_user`, and automatically derives:
- `self.role` — `tenant` | `driver` | `rider` | `admin`
- `self.tenant_id` — always set, used to scope all DB queries
- `self.time_now` — UTC-aware timestamp

This is the primary multi-tenant isolation mechanism. All queries in services **must** filter by `self.tenant_id`. The three roles resolve differently: tenants use their own `id` as `tenant_id`; drivers and riders read `tenant_id` from the join to their parent tenant.

### Auth flow
- `POST /api/v1/auth/login/{role}` where role is `tenant`, `driver`, or `rider`
- Returns `access_token` (Bearer JWT) + sets HttpOnly `refresh_token` cookie
- `oauth2.role_table_map` maps role strings to SQLAlchemy model classes for `get_current_user` lookup
- `deps.get_current_user` is the FastAPI dependency injected into protected routes

### Key third-party integrations
| Service | Purpose |
|---------|---------|
| **Stripe** | Rider payments (deposit + balance), tenant/driver Express accounts, platform webhooks at `/api/v1/webhooks/` |
| **Mapbox** | Route distance/time for booking price calculation |
| **Resend** | Transactional email (booking confirmations, driver assignments) |
| **Redis** | SlowAPI rate limiting (`redis_url` in settings) |

### Booking lifecycle
`pending` → `confirmed` → `completed` (or `cancelled`). Price is calculated at creation using Mapbox route data + tenant pricing config. Stripe deposit is charged at booking creation; balance is charged at completion with driver payout via Stripe Connect.

### Multi-tenancy
- Each tenant has a unique `slug` (subdomain identifier)
- `TenantSettings` stores flexible config as JSONB
- `TenantBranding` stores white-label visual config (colors, logos)
- PWA manifest and icons are resolved per-host from the `Host` header (`/api/v1/pwa/`)
- Public slug endpoints allow rider sign-up and branding lookup without auth

### Environment config
All settings come from `backend/app/config.py` (`Settings` class, Pydantic-settings). For local dev: `backend/app/.env`. For Docker: `docker/.env` (read by Compose). Key variables: `db_host`, `db_user`, `db_password`, `db_name`, `redis_url`, `jwt_secret`, `stripe_secret_key`, `stripe_webhook_secret`, `mapbox_token`, `resend_api_key`, `cors_origins`, `environment`, `domain`.

Use `db_host=db` when running inside Docker Compose (the Postgres service name).
