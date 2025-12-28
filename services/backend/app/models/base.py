from sqlalchemy import Column, String


class TenantMixin:
    """
    Mixin for multi-tenancy support.

    Adds a tenant_id column that is:
    - Nullable in single-tenant mode
    - Indexed for efficient filtering
    - Ready to become NOT NULL when multi-tenancy is enabled
    """
    tenant_id = Column(String, nullable=True, index=True)
