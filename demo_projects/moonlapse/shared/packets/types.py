from __future__ import annotations

import struct

from demo_projects.moonlapse.shared.packets.clientbound import REGISTRY as CB_REGISTRY
from demo_projects.moonlapse.shared.packets.serverbound import REGISTRY as SB_REGISTRY
from demo_projects.moonlapse.shared.packets.proto import PacketProto


def serialize(proto: PacketProto) -> bytes:
    ptype = proto.get_type()
    fmt = proto.get_fmt()
    structure = proto.get_structure()
    header_bytes = struct.pack(">H", ptype)
    payload_bytes = struct.pack(fmt, *structure)
    return header_bytes + payload_bytes


def deserialize(data: bytes) -> PacketProto:
    header: bytes = data[:2]
    packet_type: int = int.from_bytes(header, "big")
    payload_bytes = data[2:]
    for registry in (SB_REGISTRY, CB_REGISTRY):
        if packet_type in registry:
            return registry[packet_type].from_bytes(payload_bytes)
    raise ValueError(f"Unknown packet type: {packet_type}")
