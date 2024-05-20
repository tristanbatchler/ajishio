# Multiplayer

This is a simple server-client multiplayer game to demonstrate how Ajishio can be integrated with 
powerful Python features, such as the `socket` module, to provide a multiplayer experience with 
little effort.

In this example, a shared module is used to allow the server and clients to both use the same 
packet definitions and game objects. The server runs its own instance of the game to simulate the 
world and synchronize it with the clients. Each client also runs their own version of the game, and 
the server sends updates to the clients to keep them in sync.

The server and clients communicate using a lightweight packet system over one UDP socket.