# Ajishio

A fun, GameMaker-inspired 2D game engine built on pygame-ce for making unserious games quickly.

```python
import ajishio as aj

class Player(aj.GameObject):
    def step(self):
        if aj.keyboard_check(aj.vk_right):
            self.x += 4 * aj.delta_time

aj.register_objects(Player)
aj.set_rooms(levels)
aj.game_start()
```

See the [API Reference](./api.md) for full details.
