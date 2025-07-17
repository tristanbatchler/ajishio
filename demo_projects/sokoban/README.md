# Sokoban

This demo showcases how little or how much you want to do let Ajishio handle. For example, this demo 
does not use any of the built-in collision detection because of the simplicity of the game. Instead, 
it uses a series of dictionaries to store the positions of boxes, walls, and targets. This allows 
for improved performance over the built-in collision detection, but it does require more manual 
management of the game state.

It also shows that one does not need to use the built-in room system with LDtk. Instead, a manual 
system is used to load the level data from a text file.