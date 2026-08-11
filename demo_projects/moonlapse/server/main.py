import demo_projects.moonlapse.shared.packets.serverbound as serverbound
import demo_projects.moonlapse.shared.packets.clientbound as clientbound
from demo_projects.moonlapse.shared.packets import (
    deserialize_from_client,
    deserialize_from_server,
)


chat_request = serverbound.ChatRequest("Hello?")
bytes = chat_request.serialize()

incoming = deserialize_from_client(bytes)
response: clientbound.ClientboundPacket | None = None
if isinstance(incoming, serverbound.ChatRequest):
    print("Got a chat request!")
    print(incoming.message)
    response = clientbound.ChatResponse(ok=True)
elif isinstance(incoming, serverbound.MoveRequest):
    print("Got a move request!")
    print(f"({incoming.dx}, {incoming.dy})")
    response = clientbound.MoveResponse(
        ok=False, err="Hmmmm I don't like the look of that movement"
    )
else:
    print("Got something else!")

if response is not None:
    bytes = response.serialize()

    incoming = deserialize_from_server(bytes)

    if isinstance(incoming, clientbound.ChatResponse):
        print("Got a chat response!")
        if not incoming.ok:
            print(f"It's bad news: {incoming.err}")
        else:
            print("It's all good!")
    elif isinstance(incoming, clientbound.MoveResponse):
        print("Got a move response!")
        if not incoming.ok:
            print(f"It's not good at all... {incoming.err}")
        else:
            print("Guess they like my moves")
