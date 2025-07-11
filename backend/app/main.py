from fastapi import FastAPI
from api.routers import tenants, auth, drivers, bookings
from db.database import engine,Base
from models import *
from utils import logging


logger = logging


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Maison"
)

app.include_router(tenants.router)
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(bookings.router)

    