"""Explicit tenant-context interfaces; no tenant domain model is implemented."""

from ude_backend_tenancy.context import TenantContext, TenantContextProvider, TenantId

__all__ = ["TenantContext", "TenantContextProvider", "TenantId"]
