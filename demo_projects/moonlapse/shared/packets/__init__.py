from demo_projects.moonlapse.shared.packets import serverbound as serverbound
from demo_projects.moonlapse.shared.packets import clientbound as clientbound
from demo_projects.moonlapse.shared.packets.base import Packet


def _get_packet_class(
    packet_type: clientbound.ClientboundPacketType | serverbound.ServerboundPacketType,
) -> type[Packet]:
    if isinstance(packet_type, clientbound.ClientboundPacketType):
        try:
            return clientbound.REGISTRY[packet_type]
        except KeyError:
            raise NotImplementedError(
                f"Packet type {packet_type} not registered to clientbound packets"
            )
    else:
        try:
            return serverbound.REGISTRY[packet_type]
        except KeyError:
            raise NotImplementedError(
                f"Packet type {packet_type} not registered to serverbound packets"
            )


def deserialize_from_server(data: bytes) -> clientbound.ClientboundPacket:
    packet_type = clientbound.ClientboundPacketType(int.from_bytes(data[:2]))
    payload = data[2:]

    packet_class = _get_packet_class(packet_type)
    assert issubclass(packet_class, clientbound.ClientboundPacket)
    return packet_class.from_bytes(payload)


def deserialize_from_client(data: bytes) -> serverbound.ServerboundPacket:
    packet_type = serverbound.ServerboundPacketType(int.from_bytes(data[:2]))
    payload = data[2:]

    packet_class = _get_packet_class(packet_type)
    assert issubclass(packet_class, serverbound.ServerboundPacket)
    return packet_class.from_bytes(payload)
