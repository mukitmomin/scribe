from typing import Optional
from fastapi import Request
from app.config import settings


def get_current_tenant(request: Request) -> Optional[str]:
    """
    Extract tenant ID from request context.

    In single-tenant mode (multi_tenant_enabled=False), returns None.
    In multi-tenant mode, extracts tenant from JWT claims or header.

    Future implementation will:
    1. Extract JWT from Authorization header
    2. Validate token with auth provider (Auth0/Clerk)
    3. Extract tenant_id from claims
    """
    if not settings.multi_tenant_enabled:
        return None

    # Multi-tenant mode: extract from header or JWT
    # For now, check X-Tenant-ID header as a stub
    tenant_id = request.headers.get("X-Tenant-ID")

    if tenant_id:
        return tenant_id

    # Fallback to default tenant
    return settings.default_tenant_id
