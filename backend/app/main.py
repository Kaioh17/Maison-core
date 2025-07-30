from fastapi import FastAPI
from app.api.routers import tenants, auth, drivers, bookings, users, vehicles, tenant_settings
from app.db.database import engine
from app.models import *
# from utils import logging

from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import Settings

settings = Settings()
##add frontend urls and middleware 
#user cors
limiter = Limiter(
    key_func= get_remote_address, #rate limit by ip address
    storage_uri = settings.redis_url if settings.redis_url else None,
    default_limits = ["1000/day", "100/hour"]
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Maison"
)


# attach limiter
limiter.init_app(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(tenants.router)
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(users.router)
app.include_router(bookings.router)
app.include_router(vehicles.router)
app.include_router(tenant_settings.router)





    