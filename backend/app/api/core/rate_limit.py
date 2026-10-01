"""Rate limiting.

* `DefaultRateLimitMiddleware` applies one per-client, per-path limit to every request (Redis backed).
  It replaces slowapi's SlowAPIMiddleware, which silently stops matching routes on Starlette >= 1.0
  (its route lookup returns None, so nothing was limited).
* `limiter` is still slowapi's, used only for the explicit `@limiter.limit("n/minute")` decorators on
  individual routes, which do not depend on that lookup.

The client IP is scope["client"], i.e. the real caller only when the app sits behind a trusted proxy
configured via `trusted_proxies` (see main.py); otherwise every user would share the proxy's IP.
"""
import json
import time

from fastapi import Request
from limits import parse
from limits.storage import storage_from_string
from limits.strategies import FixedWindowRateLimiter
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import Settings
from app.utils.logging import logger

settings = Settings()

DEFAULT_LIMIT = "120/minute"
# Stripe signs these and retries on 429, so IP rate limiting only hurts here.
EXEMPT_PREFIXES = ("/api/v1/webhooks",)


def ip_and_path(request: Request) -> str:
    return f"{get_remote_address(request)}:{request.url.path}"


limiter = Limiter(key_func=ip_and_path, storage_uri=settings.redis_url or None)


class DefaultRateLimitMiddleware:
    def __init__(self, app, limit: str = DEFAULT_LIMIT):
        self.app = app
        self.item = parse(limit)
        self.strategy = FixedWindowRateLimiter(storage_from_string(settings.redis_url or "memory://"))

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] == "OPTIONS" or scope["path"].startswith(EXEMPT_PREFIXES):
            return await self.app(scope, receive, send)

        client = (scope.get("client") or ("unknown", 0))[0]
        ident = ("default", client, scope["path"])
        retry_after = 0
        try:
            allowed = self.strategy.hit(self.item, *ident)
            if not allowed:
                retry_after = max(int(self.strategy.get_window_stats(self.item, *ident).reset_time - time.time()), 1)
        except Exception as e:  # a Redis outage must not take the whole API down
            logger.warning(f"Rate limiter unavailable, letting request through: {e}")
            allowed = True
        if allowed:  # outside the try: errors from the app itself must not be mistaken for limiter errors
            return await self.app(scope, receive, send)

        body = json.dumps({"error": f"Rate limit exceeded: {self.item}"}).encode()
        await send({"type": "http.response.start", "status": 429, "headers": [
            (b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()),
            (b"retry-after", str(retry_after).encode())]})
        await send({"type": "http.response.body", "body": body})
