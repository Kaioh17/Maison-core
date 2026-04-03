from fastapi import FastAPI, Request, Depends, Security, HTTPException, status
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from app.api.routers import tenants, auth, drivers, bookings, users, vehicles, tenant_settings, admins,subscriptions, logs, slug, webhooks, dependencies
from app.db.database import engine
from app.models import *
# from utils import logging
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.config import Settings

settings = Settings()
environment = settings.environment
##add frontend urls and middleware 
#user cors

##GEts the ip and Path 
def ip_and_path(request: Request):
    ip = get_remote_address
    path = request.url.path
    return f"{ip}:{path}"

limiter = Limiter(
    key_func= ip_and_path, #rate limit by ip address
    storage_uri = settings.redis_url if settings.redis_url else None,
    default_limits = ["30/minute", "100/second"]
)

Base.metadata.create_all(bind=engine)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Maison Ride-Sharing API",
        version="1.0.0",
        description="""
        ## Maison Ride-Sharing Platform API
        
        Multi-tenant luxury car service backend: **tenants** (companies), **drivers**, **riders**, fleet, bookings, Stripe billing & Connect.
        
        ### Authentication
        Obtain tokens via **`POST /api/v1/auth/login/{role}`** (`tenant` | `driver` | `rider`). Send **`Authorization: Bearer &lt;access_token&gt;`** on protected routes.
        
        ### Multi-tenancy
        Data is scoped by **`tenant_id`** embedded in the JWT (except public registration/slug endpoints).
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": (
                    "JWT login, refresh, logout. Login returns `access_token` and sets HttpOnly `refresh_token` cookie."
                ),
            },
            {
                "name": "Tenant",
                "description": (
                    "Tenant (company) lifecycle: registration, profile, drivers, bookings, vehicles, Stripe Express, analytics."
                ),
            },
            {
                "name": "Drivers",
                "description": (
                    "Driver portal: status, registration token verify, rides, analytics, accept/decline bookings."
                ),
            },
            {
                "name": "Bookings",
                "description": (
                    "Create and list ride bookings; rider confirmation and Stripe checkout sessions."
                ),
            },
            {
                "name": "Users",
                "description": (
                    "Riders: sign up by tenant slug, profile, booking analytics."
                ),
            },
            {
                "name": "vehicles",
                "description": (
                    "Fleet CRUD, categories/rates, vehicle images — scoped to tenant/driver roles."
                ),
            },
            {
                "name": "Tenant Config",
                "description": (
                    "White-label settings: JSON `config`, pricing, branding, per-service booking deposits, logos."
                ),
            },
            {
                "name": "Subscription",
                "description": (
                    "Maison SaaS subscription checkout/upgrades via Stripe (tenant billing, not rider rides)."
                ),
            },
            {
                "name": "Slug",
                "description": (
                    "Public slug lookup for branding/signup and authenticated tenant setup metadata."
                ),
            },
            {
                "name": "Webhooks",
                "description": (
                    "Stripe platform vs Connect webhook receivers — separate URLs and signing secrets."
                ),
            },
            {
                "name": "logs",
                "description": "Ingest frontend log batches for debugging (writes to server log files).",
            },
            {
                "name": "admin",
                "description": "Internal/admin operations (tenant list, destructive actions) — protect in production.",
            },
        ]
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app = FastAPI(
    title = "Maison multi-tenant ride sharing API",
    description="Multi-tenant ride-sharing platform",
    version="1.0.0",
    contact={
        "name": "Maison Development Team",
        "email": f"dev@{settings.domain}"
    },
    # docs_url="/docs" if environment == 'development' else None,
    docs_url="/docs",
    redoc_url="/redoc" if environment == 'development' else None,
    openapi_url="/openapi.json",
    redirect_slashes=False,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": (
                "JWT auth for **tenant** (company admin), **driver**, and **rider** roles. "
                "`POST /api/v1/auth/login/{role}` returns `access_token` and sets an HttpOnly `refresh_token` cookie. "
                "Use `Authorization: Bearer <token>` on protected routes. "
                "See each operation for refresh vs manual refresh behavior."
            ),
        }
    ],
    swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}}
)
# app = FastAPI(swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}})
# CORS for frontend (dev: Vite at 3000; docker: nginx serves same-origin and proxies /api)
# Also includes mobile app origins for Flutter development
_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] 
app.add_middleware(
    CORSMiddleware,

    allow_origins=_cors_origins,
    # Single pattern: Starlette passes this to re.compile(); must be str, not a tuple.
    # allow_origin_regex=r"^https?://[\w-]+(\.usemaison\.io|\.localhost(:\d+)?)$",
    allow_origin_regex=r"^https?://([\w-]+\.)?(usemaison\.io|localhost(:\d+)?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.openapi = custom_openapi


# attach limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.include_router(tenants.router)
app.include_router(auth.router, dependencies=[Depends(dependencies.verify_api_key)])
app.include_router(drivers.router)
app.include_router(users.router)
app.include_router(bookings.router)
app.include_router(vehicles.router)
app.include_router(tenant_settings.router)
app.include_router(admins.router, dependencies=[Depends(dependencies.verify_api_key)])
app.include_router(subscriptions.router)
app.include_router(logs.router)
app.include_router(slug.router)
app.include_router(webhooks.router)




    
