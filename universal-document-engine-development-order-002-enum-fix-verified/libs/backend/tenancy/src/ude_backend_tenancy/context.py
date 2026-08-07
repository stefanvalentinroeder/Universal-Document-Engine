from __future__ import annotations

from dataclasses import dataclass
from typing import NewType, Protocol

TenantId = NewType("TenantId", str)


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Required request context for future tenant-owned operations."""

    tenant_id: TenantId
    correlation_id: str


class TenantContextProvider(Protocol):
    """Resolve tenant context without coupling domain code to authentication."""

    def require(self) -> TenantContext:
        """Return context or reject requests that have no verified tenant."""
