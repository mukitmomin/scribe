import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class LicenseMiddleware(BaseHTTPMiddleware):
    """
    Placeholder middleware for license validation.

    In production, this will:
    1. Validate LICENSE_KEY against a licensing service
    2. Check license expiration and feature flags
    3. Rate limit based on license tier

    Skip validation in development when LICENSE_KEY is empty.
    """

    async def dispatch(self, request: Request, call_next):
        license_key = os.getenv("LICENSE_KEY", "")

        # Skip validation in development
        if not license_key:
            return await call_next(request)

        # TODO: Implement actual license validation
        # For now, just accept any non-empty license key
        if license_key:
            return await call_next(request)

        raise HTTPException(
            status_code=403,
            detail="Invalid or missing license key"
        )
