from __future__ import annotations

import asyncio
import logging
from websockets.asyncio.server import ServerConnection, serve

from demo_projects.moonlapse.shared.packets import deserialize_from_client
import demo_projects.moonlapse.shared.packets.clientbound as clientbound
from demo_projects.moonlapse.server.connection import Hub
from demo_projects.moonlapse.server.client import Client
from demo_projects.moonlapse.server.state import State
from demo_projects.moonlapse.server import states

log = logging.getLogger("moonlapse")

HOST = "0.0.0.0"
PORT = 8766


async def _handle_client(hub: Hub, ws: ServerConnection) -> None:
    cid = hub.next_id
    client = Client(cid, ws)
    client.state = states.ConnectingState(client, hub)
    hub.register_client(client)
    await client.state.on_enter()

    try:
        async for raw in ws:
            data = raw if isinstance(raw, bytes) else raw.encode()
            pkt = deserialize_from_client(data)
            new_state = await client.state.handle_packet(pkt)

            if new_state is not None:
                await client.state.on_exit()
                client.state = new_state
                await client.state.on_enter()

    except Exception as exc:
        log.info(f"disconnected {cid} ({exc})")
    finally:
        _ = hub.unregister_client(cid)
        await hub.broadcast(clientbound.Announcement(f"Player {cid} left the game."))
        log.info(
            f"disconnected {cid} ({ws.remote_address}), total={len(hub.get_clients())}"  # pyright: ignore[reportAny]
        )


async def main() -> None:
    hub = Hub()
    async with serve(
        lambda ws: _handle_client(hub, ws),
        HOST,
        PORT,
    ):
        log.info("moonlapse server on %s:%d", HOST, PORT)
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    asyncio.run(main())
