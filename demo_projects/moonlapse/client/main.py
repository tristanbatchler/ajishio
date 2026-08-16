import asyncio
import logging
import ajishio as aj

from demo_projects.moonlapse.client.manager import Manager
from demo_projects.moonlapse.shared.constants import TICKS_PER_SECOND

log = logging.getLogger("moonlapse.client")

HOST = "127.0.0.1"
PORT = 8766


async def main() -> None:
    # Large window, small viewport → everything gets pixel-scaled up.
    aj.window_set_size(1280, 720)
    aj.view_set_wport(0, 96)   # viewport covers 96 units of world space
    aj.view_set_hport(0, 96)

    client = aj.GameNetClient(f"ws://{HOST}:{PORT}")
    await client.connect()
    _ = Manager(client=client)

    aj.room_set_caption("Moonlapse Client")
    aj.game_set_speed(TICKS_PER_SECOND)
    await aj.game_start_async()


if __name__ == "__main__":
    asyncio.run(main())
