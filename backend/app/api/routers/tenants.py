from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from sqlalchemy.orm import Session

router = APIRouter(
    prefix = "/tenant",
    tags = ['tenant']
)   


@router.get('/', status_code= status.HTTP_200_OK)
def tenants():
    return {"msg": "tenants are active"}