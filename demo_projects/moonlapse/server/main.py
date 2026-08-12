from __future__ import annotations

import asyncio
import logging
from websockets.asyncio.server import serve
import aiosqlite
import sqlite3
import pathlib
from demo_projects.moonlapse.server.connection import Hub
from demo_projects.moonlapse.server.db import ops
from datetime import datetime, timezone

log = logging.getLogger("moonlapse")

HOST = "0.0.0.0"
PORT = 8766
DB_PATH: str = str(pathlib.Path(__file__).parent / "moonlapse.db")


async def _init_db() -> aiosqlite.Connection:
    """Create/open the database and run schema."""
    aiosqlite.register_adapter(
        datetime, lambda val: val.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )
    await ops.create_tables(DB_PATH)
    return await aiosqlite.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)


async def main() -> None:
    db_conn = await _init_db()
    hub = Hub(db_conn)
    async with serve(
        hub.register_client,
        HOST,
        PORT,
    ):
        log.info("moonlapse server on %s:%d", HOST, PORT)
        await hub.run()
    await hub.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    asyncio.run(main())
