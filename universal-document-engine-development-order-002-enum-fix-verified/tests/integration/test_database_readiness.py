from __future__ import annotations

import os

import pytest

from ude_backend_core import MinioHealthAdapter
from ude_backend_db import Database, DatabaseReadinessProbe


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Set RUN_INFRA_TESTS=1 after starting local infrastructure",
)
async def test_database_readiness_against_local_postgres() -> None:
    database_url = os.environ["DATABASE_URL"]
    database = Database(database_url)
    try:
        result = await DatabaseReadinessProbe(database.engine).check()
    finally:
        await database.close()

    assert result.ready is True


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_INFRA_TESTS") != "1",
    reason="Set RUN_INFRA_TESTS=1 after starting isolated infrastructure",
)
async def test_object_storage_readiness_against_local_minio() -> None:
    storage = MinioHealthAdapter(os.environ["MINIO_ENDPOINT"])

    assert await storage.is_ready() is True
