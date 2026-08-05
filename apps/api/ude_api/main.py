from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHttpException

from ude_api.api.v1.router import router as v1_router
from ude_api.config import Settings, get_settings
from ude_api.errors import http_exception_handler
from ude_api.middleware import CorrelationIdMiddleware
from ude_api.routes.health import router as health_router
from ude_backend_core import MinioHealthAdapter, configure_structured_logging
from ude_backend_db import Database, DatabaseReadinessProbe

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_structured_logging(resolved_settings.log_level)
    database = Database(resolved_settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        logger.info("API service starting")
        try:
            yield
        finally:
            await database.close()
            logger.info("API service stopped")

    app = FastAPI(
        title="Universal Document Engine API",
        summary="Industry-neutral platform API foundation.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.database = database
    app.state.readiness_probe = DatabaseReadinessProbe(database.engine)
    app.state.storage_health = MinioHealthAdapter(resolved_settings.minio_endpoint)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    app.add_exception_handler(StarletteHttpException, http_exception_handler)
    app.include_router(health_router)
    app.include_router(v1_router)
    return app
