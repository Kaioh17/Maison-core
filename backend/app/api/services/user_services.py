from fastapi import HTTPException, status
from app.models import user, driver, tenant
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from .helper_service import _tenants_exist,_tenant_activity_

db_exceptions = db_error_handler.DBErrorHandler
user_table = user.Users
tenant_table = tenant.Tenants



async def create_user(db, payload):
    try:
        exists = db.query(user_table).filter(user_table.email == payload.email, 
                                             user_table.tenant_id == payload.tenant_id, 
                                             user_table.phone_no == payload.phone_no
                                             ).first()  
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail= f"User with {payload.email} already exists")    
        
        
        _tenants_exist(db, payload)
        _tenant_activity_(db, payload)

        hashed_pwd = password_utils.hash(payload.password) #hash password

        #if user exists
    
        user_info = payload.model_dump()
        user_info.pop("tenants", None)
        new_user = user.Users(**user_info)
        new_user.password = hashed_pwd

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

    logger.info(f"User {full_name} has been added")

    return new_user

async def get_user_info(db, current_user):
    try:
        logger.info(f"Getting user info for {current_user.email}")
        user_info = db.query(user.Users).filter(user.Users.email == current_user.email).first()
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
    return user_info