
import hashlib
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import Settings
from app.redis_connect import redis_client
from fastapi import HTTPException, status
from app.utils.logging import logger

settings = Settings()

limiter = Limiter(
    key_func= get_remote_address, #rate limit by ip address
    storage_uri = settings.redis_url if settings.redis_url else None,
    default_limits = ["1000/day", "100/hour"]
)

"""Helper Fynctions"""
def get_user_rate_limit_key(email: str, ip: str) -> str:
    """create unique key for user and ip combined"""
    combined = f"{email}:{ip}"
    return hashlib.md5(combined.encode()).hexdigest()

def check_user_specific_rate_limit(email:str, ip:str, max_attempts: int = 3, window_minutes: int = 5):
    """Check and updates user-specific rate limiting"""
    user_key = get_user_rate_limit_key(email, ip)
    attempts_key = f"login_attempts:{user_key}"
    logger.info(f" {attempts_key}")

    current_attempts = redis_client.incr(attempts_key)
    logger.info(f"current_attempts = {current_attempts}")

    #set expiry time 
    if current_attempts == 1:
        redis_client.expire(attempts_key, window_minutes * 60)

    if current_attempts and int(current_attempts) >= max_attempts:
        ttl = redis_client.ttl(attempts_key)
        logger.info(f"To many failed login attempts. Try again in {ttl} seconds.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail = f"To many failed login attempts. Try again in {ttl} seconds."
        )
    return attempts_key

def record_failed_attempt(attempts_key: str, window_minutes: int = 5):
    """record a failed login attempt"""
    pipe = redis_client.pipeline()
    pipe.incr(attempts_key)
    pipe.expire(attempts_key, window_minutes * 60)
    pipe.execute()                

def clear_failed_attempts(attempts_key: str):
    """clear failed attempts on successful login"""
    logger.info("attempts_key has been deleted")
    redis_client.delete(attempts_key)
