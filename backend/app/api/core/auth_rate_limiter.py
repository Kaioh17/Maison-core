"""Failure-count lockouts kept in Redis (used for login and the driver onboarding code).

Only *failures* count, so a legitimate user is never locked out by their own successful logins.
`scope` + `ident` build the key, e.g. ("login", "<md5 of email:ip>") or ("driver_verify", "<ip>:<slug>").
"""
import hashlib

from fastapi import HTTPException, status

from app.redis_connect import redis_client
from app.utils.logging import logger


def hashed(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:32]


def _key(scope: str, ident: str) -> str:
    return f"failed:{scope}:{ident}"


def assert_not_locked(scope: str, ident: str, max_failures: int) -> None:
    """429 if `ident` already has `max_failures` recent failures. Does not count the current attempt."""
    key = _key(scope, ident)
    failures = int(redis_client.get(key) or 0)
    if failures >= max_failures:
        ttl = max(redis_client.ttl(key), 1)
        logger.info(f"[{scope}] locked out, {ttl}s left")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {ttl} seconds.",
            headers={"Retry-After": str(ttl)},
        )


def record_failure(scope: str, ident: str, window_minutes: int) -> None:
    key = _key(scope, ident)
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_minutes * 60)  # window slides with each failure
    pipe.execute()


def clear_failures(scope: str, ident: str) -> None:
    redis_client.delete(_key(scope, ident))
