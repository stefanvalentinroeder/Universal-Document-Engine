from __future__ import annotations

import pytest

from ude_backend_core import MinioHealthAdapter


async def test_storage_probe_ignores_host_proxy_and_reports_connection_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALL_PROXY", "socks5://127.0.0.1:65534")
    storage = MinioHealthAdapter("http://127.0.0.1:65533", timeout_seconds=0.1)

    assert await storage.is_ready() is False
