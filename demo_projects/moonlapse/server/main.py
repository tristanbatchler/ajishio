import demo_projects.moonlapse.shared.packets.serverbound as serverbound
import demo_projects.moonlapse.shared.packets.clientbound as clientbound
from demo_projects.moonlapse.shared.packets import deserialize_from_client, deserialize_from_server


# serialise serverbound
chat = serverbound.ChatRequest(message="Hello, world!")
raw = chat.serialize()
print(f"serialised: {raw.hex()}")

# deserialise from client
pkt = deserialize_from_client(raw)
assert isinstance(pkt, serverbound.ChatRequest)
print(f"deserialised: {type(pkt).__name__}, message={pkt.message}")

# round-trip
resp = clientbound.ChatResponse(ok=True, err=None)
raw2 = resp.serialize()
pkt2 = deserialize_from_server(raw2)
assert isinstance(pkt2, clientbound.ChatResponse)
print(f"round-trip: {type(pkt2).__name__}, ok={pkt2.ok}, err={pkt2.err}")
