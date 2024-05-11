from random import uniform
from uuid import UUID, uuid4
import socket
import threading
import packet as pck

 
def threaded(server_socket: socket.socket, address: tuple) -> None:
    print(f"Player connected")
    player_id: UUID = uuid4()
    server_socket.sendto(pck.PlayerIdPacket(player_id).pack(), address)

    x = uniform(0, 800)
    y = uniform(0, 600)
    server_socket.sendto(pck.PlayerPositionPacket(x, y).pack(), address)

    while True:
        try:
            data, _ = server_socket.recvfrom(1024)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            break

        packet: pck.Packet = pck.unpack(data)
        
        if isinstance(packet, pck.PlayerInputPacket):
            print(f"Player {packet.player_id} input: {packet.x}, {packet.y}")
            x += packet.x
            y += packet.y
            server_socket.sendto(pck.PlayerPositionPacket(x, y).pack(), address)

 
def main() -> None:
    host = ""
    port: int = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(0.5)
    server_socket.bind((host, port))
    print("socket binded to port", port)
 
    # dispatch new threads for incoming UDP packets
    while True:
        try:
            # receive data from client
            data, address = server_socket.recvfrom(1024)

            packet: pck.Packet = pck.unpack(data)
            if isinstance(packet, pck.ConnectionRequestPacket):
                print('Connection from: ', address[0], ':', address[1])
    
                # Start a new thread to handle the request
                threading.Thread(target=threaded, args=(server_socket, address), daemon=True).start()
    
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            server_socket.close() 
            break

if __name__ == '__main__':
    main()