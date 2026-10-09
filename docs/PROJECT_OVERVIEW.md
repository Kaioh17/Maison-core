# Maison: A Multi-Tenant Luxury Ground Transportation Platform

## Overview

**Maison core** is a B2B2C SaaS backend for luxury ground transportation.
One deployment serves many independent operators (tenants).
Each tenant gets its own branded rider app, fleet, drivers, pricing, and payouts.
The API is built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**.
All routes live under `/api/v1`, except the PWA assets, which live at the URL root.

## Multi-Tenancy

- **Tenant slug**: Each tenant has a unique slug that doubles as its subdomain (e.g. `acme.maison.com`).
The frontend reads the slug from the hostname and the backend scopes every query by the matching `tenant_id`.
- **Data isolation**: Drivers, vehicles, riders, bookings, and payouts are only ever visible to their own tenant.
- **White-label**: `TenantBranding` holds colors, palette, logo, and phone.
`TenantSettings` holds flexible JSONB config.
- **Per-host PWA**: `/manifest.webmanifest`, `/icons/*`, `/apple-touch-icon.png`, and `/favicon.ico` resolve the tenant from the `Host` or `X-Forwarded-Host` header.
Icons are rendered with Pillow from the tenant logo, versioned by `tenant_branding.updated_on`, and cached immutably.
Unknown or inactive slugs get the default Maison manifest.
- **Public slug endpoints**: Rider sign-up, slug verification, and branding lookup work without auth.

## Architecture

```
Request -> Router (validate, auth) -> Service (business logic) -> SQLAlchemy models -> PostgreSQL
                                          |
                          Stripe / Mapbox / Resend / OpenAI or Gemini
Celery beat -> worker -> reminder_service -> Resend        (Redis is broker and rate-limit store)
```

```
backend/app/
├── api/
│   ├── routers/     # Thin HTTP layer
│   ├── services/    # Business logic (+ analytics/, stripe_services/, email_services/)
│   └── core/        # JWT/OAuth2, deps, rate limiting
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic v2 schemas
├── domain/          # plans.py, billing.py, legal.py (constants and plan definitions)
├── policies/        # plan_policy.py (quota and subscription gating)
├── data/ai_kb/      # Knowledge base for the AI assistant
├── celery_app.py    # Celery app and beat schedule
├── tasks.py         # Celery tasks
├── seed_demo.py     # Demo tenant seeding
└── utils/           # Logging, error handling, PWA icons, QR codes, passwords
```

## Core Components

### Authentication and Roles
- OAuth2 with JWT.
`POST /auth/login/{role}` returns a Bearer `access_token` and sets an HttpOnly `refresh_token` cookie.
- Four roles: `tenant` (operator admin), `driver`, `rider`, and platform `admin`.
- `deps.get_current_user` resolves the user through `oauth2.role_table_map`.
- Admin routes additionally require `verify_api_key` and `is_admin`.

### ServiceContext
Every service inherits `ServiceContext`, which takes `db` and `current_user` and derives `role`, `tenant_id`, and a UTC-aware `time_now`.
All service queries must filter by `self.tenant_id`.
This is the main multi-tenant isolation mechanism.
Background jobs run outside a request, so they open their own session instead.

### Data Model
- **Tenant side**: `Tenants`, `TenantProfile` (slug, Stripe IDs), `TenantStats`, `TenantSettings` (JSONB), `TenantBranding`, `TenantPricing`, `TenantBookingPricing`.
- **Operations**: `Users` (riders), `Drivers`, `Vehicles`, `VehicleConfig`, `VehicleCategoryRate`, `Bookings`, `BookingRatings`, review model.
- **Money**: `Transaction`, `Payout` (driver pay ledger).
- **Compliance**: `LegalAcceptance`.
- **Platform**: `Admin`.
- Migrations are managed with Alembic.

### Pricing
`pricing_calc.quote_total` is the single source of truth for fare math.
It is used by real quotes and by the tenant pricing scenario calculator (`/tenant/config/pricing/scenarios`), so the two cannot disagree.
Inputs are base fare, per-mile, per-minute or per-hour rates, vehicle category rate, and for airport rides the surcharge, gratuity, gate fee, and meet-and-greet fee.
Service types are `airport`, `hourly`, and `dropoff`.

### Subscriptions and Plan Gating
- Plans live in `domain/plans.py`: **free** (1 vehicle, 1 driver, 3% fee), **growth** (5 vehicles, 7 drivers, 2% fee, analytics), **fleet** (unlimited, 1% fee, analytics and property support).
The take rate falls as the plan price rises.
- `domain/billing.py` maps Stripe price IDs to plans server-side, so the plan is always derived from what was actually paid for and never from a client field.
- New tenants start `unsubscribed` with a NULL plan.
Free is a real $0 Stripe subscription, so a card is always collected.
- `policies/plan_policy.py` enforces quotas and subscription state.
Rejections are HTTP **402** with the message in `detail`.
`past_due` keeps a grace period.
Downgrades block new creates but never delete existing records, and deletes are never gated.
- Endpoints: `GET /subscription/plans`, `/limits`, `/billing`, plus checkout and customer portal flows.
- A founding-operator 100% off coupon is emailed to the first tenants.

