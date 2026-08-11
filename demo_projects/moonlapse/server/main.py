import demo_projects.moonlapse.shared.packets.serverbound as serverbound
import demo_projects.moonlapse.shared.packets.clientbound as clientbound
from demo_projects.moonlapse.shared.packets import deserialize


# serialise serverbound
chat = serverbound.ChatRequest(message="Hello, world!")
raw = chat.serialize()
print(f"serialised: {raw.hex()}")

# deserialise
pkt = deserialize(raw)
assert isinstance(pkt, serverbound.ChatRequest)
print(f"deserialised: {type(pkt).__name__}, message={pkt.message}")

# round-trip clientbound
resp = clientbound.ChatResponse(ok=True, err=None)
raw2 = resp.serialize()
pkt2 = deserialize(raw2)
assert isinstance(pkt2, clientbound.ChatResponse)
print(f"round-trip: {type(pkt2).__name__}, ok={pkt2.ok}, err={pkt2.err}")
