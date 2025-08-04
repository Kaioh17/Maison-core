from fastapi import FastAPI, Request
from app.api.routers import tenants, auth, drivers, bookings, users, vehicles, tenant_settings, admin
from app.db.database import engine
from app.models import *
# from utils import logging

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

app = FastAPI(
    title = "Maison"
)


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




    