from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from app.api.routers import tenants, auth, drivers, bookings, users, vehicles, tenant_settings, admin,subscriptions, logs
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
        
        A comprehensive multi-tenant ride-sharing platform with support for:
        - **Tenant Management**: Company registration and settings
        - **Driver Operations**: Registration, ride management, earnings
        - **Rider Services**: Booking, ride history, payments
        - **Vehicle Management**: Fleet tracking, categorization, pricing
        
        ### Authentication
        Uses JWT Bearer tokens. Get token from `/api/v1/login/{role}` endpoints.
        
        ### Multi-Tenancy
        All operations are scoped to the authenticated user's tenant.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": "Login and token management for all user roles"
            },
            {
                "name": "Tenant", 
                "description": "Company management, driver onboarding, fleet oversight"
            },
            {
                "name": "Drivers",
                "description": "Driver registration, available rides, earnings"
            },
            {
                "name": "Bookings",
                "description": "Ride booking, status updates, history"
            },
            {
                "name": "Users",
                "description": "Rider registration and profile management"
            }
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
        "email": "dev@maison.com"
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        }
    ]
)

# CORS for frontend (dev: Vite at 5173; docker: nginx serves same-origin and proxies /api)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(users.router)
app.include_router(bookings.router)
app.include_router(vehicles.router)
app.include_router(tenant_settings.router)
app.include_router(admin.router)
app.include_router(subscriptions.router)
app.include_router(logs.router)




    