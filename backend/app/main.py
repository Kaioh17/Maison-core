from fastapi import FastAPI
from app.api.routers import tenants, auth, drivers, bookings, users, vehicles
from app.db.database import engine
from app.models import *
# from utils import logging

##add frontend urls and middleware 
#user cors


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Maison"
)

app.include_router(tenants.router)
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(users.router)
app.include_router(bookings.router)
app.include_router(vehicles.router)






    