from fastapi import HTTPException, status
from models import tenant
from utils import password_utils

def create_tenant(db, payload):

    """Create new tenants"""
    hashed_pwd = password_utils.hash(payload.password) #hash password

    tenats_info = payload.model_dump()
    tenats_info.pop("users", None)
    new_tenant = tenant.Tenants(**tenats_info)
    new_tenant.password = hashed_pwd

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return new_tenant