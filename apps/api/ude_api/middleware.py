from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import Message, Receive, Scope, Send

from ude_api.errors import internal_error_response
from ude_backend_core.logging import request_id_context

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_REQUEST_ID_HEADER = "X-Request-ID"

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class CorrelationIdMiddleware:
    """Bind a safe request identifier to logs and response headers."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        supplied_id = Headers(scope=scope).get(_REQUEST_ID_HEADER)
        request_id = (
            supplied_id
            if supplied_id is not None and _REQUEST_ID_PATTERN.fullmatch(supplied_id)
            else uuid4().hex
        )
        token = request_id_context.set(request_id)
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                MutableHeaders(scope=message)[_REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        except Exception as exception:
            if response_started:
                raise
            response = internal_error_response(exception)
            await response(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(token)
