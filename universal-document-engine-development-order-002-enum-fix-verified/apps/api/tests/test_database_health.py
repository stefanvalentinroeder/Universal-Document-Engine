from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncEngine

from ude_backend_db import DatabaseReadinessProbe


async def test_probe_converts_connection_refusal_to_not_ready() -> None:
    engine = MagicMock(spec=AsyncEngine)
    engine.connect.side_effect = ConnectionRefusedError

    result = await DatabaseReadinessProbe(engine).check()

    assert result.ready is False
    assert result.detail == "unavailable"
