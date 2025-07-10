from fastapi import FastAPI
from api.routers import tenants, auth
from db.database import engine,Base
from models import *

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Maison"
)

app.include_router(tenants.router)
app.include_router(auth.router)
    