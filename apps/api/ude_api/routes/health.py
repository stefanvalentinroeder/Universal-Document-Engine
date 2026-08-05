from __future__ import annotations

import asyncio
from typing import cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ude_backend_core import StorageHealthPort
from ude_backend_db.health import ReadinessProbe

router = APIRouter(tags=["operations"])


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "ude-api"}


@router.get("/ready", summary="Readiness check")
async def ready(request: Request) -> JSONResponse:
    database_probe = cast(ReadinessProbe, request.app.state.readiness_probe)
    object_storage_probe = cast(StorageHealthPort, request.app.state.storage_health)
    database, object_storage_ready = await asyncio.gather(
        database_probe.check(),
        object_storage_probe.is_ready(),
    )
    is_ready = database.ready and object_storage_ready
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "database": {"status": "up" if database.ready else "down"},
            "object_storage": {"status": "up" if object_storage_ready else "down"},
        },
    }
    return JSONResponse(status_code=200 if is_ready else 503, content=payload)
