from fastapi import HTTPException, status
from app.models import user, driver, tenant, full_name
from app.utils import password_utils
from app.utils.logging import logger
from .helper_service import _tenants_exist

user_table = user.Users
async def create_user(db, payload):

    exists = db.query(user_table).filter(user_table.email == payload.email, user_table.tenant_id == payload.tenant_id).first()  
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"User with {payload.email} already exists")
    
    _tenants_exist(db, payload)

    hashed_pwd = password_utils.hash(payload.password) #hash password

    #if user exists
   
    user_info = payload.model_dump()
    user_info.pop("tenants", None)
    new_user = user.Users(**user_info)
    new_user.password = hashed_pwd

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User {full_name} has been added")

    return new_user

async def get_user_info(db, current_user):

    logger.info(f"Getting user info for {current_user.email}")
    user_info = db.query(user.Users).filter(user.Users.email == current_user.email).first()

    return user_info