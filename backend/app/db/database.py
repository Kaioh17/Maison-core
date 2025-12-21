from typing import Optional
from fastapi.params import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import Settings
from app.models.base import Base
from app.api.core import security

settings = Settings()

DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine  = create_engine(DATABASE_URL,
                         echo=False, 
                         pool_size = 10, 
                         max_overflow = 20,
                         pool_timeout= 30,
                         pool_recycle=1800)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def recieve_checkouot():
#     logger.debug(f"Connection checked out ")
def get_db(tenant_id: int | None = Depends(security.get_tenant_id_from_token)):
    ## for authorized users
    # tenant_id = security.get_tenant_id()
    db = SessionLocal()
    try:
        if tenant_id is not None:
            
            db.execute(
                text("SET app.current_tenant_id = :tenant_id").bindparams(tenant_id=tenant_id)
            )
        yield db
    finally:
        db.close()  


##for login process 
def get_base_db():
    try:
        db = SessionLocal()

        yield db
    finally:
        db.close()