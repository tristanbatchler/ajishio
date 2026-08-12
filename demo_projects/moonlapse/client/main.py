import asyncio
import logging
import ajishio as aj

from demo_projects.moonlapse.client.manager import Manager

log = logging.getLogger("moonlapse.client")

HOST = "127.0.0.1"
PORT = 8766


async def main() -> None:
    client = aj.GameNetClient(f"ws://{HOST}:{PORT}")
    await client.connect()
    mgr = Manager(client=client)
    aj.register_objects(Manager)
    aj.add_object(mgr)

    aj.room_set_caption("Moonlapse Client")
    await aj.game_start_async()


if __name__ == "__main__":
    asyncio.run(main())
