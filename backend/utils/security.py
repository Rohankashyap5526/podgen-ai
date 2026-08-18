"""
PodGen AI – Security & Rate Limiting Middleware
"""

import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ─── In-memory rate limiter ───────────────────────────────────────────────────

class RateLimiter:
    """Sliding-window rate limiter (per IP)."""

    def __init__(self, requests_per_minute: int = 20):
        self.limit = requests_per_minute
        self._windows: dict = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window = self._windows[client_ip]

        # Remove timestamps older than 60s
        self._windows[client_ip] = [t for t in window if now - t < 60]

        if len(self._windows[client_ip]) >= self.limit:
            return False

        self._windows[client_ip].append(now)
        return True


_limiter = RateLimiter(requests_per_minute=30)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Adds rate limiting and basic security headers."""

    async def dispatch(self, request: Request, call_next):
        # Skip health check
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        # Rate limiting on /api routes
        if request.url.path.startswith("/api"):
            client_ip = request.client.host if request.client else "unknown"
            if not _limiter.is_allowed(client_ip):
                logger.warning("Rate limit exceeded for %s", client_ip)
                return JSONResponse(
                    {"detail": "Rate limit exceeded. Try again in a minute."},
                    status_code=429
                )

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
