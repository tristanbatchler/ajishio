from __future__ import annotations

import asyncio
import logging
from websockets.asyncio.server import serve

from demo_projects.moonlapse.server.connection import Hub

log = logging.getLogger("moonlapse")

HOST = "0.0.0.0"
PORT = 8766


async def main() -> None:
    hub = Hub()
    async with serve(
        hub.register_client,
        HOST,
        PORT,
    ):
        log.info("moonlapse server on %s:%d", HOST, PORT)
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    asyncio.run(main())