### Pilot and Legal Acceptance
- Operators accept the current Terms, Privacy, and Subprocessors versions (`LEGAL_VERSION` in `domain/legal.py`).
Bumping the version forces re-consent.
- Pilot tenants have a 90 day window (`pilot_ends_at`), after which writes are blocked with a 403 and a clear message.
- `GET /legal/status` and `POST /legal/accept` drive the in-app consent flow.
The demo tenant is exempt.

### Driver Earnings and Payouts
- `bookings.driver_earning` is frozen at completion and is the source of truth for what a ride earned.
- The `Payout` ledger records status changes with who made them and when.
- Maison records and calculates but does not move money between operator and driver.
Only cash rides are treated as driver-held.
- Tenants list, bulk-create, and update payouts.
Drivers list their own and mark them `verified` or `disputed`.
- Driver app screens include Earnings and a rides marketplace.

### Booking Lifecycle
`pending` -> `confirmed` -> `completed` (or `cancelled`).
1. Rider (or tenant on their behalf) submits a booking.
2. Mapbox returns distance and time, and `quote_total` prices the ride.
3. A Stripe PaymentIntent collects the deposit.
4. The tenant or driver confirms.
Email confirm links (`/bookings/confirm/{token}`) and driver accept or decline (`/driver/ride/{id}/decision`) are supported.
5. On completion, the balance is charged, `driver_earning` is frozen, a `Transaction` is recorded, and the rider can leave a rating.
Riders can cancel through `/bookings/rider/{id}/cancel`.

### Stripe
- **Platform webhook** (`/webhooks`): `checkout.session.completed`, `customer.subscription.created|updated|deleted`, and `invoice.paid|payment_failed`.
These keep plan and status in sync.
- **Connect webhook** (`/webhooks/connect/tenant`): `account.updated` and `payment_intent.succeeded`.
These handle onboarding state and deposit or balance reconciliation.
- Tenants and drivers use Express accounts, with onboarding links and a dashboard link.

### Background Jobs
Celery, with Redis as broker, runs as `worker` and `beat` services in Docker Compose.
`send_booking_reminders` runs every 15 minutes.
It sends one-shot emails, tracked by boolean flags on `Bookings`:
- Drivers get a ride reminder 24h and 1h before pickup (confirmed bookings with a driver).
- Tenants and drivers get a confirm-booking nudge when a booking is still `pending` close to pickup.

### AI Assistant
`POST /ai/chat` is a small RAG in front of OpenAI or Gemini.
It retrieves keyword-matched docs from `data/ai_kb/` and adds a tenant-scoped, PII-free live snapshot.
It is read-only and cannot take actions.

### Analytics
Role-specific SQL aggregates for tenants, drivers, and riders (`services/analytics/`).
Tenant analytics are gated to paid plans.

### Email (Resend)
Modular per-role services (admin, drivers, riders, tenants) share `email_layout.py` for white-labeled templates.

### Other Pieces
- **Demo mode**: `GET /demo` returns credentials for a seeded demo tenant (`seed_demo.py`), and is disabled when `demo_tenant_slug` is empty.
- **Temp QR tool**: `/tools/temp-qr` generates QR codes for tenant links.
- **Client logs**: `POST /logs` receives frontend log events.
- **Rate limiting**: SlowAPI backed by Redis.
- **Error handling**: `DBErrorHandler` maps integrity errors to HTTP codes, and transactions roll back on failure.

## Router Map

| Prefix | Purpose |
|--------|---------|
| `/auth` | Login, refresh, logout per role |
| `/tenant`, `/tenant/config` | Tenant dashboard, drivers, vehicles, bookings, riders, Stripe, analytics, settings, pricing, branding |
| `/driver` | Driver profile, available rides, decisions, earnings, analytics |
| `/users` | Rider sign-up and profile |
| `/bookings` | Create, confirm, cancel, pay, rate |
| `/vehicles` | Fleet CRUD and images |
| `/subscription` | Plans, limits, billing, checkout |
| `/webhooks` | Stripe platform and Connect |
| `/slug` | Public slug verification and storefront |
| `/legal` | Pilot and consent status |
| `/ai`, `/demo`, `/tools/temp-qr`, `/logs`, `/admin` | Assistant, demo, tools, logging, platform admin |
| `/` (root) | Per-host PWA manifest and icons |

## Technology Stack

FastAPI, PostgreSQL 15, SQLAlchemy, Alembic, Pydantic v2, OAuth2 and JWT, Redis 7, SlowAPI, Celery, Stripe, Mapbox, Resend, OpenAI or Gemini, Pillow, Docker Compose.

## Why This Architecture

1. **Isolation**: ServiceContext scoping keeps one tenant's data away from another's.
2. **Single sources of truth**: Plans, price-to-plan mapping, fare math, and earnings each live in exactly one place.
3. **Server-side trust**: Plans, quotas, and legal state are decided by the backend, never the client.
4. **Flexibility**: JSONB settings and per-tenant branding allow customization without code changes.
5. **Simplicity**: Thin routers, a service layer, and Celery on the existing Redis keep the moving parts few.
