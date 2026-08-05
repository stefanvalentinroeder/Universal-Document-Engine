from __future__ import annotations

from typing import Protocol

import httpx


class StorageHealthPort(Protocol):
    """Provider-neutral operational check for an object-storage implementation."""

    async def is_ready(self) -> bool:
        """Return whether the configured storage implementation is reachable."""


class MinioHealthAdapter:
    """Minimal local-development adapter; it does not expose object operations."""

    def __init__(self, endpoint: str, timeout_seconds: float = 2.0) -> None:
        self._health_url = f"{endpoint.rstrip('/')}/minio/health/ready"
        self._timeout = timeout_seconds

    async def is_ready(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                trust_env=False,
            ) as client:
                response = await client.get(self._health_url)
        except httpx.HTTPError:
            return False
        return response.status_code == httpx.codes.OK
