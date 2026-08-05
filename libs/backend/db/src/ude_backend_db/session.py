from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Own the async engine and expose a narrow transaction-ready session boundary."""

    def __init__(self, url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            yield session

    async def close(self) -> None:
        await self.engine.dispose()
