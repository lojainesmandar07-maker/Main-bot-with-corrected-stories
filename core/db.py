from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable, TypeVar

import aiosqlite

DB_PATH = "data/nexus.db"

T = TypeVar("T")


@asynccontextmanager
async def get_connection() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(DB_PATH)
    try:
        yield db
    finally:
        await db.close()


async def table_exists(db: aiosqlite.Connection, table_name: str) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return (await cursor.fetchone()) is not None


async def run_read(operation: Callable[[aiosqlite.Connection], Awaitable[T]]) -> T:
    async with get_connection() as db:
        return await operation(db)


async def run_write(operation: Callable[[aiosqlite.Connection], Awaitable[T]]) -> T:
    async with get_connection() as db:
        try:
            result = await operation(db)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise
