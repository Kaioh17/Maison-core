from fastapi import HTTPException, status
from models import user, driver, tenant, full_name
from utils import password_utils
from utils.logging import logger


async def create_user(db, payload):

    hashed_pwd = password_utils.hash(payload.password) #hash password

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