from sqlalchemy.exc import *
from app.utils.logging import logger
from fastapi import HTTPException, status

class DBErrorHandler:
    COMMON_DB_ERRORS = (
        IntegrityError,
        DataError,
        OperationalError,
        SQLAlchemyError,
    )

    @staticmethod
    def handle(exc, db):
        db.rollback()

        if isinstance(exc, IntegrityError):
            logger.error("Integrity constraint failed.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail = "Duplicate or constraint violation.")
        elif isinstance(exc, DataError):
            logger.error("Data formatting or overflow issue.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail = "Invalid data sent to the database.")
        elif isinstance(exc, OperationalError):
            logger.error("Database is unreachable or broken")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail = "Database temporarily unavailable")
        elif isinstance(exc, SQLAlchemyError):
            logger.error(f"Unexpected SQLAlchemy error: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail = "unexpected database error.")
        else:
            logger.error(f"Unknown error: {exc}")

            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Unknown error.")