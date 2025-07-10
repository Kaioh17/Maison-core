from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db.database import get_db

router = APIRouter(
    prefix = "/admin",
    tags = ['admin']
)   

