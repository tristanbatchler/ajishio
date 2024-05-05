# Ajishio

![Ajishio Taro](.github/assets/ajishio_taro.png)

Ajishio is a stripped-down [pygame](https://www.pygame.org)-based game engine for creating 2D games. 
Its API is modelled after old [GameMaker](https://gamemaker.io) versions, think pre-Studio 1.4. The 
reason for this is that I wanted to create something that feels the same way as when I first started 
making games in GameMaker 7, but with the optional features of a modern language and the choice of 
using whatever text editor I want.

The name "Ajishio" is a reference to 
[Noboru Yamaguchi](https://cromartiehigh.fandom.com/wiki/Noboru_Yamaguchi), the most misunderstood 
comedian in Japan. No reason this would ever be relevant to the game engine, but I thought it was a 
cool name.

## Quick Start

Getting a blank window up and running is as simple as:
```python
import ajishio as aj

aj.room_set_caption("Hello, World!")
aj.game_start()
```

To see more substantial examples, check out the `demo_projects` directory.

## TODO

- [ ] Support to load rooms from files
- [ ] Room editor
- [ ] Support for multiple rooms in a single game
- [ ] Support to load and draw sprites from files
- [ ] Sprite editor to define collision masks and load into the game
- [ ] Sprite editor to define animations and load into the game