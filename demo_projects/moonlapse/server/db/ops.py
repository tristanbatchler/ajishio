"""Database initialization helpers."""
from __future__ import annotations

import logging
import pathlib

import aiosqlite

log = logging.getLogger("moonlapse.db")

_DIR = pathlib.Path(__file__).parent


async def create_tables(db_path: str) -> None:
    """Apply schema.sql against `db_path`.

    schema.sql uses CREATE TABLE IF NOT EXISTS so restarts are idempotent.
    """
    schema_sql = (_DIR / "schema.sql").read_text()
    async with aiosqlite.connect(db_path) as conn:
        _ = await conn.executescript(schema_sql)
        await conn.commit()
    log.info("db tables ready: %s", db_path)
