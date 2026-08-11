from demo_projects.moonlapse.shared.packets import serverbound as serverbound
from demo_projects.moonlapse.shared.packets import clientbound as clientbound


def deserialize_from_server(data: bytes) -> clientbound.ClientboundPacket:
    packet_type = clientbound.ClientboundPacketType(int.from_bytes(data[:2]))
    payload = data[2:]

    packet_class = clientbound.get_packet_class(packet_type)
    return packet_class.from_bytes(payload)


def deserialize_from_client(data: bytes) -> serverbound.ServerboundPacket:
    packet_type = serverbound.ServerboundPacketType(int.from_bytes(data[:2]))
    payload = data[2:]

    packet_class = serverbound.get_packet_class(packet_type)
    return packet_class.from_bytes(payload)
