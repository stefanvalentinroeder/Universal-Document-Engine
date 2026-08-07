from __future__ import annotations

import logging
from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHttpException

from ude_backend_core.logging import request_id_context

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


def _response(status_code: int, code: str, message: str) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id_context.get(),
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


async def http_exception_handler(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    http_exception = cast(StarletteHttpException, exception)
    safe_message = (
        http_exception.detail
        if isinstance(http_exception.detail, str)
        else "Request failed"
    )
    return _response(http_exception.status_code, "http_error", safe_message)


def internal_error_response(exception: Exception) -> JSONResponse:
    logger.exception("Unhandled request exception", exc_info=exception)
    return _response(500, "internal_error", "An internal error occurred")
