from demo_projects.moonlapse.shared.packets import serverbound as serverbound
from demo_projects.moonlapse.shared.packets import clientbound as clientbound
from demo_projects.moonlapse.shared.packets.proto import PacketProto


def deserialize(data: bytes) -> PacketProto:
    header: bytes = data[:2]
    packet_type: int = int.from_bytes(header)
    payload_bytes = data[2:]
    for registry in (serverbound.REGISTRY, clientbound.REGISTRY):
        if packet_type in registry:
            return registry[packet_type].from_bytes(payload_bytes)
    raise ValueError(f"Unknown packet type: {packet_type}")
