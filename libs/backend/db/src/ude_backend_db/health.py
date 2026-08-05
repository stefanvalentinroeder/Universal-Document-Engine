from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    ready: bool
    detail: str


class ReadinessProbe(Protocol):
    async def check(self) -> ReadinessResult:
        """Evaluate whether a required dependency can accept work."""


class DatabaseReadinessProbe:
    """Prove PostgreSQL connectivity without revealing connection details."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def check(self) -> ReadinessResult:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except (OSError, SQLAlchemyError):
            return ReadinessResult(ready=False, detail="unavailable")
        return ReadinessResult(ready=True, detail="available")
