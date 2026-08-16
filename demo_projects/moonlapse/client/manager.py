from __future__ import annotations

import logging
from typing import Unpack, override
import ajishio as aj


from demo_projects.moonlapse.shared.packets import deserialize_from_server
from demo_projects.moonlapse.client.protocol import State
from demo_projects.moonlapse.client import states

log = logging.getLogger("moonlapse.manager")


class Manager(aj.GameObject):
    def __init__(
        self,
        client: aj.GameNetClient,
        x: float = 0,
        y: float = 0,
        **kwargs: Unpack[aj.GameObjectKwargs],
    ) -> None:
        super().__init__(x, y, **kwargs)
        self.client: aj.GameNetClient = client
        self.state: State = states.ConnectingState(self)
        self.client_id: int | None = None

    def set_client_id(self, id: int):
        self.client_id = id

    def get_client_id(self):
        return self.client_id

    def _process_network(self) -> None:
        incoming = self.client.recv()
        while incoming is not None:
            p = deserialize_from_server(incoming)
            new_state = self.state.handle_packet(p)
            if new_state is not None:
                self.state.on_exit()
                aj.instance_destroy(self.state)
                self.state = new_state
                self.state.on_enter()
            incoming = self.client.recv()

    @override
    def step(self) -> None:
        super().step()
        self._process_network()
